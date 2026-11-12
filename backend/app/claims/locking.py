import asyncio
import uuid
import logging
from dataclasses import dataclass
from datetime import datetime, timezone, timedelta
from typing import Optional
from contextlib import asynccontextmanager
from sqlalchemy import select, update, delete
from sqlalchemy.exc import IntegrityError, OperationalError
from app.models.claim import SubmissionProcessingLock

logger = logging.getLogger("truthnet.claims.locking")

def _ensure_utc(dt: Optional[datetime]) -> Optional[datetime]:
    if dt is None:
        return None
    if dt.tzinfo is None:
        return dt.replace(tzinfo=timezone.utc)
    return dt

class StaleLockException(Exception):
    """Raised when an extraction worker attempts to commit after its lease expired or was superseded."""
    pass

@dataclass
class LockLease:
    submission_id: str
    owner_token: str
    fencing_token: int
    expires_at: datetime
    is_active: bool = True

class SubmissionLockManager:
    """
    Physical database-backed per-submission lock lease manager.
    Coordinates claim extraction across multiple processes, uvicorn workers,
    and concurrent async tasks without relying on in-memory locks or SQLite WAL alone.
    
    Provides:
    - Unambiguous lease ownership via unique owner tokens and monotonic fencing tokens.
    - Active background heartbeat renewal to guarantee long-running live workers never lose their lock.
    - Conditional ownership renewal and release preventing accidental deletion of successor locks.
    - Pre-commit lease verification (fencing check) preventing superseded workers from committing stale results.
    - Stale worker crash recovery based on expired TTL.
    """
    def __init__(self, lock_duration_seconds: float = 30.0, poll_interval_seconds: float = 0.05):
        self.lock_duration_seconds = lock_duration_seconds
        self.poll_interval_seconds = poll_interval_seconds

    async def renew_lease(self, session_factory, lease: LockLease, extension_seconds: Optional[float] = None) -> bool:
        """
        Extends the lease expiration time.
        Only succeeds IF AND ONLY IF the database row matches locked_by AND fencing_token.
        Returns False if the lease has been lost, expired, or superseded.
        """
        ext = extension_seconds or self.lock_duration_seconds
        try:
            async with session_factory() as session:
                now = datetime.now(timezone.utc)
                result = await session.execute(
                    select(SubmissionProcessingLock).where(
                        SubmissionProcessingLock.submission_id == lease.submission_id,
                        SubmissionProcessingLock.locked_by == lease.owner_token,
                        SubmissionProcessingLock.fencing_token == lease.fencing_token
                    )
                )
                lock_row = result.scalars().first()
                if not lock_row:
                    lease.is_active = False
                    return False

                row_expiry = _ensure_utc(lock_row.expires_at)
                if row_expiry < now:
                    lease.is_active = False
                    return False

                new_expiry = now + timedelta(seconds=ext)
                lock_row.expires_at = new_expiry
                lease.expires_at = new_expiry
                await session.commit()
                return True
        except Exception as e:
            logger.debug(f"Heartbeat renewal error for {lease.submission_id}: {e}")
            return False

    async def verify_lease(self, session, lease: LockLease) -> bool:
        """
        Verifies whether the worker still holds the valid, unexpired, un-superseded lease.
        Can be checked periodically prior to staging expensive database operations.
        """
        now = datetime.now(timezone.utc)
        result = await session.execute(
            select(SubmissionProcessingLock).where(
                SubmissionProcessingLock.submission_id == lease.submission_id,
                SubmissionProcessingLock.locked_by == lease.owner_token,
                SubmissionProcessingLock.fencing_token == lease.fencing_token
            )
        )
        lock_row = result.scalars().first()
        if not lock_row or not lease.is_active:
            return False
        row_expiry = _ensure_utc(lock_row.expires_at)
        return row_expiry >= now

    async def release_lock(self, session, lease: LockLease) -> bool:
        """
        Safely releases the lock while PRESERVING the monotonic fencing token.
        Sets locked_by = None and expires_at to past epoch, ensuring:
        1. Subsequent acquisitions increment fencing_token monotonically from this persistent value.
        2. Superseded workers cannot release a successor's lock (WHERE matches owner AND fencing_token).
        """
        try:
            past = datetime(1970, 1, 1, tzinfo=timezone.utc)
            res = await session.execute(
                update(SubmissionProcessingLock)
                .where(
                    SubmissionProcessingLock.submission_id == lease.submission_id,
                    SubmissionProcessingLock.locked_by == lease.owner_token,
                    SubmissionProcessingLock.fencing_token == lease.fencing_token
                )
                .values(
                    locked_by=None,
                    expires_at=past
                )
            )
            await session.commit()
            return res.rowcount > 0
        except Exception as rel_err:
            logger.warning(f"Error releasing lock for submission {lease.submission_id} by {lease.owner_token}: {rel_err}")
            return False

    async def commit_with_fencing(self, session, lease: LockLease) -> None:
        """
        Executes an atomic fencing verification directly within the write transaction
        prior to calling session.commit().
        
        Guarantees:
        1. An atomic conditional write asserts owner_token, fencing_token, and unexpired TTL (expires_at >= now)
           in a single atomic database statement without a separate SELECT.
        2. In SQLite WAL mode, executing this write asserts exclusive write reservation for this transaction.
        3. If the lease was superseded by another worker (which acquired with higher fencing_token
           or changed locked_by) or if the lease expired (expires_at < now), rowcount == 0.
        4. When rowcount == 0, session.rollback() is invoked immediately, discarding all staged mutations
           (including deactivations of successor records and new uncommitted claims), and StaleLockException
           is raised.
        5. When rowcount == 1, session.commit() commits the extraction run, claims, and prior deactivations
           atomically with lease verification.
        """
        now = datetime.now(timezone.utc)
        
        # Single atomic conditional update asserting ownership, fencing token, and unexpired lease
        touch_stmt = (
            update(SubmissionProcessingLock)
            .where(
                SubmissionProcessingLock.submission_id == lease.submission_id,
                SubmissionProcessingLock.locked_by == lease.owner_token,
                SubmissionProcessingLock.fencing_token == lease.fencing_token,
                SubmissionProcessingLock.expires_at >= now
            )
            .values(locked_at=now)
        )
        touch_res = await session.execute(touch_stmt)
        if touch_res.rowcount == 0:
            lease.is_active = False
            await session.rollback()
            raise StaleLockException(
                f"Worker {lease.owner_token} lost lock lease for submission {lease.submission_id} "
                f"(fencing_token={lease.fencing_token}) prior to commit. "
                f"Lock expired or was superseded. Write transaction rolled back."
            )

        await session.commit()

    @asynccontextmanager
    async def acquire_lock(
        self,
        session,
        submission_id: str,
        session_factory=None,
        timeout_seconds: float = 10.0,
        worker_id: Optional[str] = None
    ):
        worker = worker_id or f"worker-{uuid.uuid4().hex[:8]}"
        loop = asyncio.get_running_loop()
        start_time = loop.time()
        lease: Optional[LockLease] = None

        while lease is None:
            now = datetime.now(timezone.utc)
            expiry = now + timedelta(seconds=self.lock_duration_seconds)
            try:
                # Query existing lock row for submission
                res = await session.execute(
                    select(SubmissionProcessingLock).where(
                        SubmissionProcessingLock.submission_id == submission_id
                    )
                )
                existing = res.scalars().first()

                if existing is None:
                    # Case 1: First acquisition for this submission -> insert with fencing_token = 1
                    fencing_tok = 1
                    new_lock = SubmissionProcessingLock(
                        submission_id=submission_id,
                        locked_by=worker,
                        fencing_token=fencing_tok,
                        locked_at=now,
                        expires_at=expiry
                    )
                    session.add(new_lock)
                    try:
                        await session.commit()
                        lease = LockLease(
                            submission_id=submission_id,
                            owner_token=worker,
                            fencing_token=fencing_tok,
                            expires_at=expiry,
                            is_active=True
                        )
                        break
                    except IntegrityError:
                        await session.rollback()

                else:
                    existing_expiry = _ensure_utc(existing.expires_at)
                    is_lock_free = (existing.locked_by is None) or (existing_expiry < now)
                    
                    if is_lock_free:
                        # Case 2: Available lock (either normally released or stale expired)
                        # Atomic Compare-And-Swap: match existing.fencing_token to prevent race conditions
                        target_fencing_tok = existing.fencing_token + 1
                        stmt = (
                            update(SubmissionProcessingLock)
                            .where(
                                SubmissionProcessingLock.submission_id == submission_id,
                                SubmissionProcessingLock.fencing_token == existing.fencing_token
                            )
                            .values(
                                locked_by=worker,
                                fencing_token=target_fencing_tok,
                                locked_at=now,
                                expires_at=expiry
                            )
                        )
                        claim_res = await session.execute(stmt)
                        if claim_res.rowcount > 0:
                            await session.commit()
                            lease = LockLease(
                                submission_id=submission_id,
                                owner_token=worker,
                                fencing_token=target_fencing_tok,
                                expires_at=expiry,
                                is_active=True
                            )
                            break
                        else:
                            # Raced with another worker whose CAS succeeded first
                            await session.rollback()
                    else:
                        # Case 3: Valid active lock held by another worker
                        await session.rollback()

            except OperationalError as op_err:
                try:
                    await session.rollback()
                except Exception:
                    pass
                logger.debug(f"SQLite lock contention for submission {submission_id}: {op_err}")

            elapsed = loop.time() - start_time
            if elapsed >= timeout_seconds:
                raise TimeoutError(
                    f"Timed out after {timeout_seconds:.1f}s waiting for processing lock on submission {submission_id}."
                )
            await asyncio.sleep(self.poll_interval_seconds)

        # Start active heartbeat renewal task if session_factory is available
        heartbeat_task: Optional[asyncio.Task] = None
        if session_factory is not None:
            renewal_interval = max(0.2, self.lock_duration_seconds / 3.0)
            async def _heartbeat_worker():
                while lease.is_active:
                    await asyncio.sleep(renewal_interval)
                    if not lease.is_active:
                        break
                    renewed = await self.renew_lease(session_factory, lease)
                    if not renewed:
                        logger.warning(f"Heartbeat failed to renew lease for {submission_id} (lost or superseded).")
                        break

            heartbeat_task = asyncio.create_task(_heartbeat_worker())

        try:
            yield lease
        finally:
            # Stop heartbeat renewal
            lease.is_active = False
            if heartbeat_task:
                heartbeat_task.cancel()
                try:
                    await heartbeat_task
                except asyncio.CancelledError:
                    pass

            # Safe release: persist fencing token, set locked_by = None, expires_at = past
            await self.release_lock(session, lease)

submission_lock_manager = SubmissionLockManager()

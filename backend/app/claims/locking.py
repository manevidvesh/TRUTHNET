import asyncio
import uuid
import logging
from datetime import datetime, timezone, timedelta
from typing import Optional
from contextlib import asynccontextmanager
from sqlalchemy import select, delete
from sqlalchemy.exc import IntegrityError, OperationalError
from app.models.claim import SubmissionProcessingLock

logger = logging.getLogger("truthnet.claims.locking")

class SubmissionLockManager:
    """
    Physical database-backed per-submission lock manager.
    Coordinates claim extraction across multiple processes, uvicorn workers,
    and concurrent async tasks without relying on in-memory locks or SQLite WAL alone.
    
    Provides:
    - Atomic database reservation via primary key uniqueness on submission_processing_locks.
    - Automatic TTL cleanup to safely recover from crashed workers.
    - Cooperative waiting with polling backoff and configurable timeouts.
    - Operates on the caller's active database session to avoid connection contention and deadlocks.
    """
    def __init__(self, lock_duration_seconds: float = 30.0, poll_interval_seconds: float = 0.05):
        self.lock_duration_seconds = lock_duration_seconds
        self.poll_interval_seconds = poll_interval_seconds

    @asynccontextmanager
    async def acquire_lock(
        self,
        session,
        submission_id: str,
        timeout_seconds: float = 10.0,
        worker_id: Optional[str] = None
    ):
        worker = worker_id or f"worker-{uuid.uuid4().hex[:8]}"
        loop = asyncio.get_running_loop()
        start_time = loop.time()
        lock_acquired = False

        while not lock_acquired:
            now = datetime.now(timezone.utc)
            try:
                # 1. Clean up any expired locks (stale worker crash recovery)
                await session.execute(
                    delete(SubmissionProcessingLock).where(
                        SubmissionProcessingLock.expires_at < now
                    )
                )
                await session.commit()

                # 2. Attempt to insert lock row for this submission
                lock_entry = SubmissionProcessingLock(
                    submission_id=submission_id,
                    locked_by=worker,
                    locked_at=now,
                    expires_at=now + timedelta(seconds=self.lock_duration_seconds)
                )
                session.add(lock_entry)
                try:
                    await session.commit()
                    lock_acquired = True
                    break
                except IntegrityError:
                    # Another active process/worker holds the lock
                    await session.rollback()
            except OperationalError as op_err:
                # SQLite busy during concurrent write; rollback and retry
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

        try:
            yield worker
        finally:
            # Release lock in database on the same session
            try:
                await session.execute(
                    delete(SubmissionProcessingLock).where(
                        SubmissionProcessingLock.submission_id == submission_id,
                        SubmissionProcessingLock.locked_by == worker
                    )
                )
                await session.commit()
            except Exception as rel_err:
                logger.warning(f"Error releasing lock for submission {submission_id} by {worker}: {rel_err}")

submission_lock_manager = SubmissionLockManager()

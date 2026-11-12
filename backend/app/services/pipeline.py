import logging
from pathlib import Path
import httpx
from sqlalchemy import select
from app.core.config import settings
from app.core.database import async_session_factory
from app.models.evidence import EvidenceSubmission, MediaAsset

logger = logging.getLogger(__name__)

class PipelineService:
    def __init__(self, session_factory=None):
        self.session_factory = session_factory

    async def process_evidence_item(self, evidence_id: str, session_factory=None) -> bool:
        """
        Asynchronously validates an ingested evidence item.
        Per-item fault isolation: any failure updates processing_status='FAILED'
        with error_message, preventing parent investigation crash.
        """
        factory = session_factory or self.session_factory or async_session_factory
        async with factory() as session:
            try:
                result = await session.execute(
                    select(EvidenceSubmission).where(EvidenceSubmission.id == evidence_id)
                )
                submission = result.scalars().first()
                if not submission:
                    logger.error(f"Evidence submission {evidence_id} not found during processing.")
                    return False

                submission.processing_status = "PROCESSING"
                await session.commit()

                # Process by submission type
                if submission.submission_type in ("IMAGE", "AUDIO", "VIDEO"):
                    # Check media asset and physical file presence
                    if not submission.media_asset_id:
                        raise ValueError(f"Missing MediaAsset for {submission.submission_type} submission")
                    
                    asset_res = await session.execute(
                        select(MediaAsset).where(MediaAsset.id == submission.media_asset_id)
                    )
                    asset = asset_res.scalars().first()
                    if not asset:
                        raise ValueError(f"MediaAsset {submission.media_asset_id} record not found")

                    file_path = (settings.BASE_DIR / "data" / asset.file_path).resolve()
                    if not file_path.exists():
                        raise FileNotFoundError(f"Binary file missing at {file_path}")
                    if file_path.stat().st_size == 0:
                        raise ValueError("Submitted media file is zero bytes (empty or corrupt)")

                elif submission.submission_type == "URL":
                    if not submission.source_url:
                        raise ValueError("No source URL provided for URL submission")
                    
                    # Validate URL reachability safely with short timeout
                    async with httpx.AsyncClient(timeout=5.0, follow_redirects=True) as client:
                        response = await client.head(submission.source_url)
                        if response.status_code >= 400:
                            # Try GET in case HEAD is disallowed
                            response = await client.get(submission.source_url)
                            if response.status_code >= 400:
                                raise ValueError(f"URL returned HTTP error status {response.status_code}")

                elif submission.submission_type == "TEXT":
                    if not submission.raw_text and not submission.caption:
                        raise ValueError("Text submission is completely empty")

                # If all validation passes:
                submission.processing_status = "COMPLETED"
                submission.error_message = None
                await session.commit()
                return True

            except Exception as e:
                logger.warning(f"Fault isolation caught error for evidence {evidence_id}: {str(e)}")
                try:
                    # Update status to FAILED and record error message
                    result = await session.execute(
                        select(EvidenceSubmission).where(EvidenceSubmission.id == evidence_id)
                    )
                    sub = result.scalars().first()
                    if sub:
                        sub.processing_status = "FAILED"
                        sub.error_message = str(e)
                        await session.commit()
                except Exception as db_err:
                    logger.error(f"Failed to record error state for {evidence_id}: {db_err}")
                return False

pipeline_service = PipelineService()

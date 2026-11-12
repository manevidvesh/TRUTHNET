import logging
from pathlib import Path
from typing import List, Optional, Dict, Any
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.storage import storage_manager
from app.models.evidence import MediaAsset, DerivedArtifact
from app.models.fingerprint import MediaFingerprint, FrameFingerprint
from app.indexing.hasher import media_hasher
from app.indexing.descriptor_store import descriptor_store

logger = logging.getLogger("truthnet.indexing.indexer")

class MediaIndexer:
    """
    Incremental indexer managing persistent MediaFingerprint and FrameFingerprint records.
    Survives application restarts and supports controlled re-indexing without data loss.
    """

    async def index_media_asset(self, db: AsyncSession, media_asset_id: str) -> Optional[MediaFingerprint]:
        asset_res = await db.execute(select(MediaAsset).where(MediaAsset.id == media_asset_id))
        asset = asset_res.scalars().first()
        if not asset:
            logger.error(f"Cannot index non-existent MediaAsset: {media_asset_id}")
            return None

        # Resolve physical file path safely
        file_path = storage_manager.resolve_safe_path(asset.file_path)
        if not file_path.exists():
            logger.error(f"MediaAsset physical file missing for indexing: {file_path}")
            return None

        # Process image asset
        if asset.mime_type.startswith("image/"):
            try:
                fp_data = media_hasher.compute_image_fingerprints(file_path)
                desc_rel_path = descriptor_store.save_descriptors(
                    asset.sha256_hash, fp_data.get("descriptors")
                )

                # Check if fingerprint already exists
                existing_res = await db.execute(
                    select(MediaFingerprint).where(MediaFingerprint.media_asset_id == media_asset_id)
                )
                fingerprint = existing_res.scalars().first()

                if not fingerprint:
                    fingerprint = MediaFingerprint(
                        media_asset_id=media_asset_id,
                        algorithm_name=fp_data["algorithm_name"],
                        algorithm_version=fp_data["algorithm_version"],
                        preprocessing_version=fp_data["preprocessing_version"],
                        parameters=fp_data["parameters"],
                        sha256_hash=asset.sha256_hash,
                        phash_hex=fp_data["phash_hex"],
                        dhash_hex=fp_data["dhash_hex"],
                        ahash_hex=fp_data["ahash_hex"],
                        colorhash_hex=fp_data["colorhash_hex"],
                        orb_keypoints_count=fp_data["orb_keypoints_count"],
                        orb_descriptor_rel_path=desc_rel_path,
                        indexing_status="INDEXED"
                    )
                    db.add(fingerprint)
                else:
                    # Controlled update without clobbering ID or creation history
                    fingerprint.algorithm_name = fp_data["algorithm_name"]
                    fingerprint.algorithm_version = fp_data["algorithm_version"]
                    fingerprint.preprocessing_version = fp_data["preprocessing_version"]
                    fingerprint.parameters = fp_data["parameters"]
                    fingerprint.phash_hex = fp_data["phash_hex"]
                    fingerprint.dhash_hex = fp_data["dhash_hex"]
                    fingerprint.ahash_hex = fp_data["ahash_hex"]
                    fingerprint.colorhash_hex = fp_data["colorhash_hex"]
                    fingerprint.orb_keypoints_count = fp_data["orb_keypoints_count"]
                    fingerprint.orb_descriptor_rel_path = desc_rel_path
                    fingerprint.indexing_status = "INDEXED"

                await db.flush()
                return fingerprint
            except Exception as e:
                logger.error(f"Failed to index MediaAsset {media_asset_id}: {e}")
                return None

        return None

    async def index_video_keyframes(
        self,
        db: AsyncSession,
        media_asset_id: str,
        keyframe_artifacts: List[DerivedArtifact]
    ) -> List[FrameFingerprint]:
        created_fps: List[FrameFingerprint] = []

        for art in keyframe_artifacts:
            if art.artifact_type != "KEYFRAME":
                continue

            frame_path = storage_manager.resolve_safe_path(art.relative_path)
            if not frame_path.exists():
                continue

            try:
                fp_data = media_hasher.compute_image_fingerprints(frame_path)
                frame_idx = (art.artifact_metadata or {}).get("frame_index", 0)
                timestamp_ms = (art.artifact_metadata or {}).get("actual_timestamp_ms", 0.0)

                existing_res = await db.execute(
                    select(FrameFingerprint).where(FrameFingerprint.derived_artifact_id == art.id)
                )
                frame_fp = existing_res.scalars().first()

                if not frame_fp:
                    frame_fp = FrameFingerprint(
                        media_asset_id=media_asset_id,
                        derived_artifact_id=art.id,
                        frame_index=frame_idx,
                        timestamp_ms=timestamp_ms,
                        algorithm_version=fp_data["algorithm_version"],
                        preprocessing_version=fp_data["preprocessing_version"],
                        phash_hex=fp_data["phash_hex"],
                        dhash_hex=fp_data["dhash_hex"]
                    )
                    db.add(frame_fp)
                else:
                    frame_fp.algorithm_version = fp_data["algorithm_version"]
                    frame_fp.preprocessing_version = fp_data["preprocessing_version"]
                    frame_fp.phash_hex = fp_data["phash_hex"]
                    frame_fp.dhash_hex = fp_data["dhash_hex"]

                created_fps.append(frame_fp)
            except Exception as e:
                logger.warning(f"Failed to index keyframe {art.id}: {e}")

        if created_fps:
            await db.flush()
        return created_fps

    async def reindex_all(self, db: AsyncSession) -> Dict[str, int]:
        assets_res = await db.execute(select(MediaAsset))
        assets = assets_res.scalars().all()

        indexed_assets_count = 0
        for asset in assets:
            if asset.mime_type.startswith("image/"):
                res = await self.index_media_asset(db, asset.id)
                if res:
                    indexed_assets_count += 1

        return {
            "total_assets_scanned": len(assets),
            "indexed_assets": indexed_assets_count
        }

media_indexer = MediaIndexer()

import logging
from pathlib import Path
from typing import Optional, Tuple
import numpy as np
from app.core.config import settings

logger = logging.getLogger("truthnet.indexing.descriptor_store")

MAX_DESCRIPTOR_FILE_BYTES = 2 * 1024 * 1024  # 2 MB limit

class DescriptorStore:
    """
    Secure storage and retrieval for binary feature descriptor matrices (ORB)
    and 2D keypoint coordinate arrays.
    Enforces strict path isolation, file size limits, allow_pickle=False,
    and dimension/dtype validation to prevent deserialization vulnerabilities.
    """

    def __init__(self, base_dir: Optional[Path] = None):
        self.base_dir = (base_dir or (settings.DATA_DIR / "derived" / "descriptors")).resolve()
        self.base_dir.mkdir(parents=True, exist_ok=True)

    def save_features(
        self,
        sha256_hash: str,
        keypoints_pts: Optional[np.ndarray],
        descriptors: Optional[np.ndarray]
    ) -> Optional[str]:
        if descriptors is None or keypoints_pts is None or len(descriptors) == 0:
            return None

        # Verify array shapes and types
        if (
            descriptors.ndim != 2 or descriptors.shape[1] != 32 or descriptors.dtype != np.uint8 or
            keypoints_pts.ndim != 2 or keypoints_pts.shape[1] != 2 or keypoints_pts.dtype != np.float32
        ):
            logger.warning(
                f"Rejecting invalid feature arrays: descs shape={getattr(descriptors, 'shape', None)}, "
                f"kps shape={getattr(keypoints_pts, 'shape', None)}"
            )
            return None

        shard_dir = self.base_dir / sha256_hash[:2]
        shard_dir.mkdir(parents=True, exist_ok=True)
        file_path = shard_dir / f"{sha256_hash}.npz"

        # Save compressed binary numpy archive without pickle
        np.savez(str(file_path), keypoints=keypoints_pts, descriptors=descriptors)

        try:
            rel_path = str(file_path.relative_to(settings.DATA_DIR))
        except ValueError:
            rel_path = f"derived/descriptors/{sha256_hash[:2]}/{sha256_hash}.npz"

        return rel_path

    def load_features(self, rel_path: str) -> Tuple[Optional[np.ndarray], Optional[np.ndarray]]:
        if not rel_path:
            return None, None

        base = settings.DATA_DIR.resolve()
        target = (base / rel_path).resolve()
        try:
            target.relative_to(base)
        except ValueError:
            logger.error(f"Security traversal violation detected in feature path: {rel_path}")
            return None, None

        if not target.exists():
            return None, None

        if target.stat().st_size > MAX_DESCRIPTOR_FILE_BYTES:
            logger.warning(f"Feature file {rel_path} exceeds maximum size limit of {MAX_DESCRIPTOR_FILE_BYTES} bytes")
            return None, None

        try:
            with np.load(str(target), allow_pickle=False) as data:
                kps = data["keypoints"]
                descs = data["descriptors"]
                if (
                    kps.ndim == 2 and kps.shape[1] == 2 and kps.dtype == np.float32 and
                    descs.ndim == 2 and descs.shape[1] == 32 and descs.dtype == np.uint8
                ):
                    return kps, descs
                else:
                    logger.warning(f"Invalid feature array structure in {rel_path}")
                    return None, None
        except Exception as e:
            logger.error(f"Failed to load features from {rel_path}: {e}")
            return None, None

    def save_descriptors(
        self,
        sha256_hash: str,
        descriptors: Optional[np.ndarray],
        keypoints_pts: Optional[np.ndarray] = None
    ) -> Optional[str]:
        if descriptors is not None and keypoints_pts is None:
            keypoints_pts = np.zeros((len(descriptors), 2), dtype=np.float32)
        return self.save_features(sha256_hash, keypoints_pts, descriptors)

    def load_descriptors(self, rel_path: str) -> Optional[np.ndarray]:
        _, descs = self.load_features(rel_path)
        return descs

descriptor_store = DescriptorStore()

import logging
from pathlib import Path
from typing import Optional
import numpy as np
from app.core.config import settings

logger = logging.getLogger("truthnet.indexing.descriptor_store")

MAX_DESCRIPTOR_FILE_BYTES = 2 * 1024 * 1024  # 2 MB limit

class DescriptorStore:
    """
    Secure storage and retrieval for binary feature descriptor matrices (ORB).
    Enforces strict path isolation, file size limits, allow_pickle=False,
    and dimension/dtype validation to prevent deserialization vulnerabilities.
    """

    def __init__(self, base_dir: Optional[Path] = None):
        self.base_dir = (base_dir or (settings.DATA_DIR / "derived" / "descriptors")).resolve()
        self.base_dir.mkdir(parents=True, exist_ok=True)

    def save_descriptors(self, sha256_hash: str, descriptors: Optional[np.ndarray]) -> Optional[str]:
        if descriptors is None or len(descriptors) == 0:
            return None

        # Verify array shape and type
        if descriptors.ndim != 2 or descriptors.shape[1] != 32 or descriptors.dtype != np.uint8:
            logger.warning(f"Rejecting invalid descriptor array with shape {descriptors.shape} and dtype {descriptors.dtype}")
            return None

        shard_dir = self.base_dir / sha256_hash[:2]
        shard_dir.mkdir(parents=True, exist_ok=True)
        file_path = shard_dir / f"{sha256_hash}.npy"

        # Save binary numpy array without pickle
        np.save(str(file_path), descriptors, allow_pickle=False)

        # Return relative path relative to settings.DATA_DIR
        try:
            rel_path = str(file_path.relative_to(settings.DATA_DIR))
        except ValueError:
            rel_path = f"derived/descriptors/{sha256_hash[:2]}/{sha256_hash}.npy"

        return rel_path

    def load_descriptors(self, rel_path: str) -> Optional[np.ndarray]:
        if not rel_path:
            return None

        # Security: Resolve safe path ensuring no traversal outside base_dir or DATA_DIR
        base = settings.DATA_DIR.resolve()
        target = (base / rel_path).resolve()
        try:
            target.relative_to(base)
        except ValueError:
            logger.error(f"Security traversal violation detected in descriptor path: {rel_path}")
            return None

        if not target.exists():
            return None

        # Check file size bound
        if target.stat().st_size > MAX_DESCRIPTOR_FILE_BYTES:
            logger.warning(f"Descriptor file {rel_path} exceeds maximum size limit of {MAX_DESCRIPTOR_FILE_BYTES} bytes")
            return None

        try:
            # Strictly load with allow_pickle=False
            data = np.load(str(target), allow_pickle=False)
            if data.ndim == 2 and data.shape[1] == 32 and data.dtype == np.uint8:
                return data
            else:
                logger.warning(f"Corrupt or invalid descriptor structure loaded from {rel_path}: shape {data.shape}")
                return None
        except Exception as e:
            logger.error(f"Failed to load descriptor array from {rel_path}: {e}")
            return None

descriptor_store = DescriptorStore()

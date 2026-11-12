import logging
from pathlib import Path
from typing import Tuple, Dict, Any
from PIL import Image, ImageOps
import numpy as np
import cv2

logger = logging.getLogger("truthnet.indexing.preprocessing")

class ImagePreprocessor:
    """
    Deterministic image preprocessor with explicit versioning (PREPROCESS-V1).
    Ensures identical normalization for orientation, color space, and alpha transparency
    across all platforms before computing perceptual hashes or feature descriptors.
    """

    PREPROCESSING_VERSION = "PREPROCESS-V1"

    @classmethod
    def preprocess_image(cls, image_path: Path) -> Tuple[Image.Image, np.ndarray, Dict[str, Any]]:
        metadata = {
            "preprocessing_version": cls.PREPROCESSING_VERSION,
            "original_format": None,
            "original_mode": None,
            "orientation_corrected": False,
            "alpha_flattened": False
        }

        with Image.open(image_path) as raw_img:
            metadata["original_format"] = raw_img.format
            metadata["original_mode"] = raw_img.mode

            # Animated GIF / WebP: seek to first frame
            if getattr(raw_img, "is_animated", False):
                raw_img.seek(0)

            # 1. EXIF Orientation correction
            try:
                transposed = ImageOps.exif_transpose(raw_img)
                if transposed is not None:
                    img = transposed
                    metadata["orientation_corrected"] = True
                else:
                    img = raw_img.copy()
            except Exception:
                img = raw_img.copy()

            # 2. Alpha Transparency Compositing onto Solid White (255, 255, 255)
            if img.mode in ("RGBA", "LA") or (img.mode == "P" and "transparency" in img.info):
                metadata["alpha_flattened"] = True
                rgba = img.convert("RGBA")
                white_bg = Image.new("RGBA", rgba.size, (255, 255, 255, 255))
                composited = Image.alpha_composite(white_bg, rgba)
                rgb_img = composited.convert("RGB")
            else:
                rgb_img = img.convert("RGB")

            # 3. Grayscale OpenCV array for feature detection
            np_rgb = np.array(rgb_img)
            gray_cv = cv2.cvtColor(np_rgb, cv2.COLOR_RGB2GRAY)

            return rgb_img, gray_cv, metadata

preprocessor = ImagePreprocessor()

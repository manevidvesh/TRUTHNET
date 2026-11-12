import logging
from pathlib import Path
from typing import Dict, Any, Optional
import imagehash
import cv2
import numpy as np
from app.indexing.preprocessing import preprocessor

logger = logging.getLogger("truthnet.indexing.hasher")

class MediaHasher:
    """
    Computes cryptographic, perceptual, and local feature descriptors
    from deterministically preprocessed media.
    Perceptual hashes serve as candidate generators; ORB descriptors support geometric verification.
    """

    ALGORITHM_NAME = "TRUTHNET-PERCEPTUAL-HASH"
    ALGORITHM_VERSION = "1.0.0"
    DEFAULT_PARAMETERS = {
        "hash_size": 8,
        "orb_nfeatures": 1000,
        "orb_scale_factor": 1.2,
        "orb_nlevels": 8
    }

    def __init__(self):
        self.orb = cv2.ORB_create(
            nfeatures=self.DEFAULT_PARAMETERS["orb_nfeatures"],
            scaleFactor=self.DEFAULT_PARAMETERS["orb_scale_factor"],
            nlevels=self.DEFAULT_PARAMETERS["orb_nlevels"]
        )

    def compute_image_fingerprints(self, image_path: Path) -> Dict[str, Any]:
        rgb_img, gray_cv, prep_meta = preprocessor.preprocess_image(image_path)

        # 1. Perceptual candidate hashes
        phash = str(imagehash.phash(rgb_img, hash_size=8))
        dhash = str(imagehash.dhash(rgb_img, hash_size=8))
        ahash = str(imagehash.average_hash(rgb_img, hash_size=8))
        colorhash = str(imagehash.colorhash(rgb_img))

        # 2. ORB Keypoints and Descriptors
        kps, descs = self.orb.detectAndCompute(gray_cv, None)
        keypoints_count = len(kps) if kps else 0

        return {
            "algorithm_name": self.ALGORITHM_NAME,
            "algorithm_version": self.ALGORITHM_VERSION,
            "preprocessing_version": prep_meta["preprocessing_version"],
            "parameters": self.DEFAULT_PARAMETERS,
            "phash_hex": phash,
            "dhash_hex": dhash,
            "ahash_hex": ahash,
            "colorhash_hex": colorhash,
            "orb_keypoints_count": keypoints_count,
            "descriptors": descs,
            "preprocessing_meta": prep_meta
        }

    @staticmethod
    def hamming_distance(h1_hex: str, h2_hex: str) -> int:
        """
        Computes the bitwise Hamming distance between two 64-bit hexadecimal hash strings.
        """
        if not h1_hex or not h2_hex:
            return 64
        try:
            val1 = int(h1_hex, 16)
            val2 = int(h2_hex, 16)
            return bin(val1 ^ val2).count("1")
        except ValueError:
            return 64

media_hasher = MediaHasher()

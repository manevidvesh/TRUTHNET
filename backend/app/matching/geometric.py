import time
import logging
from typing import Dict, Any, Optional
import cv2
import numpy as np

logger = logging.getLogger("truthnet.matching.geometric")

class GeometricVerifier:
    """
    Evaluates geometric projective consistency between query and candidate ORB features
    using Lowe's ratio test and RANSAC homography estimation.
    Distinguishes feature-poor media from geometrically rejected transformations.
    Never outputs arbitrary confidence scores or event-level inferences.
    """

    DEFAULT_MIN_KEYPOINTS = 10
    DEFAULT_MIN_INLIERS = 12
    DEFAULT_MIN_INLIER_RATIO = 0.20
    DEFAULT_LOWE_RATIO = 0.75
    DEFAULT_RANSAC_REPROJ_THRESH = 5.0

    def verify_geometry(
        self,
        query_pts: Optional[np.ndarray],
        query_descs: Optional[np.ndarray],
        cand_pts: Optional[np.ndarray],
        cand_descs: Optional[np.ndarray],
        min_keypoints: int = DEFAULT_MIN_KEYPOINTS,
        min_inliers: int = DEFAULT_MIN_INLIERS,
        min_inlier_ratio: float = DEFAULT_MIN_INLIER_RATIO
    ) -> Dict[str, Any]:
        t_start = time.perf_counter()

        q_count = len(query_descs) if query_descs is not None else 0
        c_count = len(cand_descs) if cand_descs is not None else 0

        result: Dict[str, Any] = {
            "status": "UNPROCESSED",
            "is_geometric_match": False,
            "keypoints_query": q_count,
            "keypoints_candidate": c_count,
            "good_matches_count": 0,
            "inlier_count": 0,
            "inlier_ratio": 0.0,
            "min_inliers_threshold": min_inliers,
            "min_inlier_ratio_threshold": min_inlier_ratio,
            "homography_matrix": None,
            "failure_reason": None,
            "verification_latency_ms": 0.0
        }

        # 1. Check feature count
        if query_descs is None or query_pts is None or q_count < min_keypoints:
            result["status"] = "INSUFFICIENT_FEATURES"
            result["failure_reason"] = f"Query media has {q_count} keypoints (minimum {min_keypoints} required)"
            result["verification_latency_ms"] = round((time.perf_counter() - t_start) * 1000.0, 2)
            return result

        if cand_descs is None or cand_pts is None or c_count < min_keypoints:
            result["status"] = "INSUFFICIENT_FEATURES"
            result["failure_reason"] = f"Candidate media has {c_count} keypoints (minimum {min_keypoints} required)"
            result["verification_latency_ms"] = round((time.perf_counter() - t_start) * 1000.0, 2)
            return result

        try:
            # 2. Match ORB descriptors using Hamming distance
            bf = cv2.BFMatcher(cv2.NORM_HAMMING, crossCheck=False)
            knn_matches = bf.knnMatch(query_descs, cand_descs, k=2)

            # 3. Apply Lowe's ratio test
            good_matches = []
            for m_pair in knn_matches:
                if len(m_pair) == 2:
                    m, n = m_pair
                    if m.distance < self.DEFAULT_LOWE_RATIO * n.distance:
                        good_matches.append(m)

            result["good_matches_count"] = len(good_matches)

            if len(good_matches) < 4:
                result["status"] = "GEOMETRIC_TRANSFORMATION_REJECTED"
                result["failure_reason"] = f"Only {len(good_matches)} Lowe-ratio matches found (minimum 4 required for homography)"
                result["verification_latency_ms"] = round((time.perf_counter() - t_start) * 1000.0, 2)
                return result

            # 4. Extract matched coordinates for RANSAC
            src_pts = np.float32([query_pts[m.queryIdx] for m in good_matches]).reshape(-1, 1, 2)
            dst_pts = np.float32([cand_pts[m.trainIdx] for m in good_matches]).reshape(-1, 1, 2)

            H, mask = cv2.findHomography(src_pts, dst_pts, cv2.RANSAC, self.DEFAULT_RANSAC_REPROJ_THRESH)

            if H is None or mask is None:
                result["status"] = "GEOMETRIC_TRANSFORMATION_REJECTED"
                result["failure_reason"] = "RANSAC failed to fit projective homography"
                result["verification_latency_ms"] = round((time.perf_counter() - t_start) * 1000.0, 2)
                return result

            inliers = int(np.sum(mask))
            inlier_ratio = round(float(inliers) / float(len(good_matches)), 4) if len(good_matches) > 0 else 0.0

            result["inlier_count"] = inliers
            result["inlier_ratio"] = inlier_ratio
            result["homography_matrix"] = H.tolist()

            # 5. Evaluate geometric match thresholds
            if inliers >= min_inliers and inlier_ratio >= min_inlier_ratio:
                result["status"] = "GEOMETRIC_MATCH_CONFIRMED"
                result["is_geometric_match"] = True
            else:
                result["status"] = "GEOMETRIC_TRANSFORMATION_REJECTED"
                result["is_geometric_match"] = False
                result["failure_reason"] = (
                    f"Inliers {inliers} or ratio {inlier_ratio} fell below thresholds "
                    f"({min_inliers}, {min_inlier_ratio})"
                )

        except Exception as e:
            logger.error(f"Geometric verification error: {e}")
            result["status"] = "ERROR"
            result["failure_reason"] = str(e)

        result["verification_latency_ms"] = round((time.perf_counter() - t_start) * 1000.0, 2)
        return result

geometric_verifier = GeometricVerifier()

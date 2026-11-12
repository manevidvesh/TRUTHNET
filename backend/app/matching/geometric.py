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

    @staticmethod
    def validate_homography(
        H: Optional[np.ndarray],
        src_inliers: np.ndarray,
        dst_inliers: np.ndarray
    ) -> Tuple[bool, str]:
        """
        Validates mathematical non-degeneracy of estimated projective homography matrix.
        Rejects inverted orientations (det <= 0), singular collapses (cond > 1e4),
        extreme scale distortion, and collinear inliers spanning < 15px.
        """
        if H is None or np.isnan(H).any() or np.isinf(H).any():
            return False, "Homography matrix contains NaN or Inf values"

        # Normalize matrix so H[2, 2] == 1.0
        if abs(H[2, 2]) < 1e-8:
            return False, "Degenerate projective scale (H[2, 2] near zero)"
        H_norm = H / H[2, 2]

        A = H_norm[:2, :2]
        det = float(np.linalg.det(A))
        if det <= 0.0:
            return False, f"Degenerate orientation reflection (det(A)={det:.4f} <= 0)"

        if det < 0.005 or det > 200.0:
            return False, f"Extreme projective scale distortion (det(A)={det:.4f})"

        try:
            cond = float(np.linalg.cond(A))
            if cond > 50.0 or np.isinf(cond) or np.isnan(cond):
                return False, f"Ill-conditioned singular affine submatrix (cond(A)={cond:.1f} > 50)"
        except Exception as e:
            return False, f"Condition number computation failed: {e}"

        # Inlier spatial dispersion check (prevent 1D line of inliers faking 2D homography)
        if len(src_inliers) < 4:
            return False, "Fewer than 4 inliers for homography"

        src_pts = src_inliers.reshape(-1, 2)
        src_w = float(np.ptp(src_pts[:, 0]))
        src_h = float(np.ptp(src_pts[:, 1]))
        if src_w < 15.0 or src_h < 15.0:
            return False, f"Collinear or collapsed inliers in query media (w={src_w:.1f}px, h={src_h:.1f}px)"

        dst_pts = dst_inliers.reshape(-1, 2)
        dst_w = float(np.ptp(dst_pts[:, 0]))
        dst_h = float(np.ptp(dst_pts[:, 1]))
        if dst_w < 15.0 or dst_h < 15.0:
            return False, f"Collinear or collapsed inliers in candidate media (w={dst_w:.1f}px, h={dst_h:.1f}px)"

        return True, "Valid projective planar transformation"

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

            # Extract inlier subsets for validation
            inlier_mask = mask.ravel().astype(bool)
            src_inliers = src_pts[inlier_mask]
            dst_inliers = dst_pts[inlier_mask]

            is_valid_H, h_reason = self.validate_homography(H, src_inliers, dst_inliers)
            result["homography_valid"] = is_valid_H
            result["homography_validation_reason"] = h_reason

            # 5. Evaluate geometric match thresholds
            if inliers >= min_inliers and inlier_ratio >= min_inlier_ratio:
                if is_valid_H:
                    result["status"] = "GEOMETRIC_MATCH_CONFIRMED"
                    result["is_geometric_match"] = True
                else:
                    result["status"] = "GEOMETRIC_TRANSFORMATION_REJECTED"
                    result["is_geometric_match"] = False
                    result["failure_reason"] = f"Homography rejected: {h_reason}"
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

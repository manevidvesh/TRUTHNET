import hashlib
import logging
from pathlib import Path
from typing import Any, Dict, List, Tuple
import cv2
from app.core.config import settings

logger = logging.getLogger("truthnet.extractors.video_frames")

class KeyframeExtractor:
    """
    Extracts boundary-anchored visual keyframes from video files.
    Always includes the first and last decodable frames alongside uniform intermediate samples.
    Computes SHA-256 hash for every extracted frame artifact.
    Includes explicit sampling disclaimers.
    """

    def __init__(self, derived_dir: Path | None = None):
        self.derived_dir = derived_dir or (settings.DATA_DIR / "derived")

    def extract_keyframes(
        self,
        video_path: Path,
        evidence_id: str,
        max_frames: int = 15,
        target_interval_sec: float = 1.0
    ) -> Tuple[List[Dict[str, Any]], Dict[str, Any]]:
        """
        Extracts keyframes from video file.
        Returns:
            (frames_metadata_list, extraction_summary)
        """
        frames: List[Dict[str, Any]] = []
        summary: Dict[str, Any] = {
            "strategy": "BOUNDARY_ANCHORED_UNIFORM_INTERVAL",
            "max_frames_limit": max_frames,
            "target_interval_seconds": target_interval_sec,
            "total_frames_extracted": 0,
            "skipped_frames": 0,
            "first_frame_ms": None,
            "last_frame_ms": None,
            "disclaimer": "Sampled keyframes represent discrete observed visual checkpoints and do not establish whole-video authenticity.",
            "status": "COMPLETED"
        }

        if not video_path.exists():
            summary["status"] = "FAILED"
            summary["error"] = "Video file does not exist"
            return frames, summary

        cap = cv2.VideoCapture(str(video_path))
        if not cap.isOpened():
            summary["status"] = "FAILED"
            summary["error"] = "Failed to open video container with OpenCV decoder"
            return frames, summary

        try:
            total_frames_count = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
            fps = cap.get(cv2.CAP_PROP_FPS)
            duration_ms = (total_frames_count / fps * 1000.0) if (fps and fps > 0 and total_frames_count > 0) else 0.0

            # Target output directory: data/derived/{evidence_id}/frames/
            out_dir = self.derived_dir / evidence_id / "frames"
            out_dir.mkdir(parents=True, exist_ok=True)

            target_timestamps_ms: List[float] = []

            # 1. Boundary: First frame (0 ms)
            target_timestamps_ms.append(0.0)

            # 2. Intermediate frames
            if duration_ms > 1000.0:
                interval_ms = target_interval_sec * 1000.0
                curr = interval_ms
                while curr < (duration_ms - 200.0):
                    target_timestamps_ms.append(curr)
                    curr += interval_ms

            # 3. Boundary: Last frame
            if duration_ms > 0:
                target_timestamps_ms.append(max(0.0, duration_ms - 50.0))

            # If intermediate samples exceed max_frames, subsample evenly keeping first and last
            if len(target_timestamps_ms) > max_frames:
                first = target_timestamps_ms[0]
                last = target_timestamps_ms[-1]
                middle = target_timestamps_ms[1:-1]
                step = len(middle) / (max_frames - 2)
                sampled_middle = [middle[int(i * step)] for i in range(max_frames - 2)]
                target_timestamps_ms = [first] + sampled_middle + [last]

            # Remove duplicate timestamps that are too close
            deduped_ms: List[float] = []
            for ts in target_timestamps_ms:
                if not deduped_ms or (ts - deduped_ms[-1] >= 100.0):
                    deduped_ms.append(ts)
            target_timestamps_ms = deduped_ms

            frame_idx = 0
            for i, ts_ms in enumerate(target_timestamps_ms):
                cap.set(cv2.CAP_PROP_POS_MSEC, ts_ms)
                ret, frame_img = cap.read()
                if not ret or frame_img is None:
                    summary["skipped_frames"] += 1
                    continue

                actual_ms = cap.get(cv2.CAP_PROP_POS_MSEC)
                height, width = frame_img.shape[:2]
                
                # Encode JPEG
                ret_enc, buffer = cv2.imencode(".jpg", frame_img, [cv2.IMWRITE_JPEG_QUALITY, 90])
                if not ret_enc:
                    summary["skipped_frames"] += 1
                    continue

                frame_bytes = buffer.tobytes()
                frame_sha256 = hashlib.sha256(frame_bytes).hexdigest()

                filename = f"frame_{frame_idx}_{int(actual_ms)}ms.jpg"
                file_path = out_dir / filename
                file_path.write_bytes(frame_bytes)

                base_data_dir = self.derived_dir.parent
                try:
                    rel_path = str(file_path.relative_to(base_data_dir))
                except ValueError:
                    rel_path = f"derived/{evidence_id}/frames/{filename}"
                is_boundary = (i == 0 or i == len(target_timestamps_ms) - 1)

                frame_info = {
                    "frame_index": frame_idx,
                    "target_timestamp_ms": round(ts_ms, 2),
                    "actual_timestamp_ms": round(actual_ms, 2),
                    "width": width,
                    "height": height,
                    "sha256_hash": frame_sha256,
                    "relative_path": rel_path,
                    "file_size_bytes": len(frame_bytes),
                    "mime_type": "image/jpeg",
                    "is_boundary_frame": is_boundary
                }
                frames.append(frame_info)

                if summary["first_frame_ms"] is None:
                    summary["first_frame_ms"] = round(actual_ms, 2)
                summary["last_frame_ms"] = round(actual_ms, 2)
                frame_idx += 1

            summary["total_frames_extracted"] = len(frames)
            if len(frames) == 0:
                summary["status"] = "FAILED"
                summary["error"] = "No decodable frames found in video"

        except Exception as e:
            logger.error(f"Keyframe extraction failed on {video_path}: {e}")
            summary["status"] = "FAILED"
            summary["error"] = str(e)
        finally:
            cap.release()

        return frames, summary

keyframe_extractor = KeyframeExtractor()

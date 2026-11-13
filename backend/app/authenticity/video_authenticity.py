"""
Video Frame Authenticity Analyzer.

Evaluates authenticity across boundary-anchored visual keyframes sampled from video evidence:
- Runs technical forensics (ELA, noise residuals, 2D spectral decay, face boundaries) per frame.
- Runs executable manipulation detection models per frame.
- Computes cross-frame temporal consistency and variance.
- Enforces strict epistemic transparency: keyframe sampling does not prove whole-video authenticity.
"""

import logging
from pathlib import Path
from typing import Dict, Any, List, Optional, Tuple
import numpy as np
from PIL import Image
import cv2

from app.authenticity.forensics import TechnicalForensicsEngine
from app.authenticity.registry import model_registry, ModelStatus
from app.extractors.video_frames import keyframe_extractor

logger = logging.getLogger("truthnet.authenticity.video")


class VideoAuthenticityAnalyzer:
    """
    Analyzes sampled keyframes of video evidence with cross-frame consistency tracking.
    """

    VIDEO_DISCLAIMER = (
        "Discrete keyframe analysis evaluates spatial compression, frequency spectra, and noise residuals "
        "across sampled visual checkpoints. It does NOT verify inter-frame optical flow, temporal warping, "
        "or audio-visual synchrony, and does NOT establish whole-video authenticity. Manipulation may exist "
        "in un-sampled frames or subtle motion trajectories."
    )

    @classmethod
    def analyze_video(
        cls,
        video_path: Path,
        evidence_id: str,
        keyframe_records: Optional[List[Dict[str, Any]]] = None,
        max_frames_to_analyze: int = 6
    ) -> Dict[str, Any]:
        """
        Analyzes keyframes from video evidence.
        Accepts pre-extracted keyframes (from derived artifacts) or extracts them on demand.
        """
        frame_analyses: List[Dict[str, Any]] = []

        # If keyframe files provided from pipeline, use them; otherwise extract
        candidate_frames: List[Tuple[float, Path]] = []
        if keyframe_records:
            for kf in keyframe_records:
                ts_ms = kf.get("timestamp_ms", kf.get("actual_timestamp_ms", 0.0))
                p = kf.get("absolute_path") or kf.get("path")
                if p and Path(p).exists():
                    candidate_frames.append((float(ts_ms), Path(p)))

        # Subsample candidate frames if too many
        if candidate_frames and len(candidate_frames) > max_frames_to_analyze:
            step = len(candidate_frames) / max_frames_to_analyze
            candidate_frames = [candidate_frames[int(i * step)] for i in range(max_frames_to_analyze)]

        # If no candidates found from records, extract a few frames directly
        if not candidate_frames and video_path.exists():
            extracted, summary = keyframe_extractor.extract_keyframes(
                video_path=video_path,
                evidence_id=evidence_id,
                max_frames=max_frames_to_analyze,
                target_interval_sec=2.0
            )
            for ef in extracted:
                rel = ef.get("relative_path")
                if rel:
                    # Resolve to absolute path
                    abs_p = (keyframe_extractor.derived_dir.parent / rel).resolve()
                    if abs_p.exists():
                        candidate_frames.append((float(ef.get("actual_timestamp_ms", 0.0)), abs_p))

        # Analyze each frame
        ela_errors: List[float] = []
        noise_vars: List[float] = []
        spectral_slopes: List[float] = []

        for idx, (ts_ms, fpath) in enumerate(candidate_frames):
            try:
                with Image.open(fpath) as pil_img:
                    rgb_img = pil_img.convert("RGB")
                    img_np = np.array(rgb_img)

                    # 1. Technical Forensics on frame
                    ela_res = TechnicalForensicsEngine.compute_ela(rgb_img, quality=90)
                    noise_res = TechnicalForensicsEngine.compute_noise_residuals(img_np)
                    spectral_res = TechnicalForensicsEngine.compute_spectral_decay(img_np)
                    face_res = TechnicalForensicsEngine.analyze_face_boundary_gradients(img_np)

                    ela_errors.append(ela_res["mean_error"])
                    noise_vars.append(noise_res["channel_divergence"])
                    spectral_slopes.append(spectral_res["decay_slope"])

                    # 2. Executable Models on frame
                    models_res = []
                    for model_id in ["spectral_dct_classifier_v1", "noise_residual_consistency_v1"]:
                        inf_res = model_registry.execute_inference(
                            model_id=model_id,
                            image_np=img_np,
                            mime_type="image/jpeg",
                            metadata={"video_timestamp_ms": ts_ms, "frame_index": idx}
                        )
                        models_res.append(inf_res)

                    frame_analyses.append({
                        "frame_index": idx,
                        "timestamp_ms": round(ts_ms, 2),
                        "timestamp_seconds": round(ts_ms / 1000.0, 3),
                        "frame_path": str(fpath.name),
                        "ela_mean_error": ela_res["mean_error"],
                        "ela_divergence_ratio": ela_res["high_divergence_ratio"],
                        "noise_channel_divergence": noise_res["channel_divergence"],
                        "spectral_decay_slope": spectral_res["decay_slope"],
                        "high_frequency_peak_ratio": spectral_res["high_freq_peak_ratio"],
                        "faces_detected": face_res.get("faces_detected", 0) if face_res else 0,
                        "model_inferences": models_res
                    })
            except Exception as e:
                logger.error(f"Failed analyzing video frame {idx} ({fpath}): {e}")
                frame_analyses.append({
                    "frame_index": idx,
                    "timestamp_ms": round(ts_ms, 2),
                    "error": str(e)
                })

        # Calculate temporal stability across frames
        temporal_consistency = {
            "frames_analyzed_count": len(frame_analyses),
            "ela_mean_cross_frame": round(float(np.mean(ela_errors)), 4) if ela_errors else 0.0,
            "ela_std_cross_frame": round(float(np.std(ela_errors)), 4) if ela_errors else 0.0,
            "noise_divergence_mean": round(float(np.mean(noise_vars)), 4) if noise_vars else 0.0,
            "noise_divergence_std": round(float(np.std(noise_vars)), 4) if noise_vars else 0.0,
            "spectral_slope_mean": round(float(np.mean(spectral_slopes)), 4) if spectral_slopes else 0.0,
            "spectral_slope_std": round(float(np.std(spectral_slopes)), 4) if spectral_slopes else 0.0,
            "temporal_variation_status": (
                "STABLE_SPATIAL_METRICS" if (len(ela_errors) > 1 and np.std(ela_errors) < 4.0)
                else "ELEVATED_CROSS_FRAME_VARIATION" if len(ela_errors) > 1
                else "SINGLE_FRAME_OR_INSUFFICIENT_SAMPLES"
            )
        }

        return {
            "video_frame_analyses": frame_analyses,
            "temporal_consistency": temporal_consistency,
            "total_frames_analyzed": len(frame_analyses),
            "sampling_method": "BOUNDARY_ANCHORED_UNIFORM_INTERVAL",
            "epistemic_disclaimer": cls.VIDEO_DISCLAIMER
        }


video_authenticity_analyzer = VideoAuthenticityAnalyzer()

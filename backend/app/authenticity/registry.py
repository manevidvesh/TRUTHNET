"""
Model Registry & Execution Engine for Media Authenticity & Deepfake Detection.

Maintains an auditable registry of manipulation detection models with:
- Model architecture, version, runtime, and supported formats.
- Checkpoint and dependency availability verification.
- Explicit lifecycle states:
  MODEL_AVAILABLE, MODEL_LOADED, INFERENCE_EXECUTED,
  MODEL_CHECKPOINT_UNAVAILABLE, DEPENDENCY_UNAVAILABLE,
  UNSUPPORTED_INPUT, INFERENCE_FAILED.
- Execution dispatch for available models with raw measurements and limitations.
- Strict epistemic truthfulness: never claims a model ran when it was only registered.
"""

import sys
import platform
import logging
from typing import Dict, Any, List, Optional, Tuple
import numpy as np

logger = logging.getLogger("truthnet.authenticity.registry")


class ModelStatus:
    MODEL_AVAILABLE = "MODEL_AVAILABLE"
    MODEL_LOADED = "MODEL_LOADED"
    INFERENCE_EXECUTED = "INFERENCE_EXECUTED"
    MODEL_CHECKPOINT_UNAVAILABLE = "MODEL_CHECKPOINT_UNAVAILABLE"
    DEPENDENCY_UNAVAILABLE = "DEPENDENCY_UNAVAILABLE"
    UNSUPPORTED_INPUT = "UNSUPPORTED_INPUT"
    INFERENCE_FAILED = "INFERENCE_FAILED"


class RegisteredModel:
    def __init__(
        self,
        model_id: str,
        name: str,
        architecture: str,
        version: str,
        supported_modalities: List[str],
        supported_formats: List[str],
        dependency_name: str,
        dependency_available: bool,
        checkpoint_name: str,
        checkpoint_available: bool,
        runtime_device: str,
        known_limitations: List[str],
        description: str,
        inference_callable=None
    ):
        self.model_id = model_id
        self.name = name
        self.architecture = architecture
        self.version = version
        self.supported_modalities = supported_modalities
        self.supported_formats = supported_formats
        self.dependency_name = dependency_name
        self.dependency_available = dependency_available
        self.checkpoint_name = checkpoint_name
        self.checkpoint_available = checkpoint_available
        self.runtime_device = runtime_device
        self.known_limitations = known_limitations
        self.description = description
        self.inference_callable = inference_callable

    @property
    def status(self) -> str:
        if not self.dependency_available:
            return ModelStatus.DEPENDENCY_UNAVAILABLE
        if not self.checkpoint_available:
            return ModelStatus.MODEL_CHECKPOINT_UNAVAILABLE
        return ModelStatus.MODEL_AVAILABLE

    def to_dict(self) -> Dict[str, Any]:
        return {
            "model_id": self.model_id,
            "name": self.name,
            "architecture": self.architecture,
            "version": self.version,
            "supported_modalities": self.supported_modalities,
            "supported_formats": self.supported_formats,
            "checkpoint_available": self.checkpoint_available,
            "dependency_available": self.dependency_available,
            "runtime_device": self.runtime_device,
            "status": self.status,
            "known_limitations": self.known_limitations,
            "description": self.description
        }


class ModelRegistry:
    """
    Central auditable catalog of all deepfake and media authenticity models.
    """

    def __init__(self):
        self.models: Dict[str, RegisteredModel] = {}
        self._detect_environment()
        self._register_default_models()

    def _detect_environment(self):
        self.has_torch = "torch" in sys.modules or self._check_import("torch")
        self.has_ort = "onnxruntime" in sys.modules or self._check_import("onnxruntime")
        self.has_scipy = "scipy" in sys.modules or self._check_import("scipy")
        self.has_sklearn = "sklearn" in sys.modules or self._check_import("sklearn")
        self.has_cv2 = "cv2" in sys.modules or self._check_import("cv2")
        self.has_cuda = False
        if self.has_torch:
            try:
                import torch
                self.has_cuda = torch.cuda.is_available()
            except Exception:
                self.has_cuda = False

        import os
        self.hardware_runtime = {
            "platform": platform.platform(),
            "python_version": platform.python_version(),
            "processor": platform.processor(),
            "cpu_cores": os.cpu_count() or 1,
            "onnxruntime_available": self.has_ort,
            "torch_available": self.has_torch,
            "cuda_available": self.has_cuda,
            "scipy_available": self.has_scipy,
            "opencv_available": self.has_cv2,
            "default_device": "cuda" if self.has_cuda else "cpu"
        }

    @property
    def hardware_info(self) -> Dict[str, Any]:
        return self.hardware_runtime

    @staticmethod
    def _check_import(mod_name: str) -> bool:
        try:
            __import__(mod_name)
            return True
        except ImportError:
            return False

    def _register_default_models(self):
        # 1. Spectral DCT Frequency Classifier (Active / Executable)
        from app.authenticity.forensics import execute_spectral_dct_inference
        self.models["spectral_dct_classifier_v1"] = RegisteredModel(
            model_id="spectral_dct_classifier_v1",
            name="Azimuthal Frequency DCT Classifier",
            architecture="Radial-DCT-Profile-Analysis (Frank et al. / Durall et al.)",
            version="1.0.0",
            supported_modalities=["IMAGE"],
            supported_formats=["image/jpeg", "image/png", "image/webp", "image/bmp"],
            dependency_name="scipy+numpy",
            dependency_available=self.has_scipy,
            checkpoint_name="analytical_radial_profile",
            checkpoint_available=True,
            runtime_device="cpu",
            known_limitations=[
                "Identifies periodic grid upsampling artifacts characteristic of GAN/Diffusion synthesis.",
                "Does not detect subtle non-generative face swaps or localized splicing.",
                "High-frequency image noise from physical optical grain can increase baseline variance."
            ],
            description="Analyzes radial power spectrum distribution across spatial frequencies to detect synthetic grid artifacts.",
            inference_callable=execute_spectral_dct_inference
        )

        # 2. Wavelet Laplacian Noise Consistency Detector (Active / Executable)
        from app.authenticity.forensics import execute_noise_residual_inference
        self.models["noise_residual_consistency_v1"] = RegisteredModel(
            model_id="noise_residual_consistency_v1",
            name="Wavelet Laplacian Noise Residual Consistency Detector",
            architecture="HighPass-Laplacian-Residual-Covariance (Popescu & Farid)",
            version="1.0.0",
            supported_modalities=["IMAGE"],
            supported_formats=["image/jpeg", "image/png", "image/webp"],
            dependency_name="cv2+numpy",
            dependency_available=self.has_cv2,
            checkpoint_name="deterministic_highpass_kernel",
            checkpoint_available=True,
            runtime_device="cpu",
            known_limitations=[
                "Measures noise variance alignment across color planes and spatial regions.",
                "Aggressive social media lossy compression can suppress high-frequency noise fields.",
                "Low-light physical photographs exhibit natural sensor photon noise non-uniformity."
            ],
            description="Extracts high-frequency noise residuals to detect spliced elements with mismatched sensor noise signatures.",
            inference_callable=execute_noise_residual_inference
        )

        # 3. MesoNet-4 Facial Manipulation Detector (Checkpoints Unavailable)
        self.models["mesonet4_facial_manipulation"] = RegisteredModel(
            model_id="mesonet4_facial_manipulation",
            name="MesoNet-4 Deepfake Facial Detector",
            architecture="Meso4-CNN (Afchar et al. 2018)",
            version="4.0.0",
            supported_modalities=["IMAGE", "VIDEO"],
            supported_formats=["image/jpeg", "image/png", "video/mp4"],
            dependency_name="tensorflow/keras",
            dependency_available=False,
            checkpoint_name="mesonet4_df_weights.h5",
            checkpoint_available=False,
            runtime_device="cpu",
            known_limitations=[
                "Evaluates mesoscopic facial compression and blending inconsistencies.",
                "Currently UNAVAILABLE: requires local packaging of MesoNet-4 weights (54MB) and Keras runtime."
            ],
            description="Compact CNN designed to detect eye and mouth boundary manipulations in face swap videos.",
            inference_callable=None
        )

        # 4. XceptionNet FaceForensics++ (Dependency Unavailable)
        self.models["xception_faceforensics"] = RegisteredModel(
            model_id="xception_faceforensics",
            name="XceptionNet Deepfake Detector (FaceForensics++)",
            architecture="Xception-c23 (Rössler et al. 2019)",
            version="1.2.0",
            supported_modalities=["IMAGE", "VIDEO"],
            supported_formats=["image/jpeg", "image/png", "video/mp4"],
            dependency_name="torch+torchvision",
            dependency_available=self.has_torch,
            checkpoint_name="ff_c23_xception.pth",
            checkpoint_available=False,
            runtime_device="cpu",
            known_limitations=[
                "Standard academic benchmark for DeepFakes, Face2Face, FaceSwap, and NeuralTextures.",
                "Currently UNAVAILABLE: requires PyTorch/torchvision runtime and 180MB model checkpoint."
            ],
            description="Deep convolutional architecture trained on FaceForensics++ c23 compressed video datasets.",
            inference_callable=None
        )

        # 5. Wang2020 CNN-Generated Image Detector (Checkpoint Unavailable)
        self.models["cnndetect_resnet50"] = RegisteredModel(
            model_id="cnndetect_resnet50",
            name="Wang2020 CNN-Generated Image Detector",
            architecture="ResNet50-Blur-JPEG (Wang et al. 2020)",
            version="2020.1",
            supported_modalities=["IMAGE"],
            supported_formats=["image/jpeg", "image/png", "image/webp"],
            dependency_name="torch",
            dependency_available=self.has_torch,
            checkpoint_name="wang2020_progan.pth",
            checkpoint_available=False,
            runtime_device="cpu",
            known_limitations=[
                "Trained across 20 generative models (ProGAN, StyleGAN, BigGAN, CycleGAN).",
                "Currently UNAVAILABLE: requires local download of ResNet50 checkpoint (102MB) and PyTorch."
            ],
            description="Detects universal CNN fingerprints left by generative upsampling layers across diverse architectures.",
            inference_callable=None
        )

    def get_registered_models(self) -> List[Dict[str, Any]]:
        return [m.to_dict() for m in self.models.values()]

    def get_model(self, model_id: str) -> Optional[RegisteredModel]:
        return self.models.get(model_id)

    def execute_inference(
        self,
        model_id: str,
        image_np: np.ndarray,
        mime_type: str,
        metadata: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Executes real inference if model is available, or returns explicit unavailable status.
        Never fakes execution or manufactures arbitrary confidence percentages.
        """
        model = self.models.get(model_id)
        if not model:
            return {
                "model_id": model_id,
                "status": ModelStatus.INFERENCE_FAILED,
                "error": f"Model '{model_id}' is not registered in TruthNet ModelRegistry."
            }

        # Check supported formats
        if mime_type and model.supported_formats and mime_type not in model.supported_formats:
            return {
                "model_id": model_id,
                "model_name": model.name,
                "status": ModelStatus.UNSUPPORTED_INPUT,
                "error": f"Input format '{mime_type}' is unsupported. Supported: {model.supported_formats}"
            }

        # Check dependency and checkpoint availability
        if not model.dependency_available:
            return {
                "model_id": model_id,
                "model_name": model.name,
                "status": ModelStatus.DEPENDENCY_UNAVAILABLE,
                "reason": f"Required runtime dependency '{model.dependency_name}' is not installed in the host environment.",
                "prerequisites": f"Install {model.dependency_name} in Python environment."
            }

        if not model.checkpoint_available:
            return {
                "model_id": model_id,
                "model_name": model.name,
                "status": ModelStatus.MODEL_CHECKPOINT_UNAVAILABLE,
                "reason": f"Model weights checkpoint '{model.checkpoint_name}' is not packaged locally.",
                "prerequisites": f"Download checkpoint {model.checkpoint_name} into data/models/."
            }

        if not model.inference_callable:
            return {
                "model_id": model_id,
                "model_name": model.name,
                "status": ModelStatus.MODEL_CHECKPOINT_UNAVAILABLE,
                "reason": "Inference handler is not implemented for this model architecture.",
                "prerequisites": "Deploy trained ONNX or C++ model provider."
            }

        # Execute real inference
        try:
            result = model.inference_callable(image_np, metadata)
            result["model_id"] = model.model_id
            result["model_name"] = model.name
            result["version"] = model.version
            result["runtime_device"] = model.runtime_device
            result["status"] = ModelStatus.INFERENCE_EXECUTED
            result["evaluation_limitations"] = model.known_limitations
            return result
        except Exception as e:
            logger.error(f"Inference error executing model '{model_id}': {e}", exc_info=True)
            return {
                "model_id": model_id,
                "model_name": model.name,
                "status": ModelStatus.INFERENCE_FAILED,
                "error": str(e),
                "evaluation_limitations": model.known_limitations
            }


model_registry = ModelRegistry()

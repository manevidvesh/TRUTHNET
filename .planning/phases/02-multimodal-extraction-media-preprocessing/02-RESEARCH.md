# Phase 2: Multimodal Extraction & Media Preprocessing - Research

**Researched:** 2026-11-13
**Domain:** Multimodal media processing, EXIF metadata, OpenCV keyframe extraction, PyAV demuxing, Windows Media OCR, speech transcription
**Confidence:** HIGH

<user_constraints>
## User Constraints (from CONTEXT.md & User Refinements)

### Locked Decisions
- **D-201:** Dual-Engine OCR Adapter: `Windows.Media.Ocr` (`winocr`) as primary Windows-native operational engine, with `TesseractEngine` adapter fallback. Real capability detection with honest `UNAVAILABLE` status when uninstalled. Zero fabricated text.
- **D-202:** Transcription Engine Adapter: `faster-whisper` (CTranslate2, CPU-optimized). Time-aligned transcript segments when checkpoints exist; explicit `UNAVAILABLE` diagnostic when missing.
- **D-203:** Boundary-anchored keyframe extraction: First decodable frame (0ms), last decodable frame, and uniform intermediate intervals (capped at 15 max).
- **D-204:** EXIF preservation: Raw verbatim EXIF + normalized values + explicit `malformed_fields`. Naive timestamps never assumed UTC (`timezone_detected: False`). EXIF marked as unverified observed metadata.
- **D-205:** Versioned Extraction Records: `ExtractionRecord` model with `version: int` and `is_active: bool`. Independent modality statuses.
- **D-206:** PyAV audio demuxing: Detect audio in video containers, extract to derived WAV, link to transcription. Audio extraction failure isolated from video extraction.
- **D-207:** Derived Artifact Security: Stored under `data/derived/{evidence_id}/`, indexed in `DerivedArtifact` with SHA-256 hashes, zero absolute paths exposed in API, stream via authorized retrieval endpoints.
</user_constraints>

<research_summary>
## Summary

Phase 2 implements technical extraction and media preprocessing across image, audio, and video modalities.

For image processing, Pillow (`PIL.Image`) provides direct access to dimensions, format, mode, and decoded EXIF tags. Pillow's `_getexif()` and `ExifTags` allow extracting camera make, model, software, and original timestamps without third-party C binaries. GPS IFD tags are parsed into decimal degrees if present. Any non-standard or malformed tags are safely isolated.

For video processing and container analysis, PyAV (`av`) embeds FFmpeg libraries directly in Python wheels, enabling reliable demuxing of video containers, detection of audio streams (`container.streams.audio`), and extraction of audio packets to 16kHz WAV format. OpenCV (`cv2.VideoCapture`) performs fast frame decoding and seeking for keyframe extraction.

For OCR on Windows, `winocr` provides direct access to the built-in Windows 10/11 `Windows.Media.Ocr.OcrEngine`, eliminating external Tesseract binary installation requirements while delivering hardware-accelerated text recognition. A companion Tesseract adapter is provided for environments with `tesseract.exe`.

For speech-to-text, `faster-whisper` utilizes CTranslate2 for quantized, fast CPU execution. If model checkpoints are present, it produces time-aligned segments; if checkpoints are not downloaded, the engine honestly returns `UNAVAILABLE` with clear diagnostic instructions.
</research_summary>

<standard_stack>
## Standard Stack

### Core
| Library | Version | Purpose | Why Standard |
|---------|---------|---------|--------------|
| `pillow` | >=12.2.0 | Image manipulation & EXIF parsing | Universal Python image library |
| `opencv-python` | >=5.0.0 | Video frame decoding & seeking | Fast C++ video capture and frame processing |
| `av` (PyAV) | >=19.0.0 | Media container demuxing & audio extraction | Embedded FFmpeg bindings without system binary requirements |
| `mutagen` | >=1.48.0 | Pure Python audio metadata extraction | Comprehensive format coverage (mp3, wav, flac, ogg, m4a) |
| `winocr` | >=0.0.15 | Native Windows 10/11 OCR engine | Zero-dependency local OCR on Windows systems |

### Supporting / Optional
| Library | Version | Purpose | When to Use |
|---------|---------|---------|-------------|
| `faster-whisper` | >=1.2.0 | High-speed CPU speech-to-text | Local transcription when model weights are provided |
| `pytesseract` | >=0.3.10 | Tesseract OCR Python bridge | When external `tesseract.exe` is present on PATH |

**Installation:**
`pillow`, `opencv-python`, `av`, `mutagen`, and `winocr` are already installed in the Python environment!
</standard_stack>

<architecture_patterns>
## Architecture Patterns

### Versioned Extraction & Derived Artifact Relationship
```
EvidenceSubmission (Investigation Context)
   │
   ├──► ExtractionRecord (Version 1, is_active=True)
   │       ├── category: "OBSERVED_DATA"
   │       ├── technical_metadata: { dimensions, codecs, raw_exif, normalized_exif }
   │       ├── ocr_result: { status: "EXECUTED", text: "...", engine: "Windows.Media.Ocr" }
   │       ├── transcription_result: { status: "UNAVAILABLE", reason: "..." }
   │       ├── video_frames: [ { frame_index, timestamp_ms, artifact_id } ]
   │       └── modality_statuses: { metadata: "COMPLETED", frames: "COMPLETED", ocr: "COMPLETED", transcription: "UNAVAILABLE" }
   │
   └──► DerivedArtifacts (Stored in data/derived/{evidence_id}/)
           ├── [Artifact 1: KEYFRAME] frame_0_0ms.jpg (SHA-256: 3c4d...)
           ├── [Artifact 2: KEYFRAME] frame_1_1000ms.jpg (SHA-256: 7e8f...)
           └── [Artifact 3: EXTRACTED_AUDIO] audio.wav (SHA-256: 9a0b...)
```
</architecture_patterns>

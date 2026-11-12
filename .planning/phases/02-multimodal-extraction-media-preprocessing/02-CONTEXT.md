# Phase 2: Multimodal Extraction & Media Preprocessing - Context

**Gathered:** 2026-11-13
**Status:** Ready for planning

<domain>
## Phase Boundary

Phase 2 delivers multimodal extraction and technical preprocessing across image, audio, and video evidence. It establishes versioned extraction records, derived artifact storage and security, normalized and raw technical metadata (EXIF/GPS/codecs/duration/sample rate), boundary-anchored video keyframe extraction (including first and last frames), video audio stream detection and demuxing, and dual-engine OCR (native Windows Media OCR and Tesseract adapter) with independent failure isolation across modalities. All extracted data is registered strictly as "Observed Data" distinct from model inferences or unverified user assertions.

</domain>

<decisions>
## Implementation Decisions

### 1. OCR & Speech Transcription Architecture
- **D-201:** Dual-Engine OCR Adapter: Implement native `Windows.Media.Ocr` (`winocr`) as primary Windows-native operational engine (zero external binary dependency), plus `TesseractEngine` adapter inspecting host PATH. Genuine capability detection records operational status (`EXECUTED` vs `UNAVAILABLE`) with diagnostic explanations. No fabricated text is ever returned. — **Reversibility:** reversible
- **D-202:** Transcription Engine Adapter: Implement local speech-to-text pipeline using `faster-whisper` (CTranslate2, CPU-optimized, ~4x faster than PyTorch Whisper). If model checkpoints are present, executes time-aligned transcript segments; if absent, records explicit `UNAVAILABLE` status without blocking evidence ingestion. — **Reversibility:** reversible

### 2. Video Keyframe Extraction & Boundary Anchoring
- **D-203:** Boundary-anchored keyframe extraction: Always extract the first decodable frame (timestamp 0ms), the last decodable frame, and configurable uniform intermediate intervals (capped at 15 frames max). Every frame records index, exact millisecond timestamp, SHA-256 hash, and sampling strategy. Frame extraction explicitly disclaims exhaustive video authenticity verification. — **Reversibility:** reversible

### 3. EXIF & Technical Metadata Integrity
- **D-204:** EXIF preservation and timezone discipline: Store raw EXIF dictionaries verbatim alongside normalized values. Missing, malformed, or unparseable fields are explicitly cataloged in `malformed_fields`. Naive timestamps are NEVER assumed to be UTC (`timezone_detected: False`, `timezone_confidence: "UNSPECIFIED_LOCAL"`). EXIF data is documented as unauthenticated observed metadata, not proof of capture truth. — **Reversibility:** costly

### 4. Versioned Extraction Records & Provenance
- **D-205:** Versioned Extraction Records: New `ExtractionRecord` model with `version: int` and `is_active: bool`. Re-running extractors increments version numbers and preserves prior records for auditability. Each modality (`metadata`, `frames`, `ocr`, `transcription`) reports an independent extraction status. — **Reversibility:** one-way — Database schema design.

### 5. Video Audio Demuxing & Stream Processing
- **D-206:** PyAV (embedded FFmpeg) audio demuxing: Detect audio streams in video containers. If audio exists, demux to derived WAV format (`data/derived/{evidence_id}/audio.wav`) and pass to transcription. Audio extraction failure does not abort video frame or metadata extraction. — **Reversibility:** reversible

### 6. Derived Artifact Security & Provenance
- **D-207:** Storage isolation & URL abstraction: Derived artifacts (frames, demuxed audio) are stored in `data/derived/{evidence_id}/` distinct from `data/uploads/`. All derived artifacts are indexed in `DerivedArtifact` with SHA-256 hashes and parent evidence IDs. Absolute file paths are NEVER exposed via API responses; authorized content retrieval is routed through `/api/v1/investigations/{id}/evidence/{evidence_id}/artifacts/{artifact_id}/content`. — **Reversibility:** costly

</decisions>

<canonical_refs>
## Canonical References

### Project Specifications
- `.planning/PROJECT.md` — Non-negotiable principles (no fabricated predictions, 5-category distinction, honest capability reporting).
- `.planning/REQUIREMENTS.md` — EXTR-01 through EXTR-05 definitions.
- `.planning/ROADMAP.md` — Phase 2 scope and success criteria.

### Phase 1 Baselines
- `backend/app/models/evidence.py` — Existing `MediaAsset` and `EvidenceSubmission` models.
- `backend/app/core/storage.py` — Storage manager and path resolution.
- `backend/app/services/pipeline.py` — Asynchronous processing pipeline.
</canonical_refs>

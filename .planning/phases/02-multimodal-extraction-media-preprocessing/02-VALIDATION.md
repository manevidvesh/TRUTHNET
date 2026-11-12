---
phase: "02"
slug: "multimodal-extraction-media-preprocessing"
status: draft
nyquist_compliant: true
wave_0_complete: false
created: "2026-11-13"
---

# Phase 02 — Validation Strategy

> Per-phase validation contract for feedback sampling during Phase 2 execution.

---

## Test Infrastructure

| Property | Value |
|----------|-------|
| **Framework** | pytest 8.x + pytest-asyncio |
| **Config file** | `backend/pytest.ini` |
| **Quick run command** | `pytest backend/tests/test_extraction_metadata.py` |
| **Full suite command** | `pytest backend/tests/` |
| **Estimated runtime** | ~6 seconds |

---

## Sampling Rate

- **After every task commit:** Run quick run command
- **After every plan wave:** Run full suite command
- **Before `/gsd-verify-work`:** Full suite must be green
- **Max feedback latency:** 10 seconds

---

## Per-Task Verification Map

| Task ID | Plan | Wave | Requirement | Secure Behavior | Test Type | Automated Command | File Exists | Status |
|---------|------|------|-------------|-----------------|-----------|-------------------|-------------|--------|
| 02-01-01 | 01 | 1 | EXTR-01, EXTR-05 | No timezone assumption, raw EXIF kept | unit/integration | `pytest backend/tests/test_extraction_metadata.py` | ❌ W0 | ⬜ pending |
| 02-02-01 | 02 | 2 | EXTR-04, EXTR-05 | Boundary frames (first/last), derived artifact path isolation | integration | `pytest backend/tests/test_video_keyframes.py` | ❌ W0 | ⬜ pending |
| 02-03-01 | 03 | 2 | EXTR-02, EXTR-03, EXTR-05 | Real capability detection, zero fake OCR/transcript | integration | `pytest backend/tests/test_ocr_transcription.py` | ❌ W0 | ⬜ pending |
| 02-03-02 | 03 | 3 | EXTR-01..05 | Full end-to-end regression without Phase 1 impact | e2e | `pytest backend/tests/test_phase2_e2e.py` | ❌ W0 | ⬜ pending |

*Status: ⬜ pending · ✅ green · ❌ red · ⚠️ flaky*

---

## Wave 0 Requirements

- [ ] Sample test image with synthetic EXIF and GPS tags
- [ ] Sample synthetic video file with video stream and audio stream (created via PyAV/OpenCV)
- [ ] Sample synthetic video file without audio stream
- [ ] Sample synthetic audio WAV file
- [ ] Sample image with rendered text for OCR validation

---

## Validation Sign-Off

- [x] All tasks have automated verify commands
- [x] Sampling continuity: no 3 consecutive tasks without automated verify
- [x] Derived artifact security tests included
- [x] EXIF timezone uncertainty tests included
- [x] `nyquist_compliant: true` set in frontmatter

**Approval:** approved 2026-11-13

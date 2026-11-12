---
phase: "03"
slug: "persistent-historical-media-indexing-perceptual-hashing"
status: draft
nyquist_compliant: true
wave_0_complete: false
created: "2026-11-13"
---

# Phase 03 — Validation Strategy (Revised)

> Per-phase validation contract for feedback sampling during Phase 3 execution.

---

## Test Infrastructure

| Property | Value |
|---|---|
| **Framework** | pytest 8.x + pytest-asyncio |
| **Config file** | `backend/pyproject.toml` |
| **Quick run command** | `pytest backend/tests/test_fingerprint_indexing.py` |
| **Full suite command** | `pytest backend/tests/` |
| **Estimated runtime** | ~12 seconds |

---

## Per-Task Verification Map

| Task ID | Plan | Wave | Requirement | Secure Behavior | Test Type | Automated Command | File Exists | Status |
|---|---|---|---|---|---|---|---|---|
| 03-01-01 | 01 | 1 | HIST-01, HIST-02 | SQLite persistence of media and frame fingerprints, deterministic preprocessing, descriptor store security | unit/integration | `pytest backend/tests/test_fingerprint_indexing.py` | ❌ W0 | ⬜ pending |
| 03-02-01 | 02 | 2 | HIST-03, HIST-04 | 6 classifications, raw metrics, RANSAC homography, candidate retrieval telemetry | integration | `pytest backend/tests/test_geometric_matching.py` | ❌ W0 | ⬜ pending |
| 03-03-01 | 03 | 3 | HIST-05, HIST-06 | Cross-investigation privacy proof, multi-frame video boundaries, transformation benchmark suite | e2e | `pytest backend/tests/test_historical_matcher.py backend/tests/test_phase3_e2e.py` | ❌ W0 | ⬜ pending |

---

## Validation Sign-Off

- [x] All tasks have automated verify commands
- [x] False-positive and false-negative transformation evaluations specified across 12 distinct variations
- [x] Epistemological disclaimer verification included
- [x] Cross-investigation privacy checks included
- [x] `nyquist_compliant: true` set in frontmatter

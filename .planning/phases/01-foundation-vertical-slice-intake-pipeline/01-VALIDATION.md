---
phase: "01"
slug: "foundation-vertical-slice-intake-pipeline"
status: draft
nyquist_compliant: true
wave_0_complete: false
created: "2026-11-13"
---

# Phase 01 — Validation Strategy

> Per-phase validation contract for feedback sampling during execution.

---

## Test Infrastructure

| Property | Value |
|----------|-------|
| **Framework** | pytest 8.x + pytest-asyncio |
| **Config file** | `backend/pytest.ini` |
| **Quick run command** | `pytest backend/tests/test_investigations.py` |
| **Full suite command** | `pytest backend/tests/` |
| **Estimated runtime** | ~5 seconds |

---

## Sampling Rate

- **After every task commit:** Run quick run command
- **After every plan wave:** Run full suite command
- **Before `/gsd-verify-work`:** Full suite must be green
- **Max feedback latency:** 10 seconds

---

## Per-Task Verification Map

| Task ID | Plan | Wave | Requirement | Threat Ref | Secure Behavior | Test Type | Automated Command | File Exists | Status |
|---------|------|------|-------------|------------|-----------------|-----------|-------------------|-------------|--------|
| 01-01-01 | 01 | 1 | INTK-01 | T-01-01 | Input sanitization, valid status enum | unit/integration | `pytest backend/tests/test_investigations.py` | ❌ W0 | ⬜ pending |
| 01-02-01 | 02 | 1 | INTK-02, INTK-03 | T-01-02 | File path traversal prevention, streaming hash | integration | `pytest backend/tests/test_evidence_intake.py` | ❌ W0 | ⬜ pending |
| 01-02-02 | 02 | 1 | INTK-04 | T-01-03 | Separate claimed metadata from observed data | unit | `pytest backend/tests/test_evidence_metadata.py` | ❌ W0 | ⬜ pending |
| 01-03-01 | 03 | 2 | INTK-05 | T-01-04 | Fault isolation on corrupt file/URL | integration | `pytest backend/tests/test_fault_isolation.py` | ❌ W0 | ⬜ pending |

*Status: ⬜ pending · ✅ green · ❌ red · ⚠️ flaky*

---

## Wave 0 Requirements

- [ ] `backend/pytest.ini` — test runner configuration
- [ ] `backend/tests/conftest.py` — shared async test client and temporary database fixtures
- [ ] `pytest`, `pytest-asyncio`, `httpx` installed in Python environment

---

## Manual-Only Verifications

| Behavior | Requirement | Why Manual | Test Instructions |
|----------|-------------|------------|-------------------|
| OpenAPI Docs UI Interactive Inspection | INTK-01, INTK-02 | Visual verification of Swagger UI | Open `http://localhost:8000/docs` in browser and test `/api/v1/investigations` |

---

## Validation Sign-Off

- [x] All tasks have `<automated>` verify or Wave 0 dependencies
- [x] Sampling continuity: no 3 consecutive tasks without automated verify
- [x] Wave 0 covers all test harness files
- [x] No watch-mode flags
- [x] Feedback latency < 10s
- [x] `nyquist_compliant: true` set in frontmatter

**Approval:** approved 2026-11-13

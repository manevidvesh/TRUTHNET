# Phase 4 Validation & Verification Strategy

## 1. Test Suite Architecture

Phase 4 testing will be implemented across four dedicated test suites guaranteeing zero regressions on existing Phase 1-3 capabilities:

1. **`backend/tests/test_claim_extraction.py`**:
   - Tests claim proposition extraction from raw text, OCR text, and Whisper transcripts.
   - Tests entity extraction (entities, alleged dates, locations, numbers).
   - Tests multilingual verbatim preservation across English, Hindi, and Telugu.
   - Tests rejection of non-factual opinion text and empty inputs.

2. **`backend/tests/test_contextual_verification.py`**:
   - Tests explicit temporal contradiction detection (photo captured in 2018, claimed in 2026 -> `HISTORICAL_CONTEXT_CONFLICT`).
   - Tests spatial Haversine distance conflict detection (claimed location Paris, EXIF GPS in Tokyo -> `HISTORICAL_CONTEXT_CONFLICT`).
   - Tests legitimate archival reuse recognition (accurate historical attribution -> `LEGITIMATE_ARCHIVAL_REUSE`).
   - Tests missing context handling (photo lacks capture timestamp -> `INSUFFICIENT_CONTEXT`).

3. **`backend/tests/test_source_independence.py`**:
   - Tests syndicated wire service republication detection (10 articles citing PTI wire are grouped into 1 independent source cluster).
   - Tests genuine independent corroboration (two distinct investigative outlets with independent bylines and disparate text -> 2 independent sources).
   - Tests single-source origin tracking (multiple blogs repeating an unverified tweet).
   - Tests passage-level snippet extraction and canonical URL preservation.

4. **`backend/tests/test_phase4_e2e_lineage.py`**:
   - E2E Test 1: Complete claim verification pipeline (Extraction -> Retrieval -> Contextual Diff -> Lineage Graph -> Explainable Verdict).
   - E2E Test 2: Invariant verification:
     - Manipulated image with true claim text -> Verdict isolates media manipulation from claim truth.
     - Authentic historical image with recycled caption -> Verdict flags `MISLEADING_CONTEXT`, not manipulated media.
   - E2E Test 3: Explicit abstention on insufficient or conflicting evidence -> Produces `INSUFFICIENT_EVIDENCE` or `CONFLICTING_EVIDENCE` with open questions.
   - Full regression suite execution across all 45 existing tests + Phase 4 tests.

---

## 2. PS-11 Demonstration Scenarios Addressed in Phase 4

Phase 4 directly enables and validates 3 of the 5 official PS-11 demonstration scenarios:
- **Scenario A (Historical Contextual Conflict)**: Genuine archival video from a 2019 flood circulated in 2026 claiming to depict a current disaster. Engine discovers historical match, calculates $\Delta t = -2,500\text{ days}$, detects context conflict, and flags misleading recycling.
- **Scenario B (Legitimate Archival Reuse)**: News retrospective accurately referencing a 2015 historical photograph. Engine recognizes archival framing keywords, labels as `LEGITIMATE_ARCHIVAL_REUSE`, and avoids false-positive accusation.
- **Scenario C (Claim Verification & Abstention)**: Uncorroborated viral claim lacking independent primary sources or fact-checks. Engine explicitly abstains with `INSUFFICIENT_EVIDENCE` and lists what investigators must verify next.

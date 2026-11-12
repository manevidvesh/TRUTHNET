# Phase 4 Context: Claim Intelligence, Contextual Verification & Source Independence Engine

## 1. Executive Summary & PS-11 Alignment

In accordance with Problem Statement PS-11 (YUKTIK-2026: Real-Time Multimodal Deepfake Detection and Coordinated Misinformation Intelligence Platform), **Phase 4 transitions TRUTHNET AI from a media indexing utility into a full-fledged investigative intelligence workbench.**

The central design principle of TRUTHNET governs this phase:
> **AI identifies signals. Evidence establishes context. The system explains relationships. Investigators make decisions.**

A core failure mode of naive misinformation tools is conflating media manipulation with claim falsity, or assuming an authentic image proves a caption true. Phase 4 mathematically and logically enforces the core epistemological invariants:
1. **A manipulated image does NOT automatically make its associated claim false.** (e.g. an authentic speech accompanied by a synthetically saturated or cropped photograph).
2. **An authentic image does NOT automatically make its associated caption true.** (e.g. a genuine 2015 earthquake photograph repurposed with a false 2026 caption).
3. **A historical media match does NOT automatically establish malicious misattribution.** (e.g. legitimate archival reuse by historical documentaries or news retrospectives).

---

## 2. Core Capabilities Delivered in Phase 4

### A. Factual Claim Extraction & Normalization (CLAM-01 to CLAM-05)
- Extracts atomic factual propositions from submitted text, captions, OCR text, and speech transcripts.
- Extracts named entities (persons, organizations, geopolitical entities), alleged dates, locations, and numerical assertions.
- Normalizes claims into canonical predicate representations while strictly preserving verbatim original text and language.
- Explicit multilingual tracking for English, Hindi, and Telugu.

### B. Historical vs. Current Contextual Verification Engine (CONT-01 to CONT-05)
- Automated comparison diffing newly claimed context (`claimed_event`, `claimed_date`, `claimed_location`, caption attribution) against:
  1. Technical observed EXIF metadata and GPS coordinates extracted in Phase 2.
  2. Prior historical `EvidenceSubmission`s linked to the same `MediaAsset` indexed in Phase 3.
  3. External primary source publication records.
- Classifications:
  - `HISTORICAL_CONTEXT_CONFLICT`: Explicit contradiction (e.g. capture date predating claimed event date).
  - `LEGITIMATE_ARCHIVAL_REUSE`: Valid historical retrospective or archival citation without deception.
  - `CONSISTENT_CONTEXT`: Newly claimed context aligns with historical provenance.
  - `INSUFFICIENT_CONTEXT`: Inadequate historical data to confirm or refute.
- Computes exact temporal deltas ($\Delta t$ in days) and spatial distances ($d$ in km via Haversine formula).

### C. Retrieval-First Evidence Discovery & Source Independence (RETR-01 to RETR-05)
- Searches public fact-check records (ClaimReview schema) and authoritative primary sources.
- Preserves passage-level text snippets, canonical URLs, publication timestamps, and author bylines.
- **Source Independence Analysis**: Distinguishes wire service syndication chains (e.g., 15 news websites reprinting the identical PTI/Reuters/ANI dispatch) from genuinely independent corroborating investigations.
- Explicit abstention when evidence is missing or ambiguous.

### D. Claim Lineage Graph & Explainable Assessment Engine (LINE-01 to LINE-05)
- Builds an auditable NetworkX directed graph linking `Investigation`, `EvidenceSubmission`, `MediaAsset`, `Claim`, `Source`, and `Account`.
- Assigns explicit relationship types: `SUPPORTS`, `CONTRADICTS`, `SAME_CLAIM`, `CLAIM_VARIANT`, `HISTORICAL_CONTEXT_CONFLICT`, `REPEATS_SOURCE`.
- Every relationship cites its underlying evidence ID, method, timestamp, and observed vs. inferred status.
- Synthesizes findings into explainable verdicts: `VERIFIED_TRUE`, `VERIFIED_FALSE`, `MISLEADING_CONTEXT`, `MANIPULATED_MEDIA_USED`, `INSUFFICIENT_EVIDENCE`, `CONFLICTING_EVIDENCE`.

---

## 3. Preserved Phase 3 Limitations

Phase 4 preserves all Phase 3 engineering and security constraints:
1. The historical perceptual index is recognized as an $O(N)$ linear baseline ($2.46\text{ms}$ at 100 assets, $12.82\text{ms}$ at 1,000 assets, $192.79\text{ms}$ at 10,000 assets).
2. The 22-scenario adversarial benchmark is treated as a handcrafted test suite, not a universal guarantee.
3. Cross-investigation privacy isolation is strictly maintained (`GLOBAL_INDEX_ANONYMIZED` scrubs all foreign titles, notes, investigator names, and internal paths).

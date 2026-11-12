# Phase 4 Context: Claim Intelligence, Contextual Verification & Source Independence Engine

## 1. Executive Summary & PS-11 Alignment

In accordance with Problem Statement PS-11 (YUKTIK-2026: Real-Time Multimodal Deepfake Detection and Coordinated Misinformation Intelligence Platform), **Phase 4 transitions TRUTHNET AI from a media indexing utility into a full-fledged investigative intelligence workbench.**

The central design principle of TRUTHNET governs this phase:
> **AI identifies signals. Evidence establishes context. The system explains relationships. Investigators make decisions.**

A core failure mode of naive automated verification systems is conflating media manipulation with claim falsity, or assuming that an authentic image proves a text caption true. Phase 4 mathematically and logically enforces five core epistemological invariants:

1. **A manipulated image does NOT automatically make its associated claim false.**
   *(e.g., an authentic political speech accompanied by a cropped, re-saturated, or synthetic illustration).*
2. **An authentic image does NOT automatically make its associated caption true.**
   *(e.g., a genuine 2015 earthquake photograph repurposed with a false 2026 breaking news caption).*
3. **A historical media match does NOT automatically establish malicious misattribution.**
   *(e.g., legitimate archival reuse by historical documentaries, museum archives, or news retrospectives).*
4. **Old or geographically shifted media does NOT automatically make the underlying claim false.**
   *(Media context discrepancy is an observational evidence signal of potential media recycling or caption mismatch, not mathematical proof that the underlying factual proposition never occurred).*
5. **Source independence is an evidence-quality dimension, not a truth formula.**
   *(Counting 15 republications of the same wire dispatch as 15 independent corroborations is an epistemological error. Conversely, a claim with 2 independent sources is not mathematically guaranteed true).*

TRUTHNET does NOT issue absolute declarations of universal truth (`VERIFIED_TRUE` / `VERIFIED_FALSE`). Instead, the platform synthesizes observable multimodal evidence into **structured evidence assessments**:
- `SUPPORTED`: Documented evidence from independent, corroborated primary sources or authoritative fact-checks aligns with the claim.
- `CONTRADICTED`: Corroborated factual evidence or authoritative debunking directly refutes the claim assertions.
- `MISLEADING_CONTEXT`: The underlying media or event is authentic, but framed with conflicting dates, locations, entities, or narratives.
- `INSUFFICIENT_EVIDENCE`: Available sources and archives provide inadequate evidence to corroborate or refute; system explicitly abstains and poses investigative questions.
- `CONFLICTING_EVIDENCE`: Distinct credible sources report irreconcilable or mutually contradictory accounts; system flags the conflict for human review.
- `UNVERIFIED`: Breaking claim with zero verified external records; system presents what is known without speculation.

---

## 2. Core Capabilities Delivered in Phase 4

### A. Hybrid Factual Claim Extraction & Normalization (CLAM-01 to CLAM-05)
- Extracts atomic factual propositions from submitted captions, raw text, OCR extractions, and speech transcripts.
- Implements a hybrid extraction pipeline:
  - Deterministic segmentation and preprocessing.
  - Entity, temporal expression, location, quantity, and attribution parsing.
  - Atomic claim decomposition into structured Subject-Predicate-Object (SPO) propositions with qualifiers.
  - Verbatim original text preservation with **evidence-span character offsets** (`start_char`, `end_char`) directly linking claims to source text.
  - Explicit handling and filtering of non-factual statements (rhetorical questions, subjective opinions, emotional commentary).
  - Explicit distinction between deterministic parsing and semantic model inference, with bounded fallbacks when external LLMs are unavailable.
- Real statistical language detection (`en`, `hi`, `te`) preserving detector-supplied confidence, detection method, and translation provenance.

### B. Historical vs. Current Contextual Verification Engine (CONT-01 to CONT-05)
- Evaluates newly claimed context (`claimed_event`, `claimed_date`, `claimed_location`, caption framing) against observed technical evidence:
  1. Technical observed EXIF metadata and GPS coordinates extracted in Phase 2.
  2. Prior historical `EvidenceSubmission`s linked to the same `MediaAsset` indexed in Phase 3.
  3. External primary source publication records.
- Treats temporal deltas ($\Delta t$ in days) and spatial distances ($d$ in km via Haversine geodesic formula) as **quantitative evidence signals**, not rigid binary truth arbiters.
- Preserves explicit date provenance taxonomy:
  - `capture_date`: Camera hardware sensor timestamp (treated as potentially editable/unverified).
  - `publication_date`: Dissemination timestamp from news or web metadata.
  - `archive_date`: Snapshot date from web archives or fact-check records.
  - `submission_date`: Timestamp when intake occurred in TRUTHNET.
  - `truthnet_observation_date`: System indexing timestamp.
- Treats GPS metadata as camera location (not proof of event location) and city centroids as reference points (not event evidence).
- Produces conservative contextual classifications:
  - `HISTORICAL_CONTEXT_CONFLICT`: Demonstrable temporal or geographic discrepancy with historical provenance.
  - `POSSIBLE_CONTEXT_MISMATCH`: Potential inconsistency requiring corroboration.
  - `CONSISTENT_CONTEXT`: Contextual assertions align with recorded historical facts.
  - `LEGITIMATE_ARCHIVAL_REUSE`: Contextual signals indicate transparent historical or retrospective reference.
  - `INSUFFICIENT_CONTEXT`: Inadequate metadata to confirm or refute.
  - `CONFLICTING_CONTEXT_EVIDENCE`: Discrepant metadata across multiple historical records.

### C. Multi-Signal Retrieval & Source Independence Engine (RETR-01 to RETR-05)
- Retrieval-first evidence discovery querying:
  1. Curated local ClaimReview JSON-LD archive with verifiable provenance and license adherence.
  2. Google Fact Check Tools API (when configured with API key).
  3. Web retrieval engine with strict Phase 1 SSRF protections (blocking loopback, RFC 1918 private ranges, AWS/cloud metadata, DNS rebinding, redirect re-validation).
- Preserves passage-level evidence snippets ($\le 500$ chars), canonical URLs, publication timestamps, and author bylines.
- Multi-signal source dependency analysis evaluating four orthogonal independence dimensions:
  1. `publisher_independence`: Corporate and organizational separation.
  2. `reporting_independence`: Independent investigative reporting vs syndicated wire republishing.
  3. `evidence_independence`: Distinct physical/documentary evidence vs common press release.
  4. `source_of_origin_independence`: Separate eyewitnesses vs citing a single viral post.
- Explicitly flags uncertain dependencies as `UNRESOLVED_DEPENDENCY` rather than forcing inaccurate clusters.
- Honest provider availability reporting: returns `PROVIDER_UNAVAILABLE` or `OFFLINE` when disconnected; never hallucinates or fabricates search results.

### D. Claim Lineage Graph & Explainable Assessment Engine (LINE-01 to LINE-05)
- Builds an auditable NetworkX directed graph linking `Investigation`, `EvidenceSubmission`, `MediaAsset`, `Claim`, `RetrievedSource`, and `Account`.
- Strictly distinguishes **observed** edges (direct metadata, verbatim quotes, cryptographic hashes) from **inferred** edges (predicate extraction, text similarity, hypothesized republication chains).
- Every inferred relationship retains its underlying evidence ID, method, and explanatory rationale.
- Assigns explicit relationship types: `SUPPORTS`, `CONTRADICTS`, `SAME_CLAIM`, `CLAIM_VARIANT`, `HISTORICAL_CONTEXT_CONFLICT`, `REPEATS_SOURCE`.
- Synthesizes findings into evidence assessments (`SUPPORTED`, `CONTRADICTED`, `MISLEADING_CONTEXT`, `INSUFFICIENT_EVIDENCE`, `CONFLICTING_EVIDENCE`, `UNVERIFIED`).
- Decouples media authenticity from claim veracity (`MANIPULATED_MEDIA_USED` is an orthogonal signal).
- Compiles transparent assessment rationales, known limitations, and unresolved questions for human investigators.
- Tracks human review lifecycle (`PENDING_REVIEW`, `INVESTIGATOR_CONFIRMED`, `INVESTIGATOR_OVERRIDDEN`).

---

## 3. Preserved Phase 3 Foundations & System Limits

Phase 4 preserves all Phase 1–3 engineering, storage, and security guarantees:
1. **Database & Storage Compatibility**: SQLite with WAL mode. All Phase 4 tables (`claims`, `context_comparisons`, `retrieved_sources`, `source_independence_clusters`, `claim_relationships`, `claim_assessments`) are strictly additive. Foreign keys enforce referential integrity with explicit cascade policies.
2. **Local-First Reliability**: System operates fully offline using the local ClaimReview archive and deterministic rule engines. External APIs (Google Fact Check, Web Retrieval) are optional enhancements.
3. **Cross-Investigation Privacy**: The `GLOBAL_INDEX_ANONYMIZED` privacy boundary established in Phase 3 is strictly preserved. Global matching never leaks foreign investigation IDs, investigator notes, or local file paths.
4. **Epistemological Humility**: The platform provides evidence and structured explanations; investigators make the final determination.

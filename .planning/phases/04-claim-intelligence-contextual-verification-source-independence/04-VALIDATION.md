# Phase 4 Validation & Adversarial Verification Strategy

## 1. Test Suite Architecture

Phase 4 testing is implemented across four dedicated test suites with adversarial edge cases, zero fabricated assertions, and strict regression guarantees:

```
backend/tests/
├── test_claim_extraction.py          # Wave 1: Hybrid claim extraction, entities, spans, languages
├── test_contextual_verification.py   # Wave 2: Spatial-temporal evidence signals, date taxonomy, archival reuse
├── test_source_independence.py       # Wave 3: Multi-signal independence (4 dimensions), SSRF, ClaimReview
└── test_phase4_e2e_lineage.py        # Wave 4: End-to-end lineage graph, non-conflation invariants, assessments
```

---

## 2. Detailed Test Specifications by Test Suite

### A. `test_claim_extraction.py` (Adversarial Claim & Language Tests)
1. **Multiple Claims in One Paragraph**:
   - Paragraph containing three distinct assertions ("The bridge collapsed on Tuesday. Government announced 10 crore relief. Opposition demanded resignation.").
   - Asserts extraction yields 3 atomic `ClaimRecord`s with discrete character span offsets `[start_char, end_char]`.
2. **Negation Disambiguation**:
   - Compares positive assertion ("Health Ministry approved the vaccine") with negated assertion ("Health Ministry did not approve the vaccine").
   - Verifies predicate negation is explicitly captured in the predicate/qualifier structure and normalized claim.
3. **Attribution vs. Direct Assertion**:
   - Parses "Spokesperson X alleged that Company Y engaged in fraud".
   - Verifies attribution entity (`Spokesperson X`) is separated from the underlying proposition (`Company Y engaged in fraud`).
4. **Causal Assertions**:
   - Parses "Flooding in District Z was caused by the upstream dam opening".
   - Asserts subject, predicate, object, and causal relation are represented.
5. **Ambiguous & Relative Dates**:
   - Tests relative phrases ("last Friday", "earlier today", "two weeks ago") alongside explicit ISO dates.
   - Asserts relative phrases record their raw string without fabricating an artificial calendar date unless anchored by submission timestamp.
6. **Mixed-Language Text**:
   - Code-switched sentences (Hinglish: "Aaj Delhi me new policy announce hui", Tenglish: "Hyderabad lo heavy rain paddadi").
   - Asserts language detector handles mixed code and records primary language with genuine confidence.
7. **Multilingual Script & Language Support (Hindi & Telugu)**:
   - Genuine Hindi sentence: "स्वास्थ्य मंत्रालय ने नई गाइडलाइंस जारी कीं।"
   - Genuine Telugu sentence: "హైదరాబాద్‌లో భారీ వర్షం కారణంగా పాఠశాలలకు సెలవు ప్రకటించారు."
   - Asserts Devanagari and Telugu unicode text is preserved verbatim without corruption, detected as `hi` and `te`, with `detection_method` recorded.
8. **OCR Errors & Transposition Noise**:
   - OCR input with common noise ("Teh g0vernment has ann0unced...").
   - Asserts parser extracts claim resiliently and records character spans.
9. **Partial & Broken Transcripts**:
   - Whisper transcript fragments ending abruptly mid-sentence with ellipses or speaker breaks.
   - Asserts incomplete fragments are flagged as partial without hallucinating missing entities.
10. **Non-Factual & Opinion Statements**:
    - Subjective rhetoric ("This is the worst policy in human history!", "Why is everyone so angry?").
    - Asserts `is_factual_assertion == False` and proposition is flagged as opinion rather than an objective verifiable claim.

---

### B. `test_contextual_verification.py` (Adversarial Context & Provenance Tests)
1. **Legitimate Archival Reuse**:
   - Submission caption: "Remembering the 2018 Kerala floods: File photo of rescue operations."
   - Photo captured in 2018; submission in 2026.
   - Asserts `classification == "LEGITIMATE_ARCHIVAL_REUSE"`, `is_archival_reuse_signal is True`.
2. **Deceptive Historical Attribution**:
   - Submission caption: "Breaking: Massive earthquake hits city today!"
   - Photo captured in 2015; submission in 2026.
   - Asserts `classification == "HISTORICAL_CONTEXT_CONFLICT"`, temporal delta $\Delta t > 3,800\text{ days}$, `requires_human_review is True`.
3. **Missing EXIF Metadata**:
   - Stripped media without EXIF timestamp or GPS.
   - Asserts `classification == "INSUFFICIENT_CONTEXT"` without false-positive accusation.
4. **Altered / Inconsistent EXIF**:
   - File system modified time is earlier than the internal EXIF `DateTimeOriginal`.
   - Asserts inconsistency is recorded in `comparison_metrics` and flagged for investigator review.
5. **Distant Camera GPS vs. Event Location**:
   - Camera GPS shows hillside 65 km away from city center (telephoto lens).
   - Asserts Haversine distance is recorded as an evidence signal with `reliability_limitations` explaining camera vs. event position distinction.
6. **Conflicting Publication vs. Capture Dates**:
   - Article published 2 days *before* camera EXIF timestamp (indicating camera clock was misconfigured or EXIF was spoofed).
   - Asserts temporal paradox is flagged as `CONFLICTING_CONTEXT_EVIDENCE`.
7. **Repeated Events at the Same Location**:
   - Annual festival photos captured in 2022 claiming to depict the 2025 celebration at the same temple.
   - Asserts spatial distance is near 0 km ($d < 1\text{ km}$), but temporal delta $\Delta t \approx 1,095\text{ days}$ triggers temporal conflict signal.
8. **Contradictory Historical Metadata**:
   - Two historical submissions for the same asset record conflicting locations (e.g. Mumbai vs. Kolkata).
   - Asserts system outputs `CONFLICTING_CONTEXT_EVIDENCE`.

---

### C. `test_source_independence.py` (Multi-Signal Independence & Retrieval Tests)
1. **Syndicated Wire Republication Chain**:
   - 5 news outlets reprinting identical PTI wire story with different headlines.
   - Asserts `total_sources_count == 5`, `independent_sources_count == 1`, `independence_assessment == "WIRE_REPUBLICATION_CHAIN"`.
2. **Genuinely Independent Corroboration**:
   - 2 independent investigative reports with distinct bylines, unique interview quotes, and no wire markers.
   - Asserts `independent_sources_count == 2`, `independence_assessment == "INDEPENDENT_CORROBORATION"`.
3. **Shared Quotations with Independent Reporting**:
   - 2 news outlets quoting the exact same official press conference sentence, but with distinct surrounding journalistic reporting.
   - Asserts shared quotes do NOT collapse the outlets into a single source when reporting is independent.
4. **Rewritten Wire Dispatches**:
   - Article with rewritten lead paragraph that retains the underlying wire facts and agency attribution.
   - Asserts attribution detection groups it under the wire cluster despite superficial wording differences.
5. **Unknown Origins & Unresolved Dependencies**:
   - Aggregator blog with no author byline, no date, and no external citations.
   - Asserts relationship is classified as `UNRESOLVED_DEPENDENCY` and does NOT increment independent source count.
6. **Multiple Outlets Citing a Single Social Media Post**:
   - 4 news websites all citing a single unverified tweet from an anonymous account.
   - Asserts `independence_assessment == "SINGLE_SOURCE_ORIGIN"`, tracking the primary origin back to the tweet.
7. **Two Reports Sharing Facts but Not Sources**:
   - Two articles report identical casualty figures from distinct local hospitals.
   - Evaluates evidence independence dimensions.
8. **Conflicting Primary-Source Statements**:
   - Police department releases statement contradicting fire department communique.
   - Evaluates stance contradiction detection.
9. **SSRF Hardening on URL Retrieval**:
   - Attempts retrieval from `http://127.0.0.1:8000`, `http://169.254.169.254/latest/meta-data/`, and private IP ranges.
   - Asserts SSRF filter blocks requests with `SecurityException` / HTTP 400.
10. **Passage-Level Preservation Limits**:
    - Long news article (5,000 words).
    - Asserts extracted passage snippet is strictly capped at $\le 500$ characters with character offsets and canonical URL preserved.

---

### D. `test_phase4_e2e_lineage.py` (Lineage Graph & Non-Conflation Invariant Tests)
1. **Invariant 1: Authentic Media with False Caption**:
   - Authentic photograph recycled with false breaking news text.
   - Asserts media authenticity is `AUTHENTIC`, but claim assessment is `MISLEADING_CONTEXT`.
2. **Invariant 2: Manipulated Media with True Claim**:
   - Saturated/contrast-altered image accompanying a verified factual claim.
   - Asserts media authenticity indicates manipulation, but claim assessment is `SUPPORTED`. Proves non-conflation.
3. **Invariant 3: Legitimate Archival Reuse**:
   - Historical documentary citing old media with transparent historical caption.
   - Asserts assessment does NOT accuse user of misinformation.
4. **Invariant 4: Wire Reprints Do Not Equal Independent Corroboration**:
   - 10 syndicated wire articles supporting a claim.
   - Asserts `independent_sources_count == 1`. Does not treat $N=10$ reprints as 10 independent confirmations.
5. **Invariant 5: Conflicting Evidence Abstention**:
   - Authoritative sources split 50/50 on claim veracity.
   - Asserts assessment is `CONFLICTING_EVIDENCE` with structured review flags.
6. **Invariant 6: Insufficient Evidence Abstention**:
   - Novel unverified claim with zero external fact-checks.
   - Asserts assessment is `INSUFFICIENT_EVIDENCE` and compiles actionable investigator questions.
7. **Invariant 7: Breaking Claim Handling**:
   - Rapidly developing event without established consensus.
   - Asserts assessment is `UNVERIFIED`.
8. **Graph Edge Integrity**:
   - Verifies all edges in NetworkX lineage graph have explicit `edge_nature` (`OBSERVED` or `INFERRED`) and retain supporting evidence IDs.

---

## 3. Benchmark Metric Discipline

In accordance with Phase 3 audit findings:
- Candidate retrieval false positives (retrieving visually similar but distinct photographs from the index) must be measured and reported **separately** from identity-classification false positives.
- Source independence clusters must report:
  1. `total_sources_count`
  2. `independent_sources_count`
  3. `unresolved_dependencies_count`
- The system must never claim a "0% false-positive rate" without explicitly stating the benchmark denominator and defining the classification boundary.

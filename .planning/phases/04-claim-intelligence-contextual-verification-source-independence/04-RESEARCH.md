# Phase 4 Research & Architecture Specification

## 1. Technical Implementation Breakdown by Capability

| Capability | Category | Implementation Method | Fallback / Offline Behavior |
| :--- | :--- | :--- | :--- |
| **Claim Extraction** | Deterministic Algorithmic + NLP | Syntactic dependency parsing, quotation/predicate extraction, and regex entity chunkers. Supports English, Hindi, and Telugu unicode text. | Deterministic pattern matching with confidence scoring. Zero hallucination. |
| **Entity & Assertion Parsing** | Deterministic Algorithmic | Regular expressions for temporal ISO-8601 parsing, coordinate/place normalization, and numerical assert extraction. | Preserves raw verbatim substring when normalization fails. |
| **Contextual Verification** | Mathematical / Algorithmic | Julian day delta ($\Delta t = t_{\text{claimed}} - t_{\text{observed}}$), Haversine spatial geodesic distance ($d = 2R \arcsin(\dots)$), and token Jaccard overlap on event descriptions. | Outputs `INSUFFICIENT_CONTEXT` if historical metadata lacks timestamps or GPS. |
| **Archival Reuse Classifier** | Rule-Based / Contextual | Distinguishes archival reuse from deception by analyzing caption framing keywords ("File photo", "Archive", "Retrospective", "Remembering 2018") and attribution transparency. | Flags as `POSSIBLE_CONTEXT_MISALIGNMENT` requiring human review if ambiguous. |
| **Evidence Retrieval** | Retrieval-First API / Local DB | Queries ClaimReview JSON-LD fact-checks, Google Fact Check Tools API (when key available), and local offline fact-check database. | Queries local curated fact-check dataset; reports `UNAVAILABLE` or `NO_EXTERNAL_RECORDS_FOUND` if offline. |
| **Passage-Level Preservation** | Deterministic Data Architecture | Extracts exact passage snippet ($\le 500$ chars), canonical URL, publisher domain, and publication timestamp. | Raw HTML stripped; content-addressed caching in SQLite. |
| **Source Independence Analyzer** | Algorithmic Graph Analysis | Text n-gram overlap + byline syndication detection ("PTI", "ANI", "Reuters", "AP", "Syndicated Feed") clustering reprinted articles. | Single outlet labeled as `SINGLE_SOURCE_ORIGIN`; reprinted articles clustered under `WIRE_REPUBLICATION_CHAIN`. |
| **Claim Lineage Graph** | Graph Theory (NetworkX) | Directed multigraph modeling nodes (`Submission`, `MediaAsset`, `Claim`, `Source`) and typed edges (`SUPPORTS`, `CONTRADICTS`, `SAME_CLAIM`, etc.). | Serialized as node-link JSON for graph visualization and tabular edge inspection. |
| **Explainable Assessment** | Deterministic Rule-Based Logic | Goal-backward synthesis of independent corroboration count ($N_{\text{indep}} \ge 2$), context conflicts, and media authenticity signals. | Abstains with `INSUFFICIENT_EVIDENCE` or `CONFLICTING_EVIDENCE` when evidence is incomplete or split. |

---

## 2. Mathematical & Algorithmic Formulations

### A. Geodesic Distance (Haversine Formula)
For claimed location $(\phi_1, \lambda_1)$ and historical observed EXIF GPS $(\phi_2, \lambda_2)$:
$$\Delta \phi = \phi_2 - \phi_1, \quad \Delta \lambda = \lambda_2 - \lambda_1$$
$$a = \sin^2\left(\frac{\Delta \phi}{2}\right) + \cos(\phi_1)\cos(\phi_2)\sin^2\left(\frac{\Delta \lambda}{2}\right)$$
$$d = 2 R \arctan2\left(\sqrt{a}, \sqrt{1 - a}\right) \quad (R = 6,371\text{ km})$$
- If $d > 50\text{ km}$ and caption claims a local physical event: Flag spatial conflict.

### B. Temporal Delta & Julian Day Difference
$$\Delta t_{\text{days}} = \frac{t_{\text{claimed\_event}} - t_{\text{observed\_capture}}}{86,400\text{ seconds}}$$
- If $\Delta t_{\text{days}} > 30\text{ days}$: Flag temporal discrepancy.
- If $\Delta t_{\text{days}} < -1\text{ days}$ (claimed event allegedly happened *before* photo was captured): Flag physical impossibility conflict.

### C. Source Independence Metric
Let $S = \{s_1, s_2, \dots, s_k\}$ be the set of reporting articles.
For each pair $(s_i, s_j)$, compute text Jaccard similarity $J(s_i, s_j)$ on 5-grams and check shared wire agency tags $W(s_i) \cap W(s_j)$.
- If $J(s_i, s_j) > 0.60$ or $W(s_i) = W(s_j) \ne \emptyset$: $s_i$ and $s_j$ belong to the same republication component.
- The **Independent Source Count** $N_{\text{indep}}$ is the number of connected components in the independence graph.
- A claim requires $N_{\text{indep}} \ge 2$ distinct corroborating components to be confirmed without external fact-checks.

---

## 3. Database Schema Design (Additive & Non-Breaking)

### 1. `claims` table (`ClaimRecord`)
- `id`: UUID (Primary Key)
- `investigation_id`: FK -> `investigations.id`
- `evidence_submission_id`: FK -> `evidence_submissions.id`
- `claim_text`: Text (verbatim extracted assertion)
- `normalized_claim`: Text (canonicalized predicate-argument representation)
- `extracted_entities`: JSON (names, organizations, locations, dates, numbers)
- `language`: String(10) (detected language: "en", "hi", "te")
- `translation_provenance`: JSON (original_text, translated_text, engine)
- `confidence`: Float (extraction confidence score)
- `created_at`: DateTime

### 2. `context_comparisons` table (`ContextComparisonRecord`)
- `id`: UUID (Primary Key)
- `evidence_submission_id`: FK -> `evidence_submissions.id`
- `matched_media_asset_id`: FK -> `media_assets.id`
- `classification`: String(50) (`HISTORICAL_CONTEXT_CONFLICT`, `LEGITIMATE_ARCHIVAL_REUSE`, `CONSISTENT_CONTEXT`, `INSUFFICIENT_CONTEXT`)
- `claimed_event`: String(255)
- `historical_event`: String(255)
- `temporal_delta_days`: Float (signed day delta)
- `spatial_distance_km`: Float (Haversine distance)
- `is_archival_reuse`: Boolean
- `raw_comparison_metrics`: JSON (detailed field-by-field diff)
- `explanation`: Text (explainable rationale)
- `disclaimer`: Text (epistemological limits)
- `created_at`: DateTime

### 3. `retrieved_sources` table (`RetrievedSourceRecord`)
- `id`: UUID (Primary Key)
- `claim_id`: FK -> `claims.id`
- `source_type`: String(50) (`FACT_CHECK_ARTICLE`, `PRIMARY_NEWS_REPORT`, `OFFICIAL_GOVERNMENT_COMMUNIQUE`, `HISTORICAL_ARCHIVE`)
- `publisher_name`: String(255)
- `canonical_url`: String(1000)
- `article_title`: String(500)
- `published_date`: DateTime
- `fact_check_verdict`: String(100) (e.g. "False", "Misleading", "Altered Video")
- `passage_text`: Text (exact preserved snippet supporting or refuting)
- `wire_attribution`: String(100) (e.g. "PTI", "Reuters", "AP", "ANI", "Original")
- `source_credibility_signals`: JSON (transparency, publisher domain)
- `created_at`: DateTime

### 4. `source_independence_clusters` table (`SourceIndependenceRecord`)
- `id`: UUID (Primary Key)
- `claim_id`: FK -> `claims.id`
- `independent_sources_count`: Integer
- `total_sources_count`: Integer
- `cluster_breakdown`: JSON (groups of syndicated reprints)
- `independence_assessment`: String(50) (`INDEPENDENT_CORROBORATION`, `WIRE_REPUBLICATION_CHAIN`, `SINGLE_SOURCE_ORIGIN`, `UNRESOLVED_DEPENDENCY`)
- `explanation`: Text
- `created_at`: DateTime

### 5. `claim_relationships` table (`ClaimRelationshipRecord`)
- `id`: UUID (Primary Key)
- `investigation_id`: FK -> `investigations.id`
- `source_entity_id`: String(36) (Claim, Submission, or MediaAsset ID)
- `source_entity_type`: String(50)
- `target_entity_id`: String(36)
- `target_entity_type`: String(50)
- `relationship_type`: String(50) (`SUPPORTS`, `CONTRADICTS`, `SAME_CLAIM`, `CLAIM_VARIANT`, `HISTORICAL_CONTEXT_CONFLICT`, `REPEATS_SOURCE`)
- `evidence_id`: String(36) (underlying evidence supporting this relationship)
- `is_inferred`: Boolean
- `confidence`: Float
- `rationale`: Text
- `created_at`: DateTime

### 6. `claim_verdicts` table (`ClaimVerificationVerdictRecord`)
- `id`: UUID (Primary Key)
- `claim_id`: FK -> `claims.id`
- `verdict`: String(50) (`VERIFIED_TRUE`, `VERIFIED_FALSE`, `MISLEADING_CONTEXT`, `MANIPULATED_MEDIA_USED`, `INSUFFICIENT_EVIDENCE`, `CONFLICTING_EVIDENCE`)
- `independent_sources_count`: Integer
- `supporting_sources_count`: Integer
- `contradicting_sources_count`: Integer
- `has_historical_context_conflict`: Boolean
- `has_manipulated_media`: Boolean
- `summary_explanation`: Text
- `unresolved_questions`: JSON (list of open questions for investigators)
- `disclaimer`: Text
- `created_at`: DateTime

# Requirements: TRUTHNET AI

**Defined:** 2026-11-13
**Core Value:** AI identifies signals. Evidence establishes context. The system explains relationships. Investigators make decisions.

## v1 Requirements

Requirements for initial release. Each maps to roadmap phases.

### Core Architecture & Evidence Intake (INTK)

- [x] **INTK-01**: User can create, list, and switch between investigations with persistent SQLite storage.
- [x] **INTK-02**: User can submit multimodal evidence items (plain text, image files, audio files, video files, public URLs) to an investigation.
- [x] **INTK-03**: System computes and stores SHA-256 hash, MIME type, original filename, and byte size immediately upon intake.
- [x] **INTK-04**: System records submission context (claimed event, claimed date, claimed location, caption, source URL, language).
- [x] **INTK-05**: System allows individual evidence items to process or fail independently without blocking the investigation.

### Media Extraction & Technical Preprocessing (EXTR)

- [ ] **EXTR-01**: System extracts technical metadata (dimensions, duration, codecs, EXIF/container metadata) for media items.
- [ ] **EXTR-02**: System extracts text from submitted images via OCR (pytesseract or easyocr fallback).
- [ ] **EXTR-03**: System extracts speech transcripts from submitted audio and video using whisper or local speech-to-text.
- [ ] **EXTR-04**: System samples key video frames and timestamps using OpenCV / FFmpeg.
- [ ] **EXTR-05**: System categorizes all extracted content strictly as "Observed Data" distinct from model inferences.

### Media Authenticity & Deepfake Detection Engine (AUTH)

- [ ] **AUTH-01**: System maintains an auditable Model Registry recording model name, version, checkpoint identity, modality, runtime, and status.
- [ ] **AUTH-02**: System executes an actual loaded image deepfake / synthetic artifact detection model on submitted images.
- [ ] **AUTH-03**: System executes facial manipulation / anomaly detection on detected faces within images or sampled video frames.
- [ ] **AUTH-04**: System reports frame-level anomaly scores and aggregate video manipulation indicators.
- [ ] **AUTH-05**: System records raw detector outputs as "Model Output", never converting a prediction into a verified factual truth.
- [ ] **AUTH-06**: System returns an explicit "UNAVAILABLE" status with limitations when a detector checkpoint is uninstalled or unexecutable.

### Historical Media Rediscovery & Local Indexing (HIST)

- [ ] **HIST-01**: System maintains a persistent local perceptual index across application restarts without requiring external APIs.
- [ ] **HIST-02**: System computes and indexes perceptual fingerprints (pHash, dHash) for images and sampled video keyframes.
- [ ] **HIST-03**: System decouples MediaAsset (binary identity & fingerprints) from EvidenceSubmission (contextual claims & timestamps).
- [ ] **HIST-04**: When an identical file is submitted again, system reuses the existing MediaAsset while creating a distinct EvidenceSubmission.
- [ ] **HIST-05**: System classifies matches into 6 discrete levels: Exact File Match, Near-Duplicate, Same Photograph, Possible Same Photo, Visually Related, or No Sufficient Match.
- [ ] **HIST-06**: System surfaces external reverse-image search as "EXTERNAL REVERSE-IMAGE SEARCH UNAVAILABLE" unless a genuine provider is configured.

### Historical vs Current Contextual Verification (CONT)

- [ ] **CONT-01**: System compares newly claimed context (event, date, location, caption, attribution) against recorded historical context of matched media.
- [ ] **CONT-02**: System identifies explicit contradictions (e.g. historical capture date predates claimed event date).
- [ ] **CONT-03**: System identifies consistent details and legitimate archival reuse without automatically labeling historical reuse as misinformation.
- [ ] **CONT-04**: System outputs cautious, evidence-backed findings (e.g. HISTORICAL CONTEXT CONFLICT IDENTIFIED, POSSIBLE RECYCLED MEDIA).
- [ ] **CONT-05**: System preserves source attribution and retrieval dates separately from original media creation dates.

### Claim Extraction, Normalization & Multilingual Processing (CLAM)

- [ ] **CLAM-01**: System extracts factual claims from submitted text, captions, OCR, and audio/video transcripts.
- [ ] **CLAM-02**: System identifies key entities, alleged events, dates, locations, and numerical assertions for each claim.
- [ ] **CLAM-03**: System normalizes claims for semantic comparison while preserving original verbatim text and language.
- [ ] **CLAM-04**: System detects submission language with explicit support for English, Hindi, and Telugu where practical.
- [ ] **CLAM-05**: System tracks translation provenance (original text, translated text, translation method, detected language).

### Retrieval-First Evidence & Source Independence (RETR)

- [ ] **RETR-01**: System searches public web sources and fact-check databases for extracted claims.
- [ ] **RETR-02**: System extracts relevant source passages, page titles, publication dates, and canonical URLs.
- [ ] **RETR-03**: System performs source independence analysis, identifying whether multiple articles repeat the same wire service or original report.
- [ ] **RETR-04**: System classifies evidence into SUPPORTED, CONTRADICTED, MISLEADING / CONTEXT MISSING, UNVERIFIED, or INSUFFICIENT EVIDENCE.
- [ ] **RETR-05**: System explicitly abstains from declaring a claim false solely because no existing fact-check was found.

### Claim Lineage & Relationship Graph Engine (LINE)

- [ ] **LINE-01**: System builds a data-backed Claim Lineage model connecting Submissions, Claims, MediaAssets, Sources, and Accounts.
- [ ] **LINE-02**: System assigns explicit, record-backed relationship types (SAME_CLAIM, CLAIM_VARIANT, SUPPORTS, CONTRADICTS, EXACT_MEDIA_MATCH, NEAR_DUPLICATE_MEDIA, HISTORICAL_CONTEXT_CONFLICT, REPEATS_SOURCE).
- [ ] **LINE-03**: Every graph edge cites the underlying evidence ID, matching method, timestamp, and whether it is observed or inferred.
- [ ] **LINE-04**: User can interactively inspect nodes and edges in the graph to view supporting evidence in the side inspector.
- [ ] **LINE-05**: System generates a chronological investigation timeline tracking media capture, publication, submission, and claimed dates.

### Coordinated Misinformation Intelligence (CORD)

- [ ] **CORD-01**: System analyzes explainable coordination signals (caption similarity, claim clustering, media reuse, URL overlap, temporal posting bursts).
- [ ] **CORD-02**: System executes graph community detection (NetworkX) to discover clusters of tightly connected submissions or accounts.
- [ ] **CORD-03**: System records each coordination signal independently with timestamps, thresholds, and inspected time windows.
- [ ] **CORD-04**: System outputs cautious behavioral findings (e.g. SHARED CONTENT PATTERN, TEMPORAL CLUSTER IDENTIFIED) without making unsubstantiated bot/malice accusations.

### Live Monitoring & Controlled Simulation Mode (SIML)

- [ ] **SIML-01**: System provides a controlled simulation dataset with 15-20 fictional accounts and 30-50 posts illustrating a coordinated misinformation event.
- [ ] **SIML-02**: System clearly and visibly tags all synthetic/simulated records with the "SIMULATED" badge across all views and APIs.
- [ ] **SIML-03**: System passes simulated items through the identical evidence ingestion, extraction, and relationship pipeline as real submissions.
- [ ] **SIML-04**: User can promote a detected cluster from simulation / live feed directly into a formal investigation.
- [ ] **SIML-05**: System uses WebSockets or server-sent events for genuine real-time processing progress without frontend fake timers.

### Incident Prioritization & Human Review Workbench (WORK)

- [ ] **WORK-01**: System computes explainable investigation priority (LOW, MEDIUM, HIGH, URGENT REVIEW) based on velocity, media reuse, and unresolved conflicts.
- [ ] **WORK-02**: Investigator can record notes, mark evidence relevance, and record final human verdicts (Verified Authentic, Misleading Context, Manipulated Media, Inconclusive).
- [ ] **WORK-03**: Investigator can dispute or override automated model findings without erasing the original model output.
- [ ] **WORK-04**: System maintains an append-only Audit Record of all investigator actions, timestamped with user identity.

### Workbench UI & Visualization (UIUX)

- [ ] **UIUX-01**: Clean, calm, information-dense visual identity using warm neutrals, readable typography, and teal/amber/red status accents.
- [ ] **UIUX-02**: Concise landing page communicating core principles, workflow, and direct entry points into investigations.
- [ ] **UIUX-03**: Three-pane investigation workspace (Left: Navigation & Evidence Queue; Center: Claim Lineage & Timeline; Right: Evidence Inspector).
- [ ] **UIUX-04**: Dedicated side-by-side Historical Media Comparison view highlighting matching regions, metadata diffs, and context conflicts.
- [ ] **UIUX-05**: Consistent progressive disclosure of technical model details and honest capability status badges.

### Traceable Case Reporting & Demo Scenarios (REPO)

- [ ] **REPO-01**: User can generate and export a comprehensive case report (JSON / Markdown / printable HTML) with full evidence provenance and chain of custody.
- [ ] **REPO-02**: Report clearly distinguishes the 5 categories (Observed Data, Model Output, Retrieved Evidence, System Inference, Investigator Decision).
- [ ] **REPO-03**: System includes Scenario A: Historical contextual conflict demonstration with reproducible assets.
- [ ] **REPO-04**: System includes Scenario B: Legitimate archival reuse demonstration with valid context.
- [ ] **REPO-05**: System includes Scenario C: Claim verification with source attribution and abstention demonstration.
- [ ] **REPO-06**: System includes Scenario D: Coordinated activity detection on labeled simulated dataset.
- [ ] **REPO-07**: System includes Scenario E: Media authenticity execution with real model inference or explicit unavailable handling.

## v2 Requirements

Deferred to future release. Tracked but not in current roadmap.

### Advanced Capabilities

- **ADV-01**: Multilingual speech-to-text fine-tuning for regional Indian dialects.
- **ADV-02**: Hardware-accelerated local vector database (Chroma/Milvus) for 1M+ image embedding index.
- **ADV-03**: Direct integration with official commercial reverse-image search APIs (Google Lens / TinEye enterprise) when paid credentials are provided.
- **ADV-04**: Automated video frame-by-frame deepfake heatmaps overlaying face bounding boxes.

## Out of Scope

Explicitly excluded. Documented to prevent scope creep.

| Feature | Reason |
|---------|--------|
| Fabricated model confidence scores | Violates non-negotiable principle 1.1; explicit UNAVAILABLE status used when models cannot execute |
| Cloud-only microservices / Kubernetes | Violates modular monolith and local-first architecture requirement |
| Direct scraping of private social media feeds | Violates platform terms and rate limits; handled via public URLs or labeled simulation |
| Autonomous truth determination by LLM | Violates principle that evidence establishes context and humans make decisions |
| Whole-video identity claims based on single frames | Frame matches report specific timestamps and matched frames only |

## Traceability

Which phases cover which requirements. Updated during roadmap creation.

| Requirement | Phase | Status |
|-------------|-------|--------|
| INTK-01 | Phase 1 | Complete |
| INTK-02 | Phase 1 | Complete |
| INTK-03 | Phase 1 | Complete |
| INTK-04 | Phase 1 | Complete |
| INTK-05 | Phase 1 | Complete |
| EXTR-01 | Phase 2 | Pending |
| EXTR-02 | Phase 2 | Pending |
| EXTR-03 | Phase 2 | Pending |
| EXTR-04 | Phase 2 | Pending |
| EXTR-05 | Phase 2 | Pending |
| HIST-01 | Phase 3 | Pending |
| HIST-02 | Phase 3 | Pending |
| HIST-03 | Phase 3 | Pending |
| HIST-04 | Phase 3 | Pending |
| HIST-05 | Phase 3 | Pending |
| HIST-06 | Phase 3 | Pending |
| CONT-01 | Phase 4 | Pending |
| CONT-02 | Phase 4 | Pending |
| CONT-03 | Phase 4 | Pending |
| CONT-04 | Phase 4 | Pending |
| CONT-05 | Phase 4 | Pending |
| AUTH-01 | Phase 5 | Pending |
| AUTH-02 | Phase 5 | Pending |
| AUTH-03 | Phase 5 | Pending |
| AUTH-04 | Phase 5 | Pending |
| AUTH-05 | Phase 5 | Pending |
| AUTH-06 | Phase 5 | Pending |
| CLAM-01 | Phase 6 | Pending |
| CLAM-02 | Phase 6 | Pending |
| CLAM-03 | Phase 6 | Pending |
| CLAM-04 | Phase 6 | Pending |
| CLAM-05 | Phase 6 | Pending |
| RETR-01 | Phase 7 | Pending |
| RETR-02 | Phase 7 | Pending |
| RETR-03 | Phase 7 | Pending |
| RETR-04 | Phase 7 | Pending |
| RETR-05 | Phase 7 | Pending |
| LINE-01 | Phase 8 | Pending |
| LINE-02 | Phase 8 | Pending |
| LINE-03 | Phase 8 | Pending |
| LINE-04 | Phase 8 | Pending |
| LINE-05 | Phase 8 | Pending |
| CORD-01 | Phase 9 | Pending |
| CORD-02 | Phase 9 | Pending |
| CORD-03 | Phase 9 | Pending |
| CORD-04 | Phase 9 | Pending |
| SIML-01 | Phase 10 | Pending |
| SIML-02 | Phase 10 | Pending |
| SIML-03 | Phase 10 | Pending |
| SIML-04 | Phase 10 | Pending |
| SIML-05 | Phase 10 | Pending |
| WORK-01 | Phase 11 | Pending |
| WORK-02 | Phase 11 | Pending |
| WORK-03 | Phase 11 | Pending |
| WORK-04 | Phase 11 | Pending |
| UIUX-01 | Phase 12 | Pending |
| UIUX-02 | Phase 12 | Pending |
| UIUX-03 | Phase 12 | Pending |
| UIUX-04 | Phase 12 | Pending |
| UIUX-05 | Phase 12 | Pending |
| REPO-01 | Phase 12 | Pending |
| REPO-02 | Phase 12 | Pending |
| REPO-03 | Phase 12 | Pending |
| REPO-04 | Phase 12 | Pending |
| REPO-05 | Phase 12 | Pending |
| REPO-06 | Phase 12 | Pending |
| REPO-07 | Phase 12 | Pending |

**Coverage:**
- v1 requirements: 65 total
- Mapped to phases: 65
- Unmapped: 0 ✓

---
*Requirements defined: 2026-11-13*
*Last updated: 2026-11-13 after initialization*

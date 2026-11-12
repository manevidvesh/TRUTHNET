# Roadmap: TRUTHNET AI

## Overview

TRUTHNET AI is built in 12 focused phases delivering a complete multimodal misinformation investigation workbench. Starting with a rock-solid modular monolith foundation, intake pipeline, and technical extraction, the platform implements persistent historical media indexing and contextual verification (the signature differentiator), real media authenticity detection, retrieval-first claim verification with source independence, Claim Lineage graphs, explainable coordination intelligence, labeled simulation mode, investigator review, and a calm, information-dense intelligence workbench with 5 reproducible demo scenarios.

## Phases

**Phase Numbering:**
- Integer phases (1, 2, 3...): Planned milestone work
- Decimal phases (2.1, 2.2...): Urgent insertions (marked with INSERTED)

- [x] **Phase 1: Foundation & Vertical Slice Intake Pipeline** - Establish modular monolith architecture, SQLite schema, investigation CRUD, and multimodal evidence intake.
- [x] **Phase 2: Multimodal Extraction & Media Preprocessing** - Extract technical metadata, OCR, speech transcripts, and video keyframes strictly as Observed Data.
- [x] **Phase 3: Persistent Historical Media Indexing & Perceptual Hashing** - Implement local perceptual index, MediaAsset vs EvidenceSubmission decoupling, and 6-level match classification.
- [ ] **Phase 4: Historical vs Current Contextual Verification Engine** - Build automated contextual comparison diffing claimed vs historical event, date, location, and attribution.
- [ ] **Phase 5: Media Authenticity & Deepfake Model Detection Engine** - Build auditable Model Registry, real detector inference, facial anomaly analysis, and explicit unavailable reporting.
- [ ] **Phase 6: Claim Extraction, Normalization & Multilingual Processing** - Extract and normalize factual claims, preserve original text, and handle English, Hindi, and Telugu.
- [ ] **Phase 7: Retrieval-First Fact Verification & Source Independence** - Retrieve public sources and fact-checks, analyze source independence (wire repeats vs corroboration), and cautious assessment.
- [ ] **Phase 8: Claim Lineage & Interactive Relationship Graph** - Build record-backed lineage graph, explicit relationship typing, timeline generation, and edge-level evidence inspection.
- [ ] **Phase 9: Coordinated Misinformation Intelligence Engine** - Detect caption similarity, temporal bursts, media reuse, and NetworkX community clusters with explainable signals.
- [ ] **Phase 10: Real-Time Event Pipeline & Labeled Simulation Mode** - Deliver genuine WebSocket/SSE progress updates and a 15-20 account / 30-50 post labeled SIMULATED demonstration scenario.
- [ ] **Phase 11: Incident Prioritization & Human Review Workbench** - Implement explainable priority scoring, investigator review verdicts, overrides, and append-only audit trail.
- [ ] **Phase 12: Intelligence Workbench UI, Case Reporting & End-to-End Scenarios** - Build the Next.js investigative UI, exportable case reports, and 5 verified demonstration scenarios.

## Phase Details

### Phase 1: Foundation & Vertical Slice Intake Pipeline
**Goal**: Establish the core modular monolith architecture (FastAPI + SQLite), investigation lifecycle, and multimodal evidence intake pipeline.
**Mode:** mvp
**Depends on**: Nothing (first phase)
**Requirements**: INTK-01, INTK-02, INTK-03, INTK-04, INTK-05
**Success Criteria** (what must be TRUE):
  1. User can create, list, view, and manage investigations in SQLite database.
  2. User can submit multimodal evidence items (text, images, audio, video, URLs) with immediate SHA-256 calculation and metadata recording.
  3. Evidence items process asynchronously and failures on one item do not crash or abort the parent investigation.
**Plans**: 3 plans

Plans:
- [x] 01-01: Foundation, SQLite WAL Database Setup, and Investigation Lifecycle
- [x] 01-02: Storage Engine, MediaAsset/EvidenceSubmission Decoupling, and Streaming Multimodal Intake
- [x] 01-03: Asynchronous Processing Pipeline, Fault Isolation, and Duplicate File Resilience

### Phase 2: Multimodal Extraction & Media Preprocessing
**Goal**: Implement technical metadata extraction, OCR, speech-to-text transcription, and video keyframe sampling.
**Mode:** mvp
**Depends on**: Phase 1
**Requirements**: EXTR-01, EXTR-02, EXTR-03, EXTR-04, EXTR-05
**Success Criteria** (what must be TRUE):
  1. Image text is extracted via local OCR and stored with bounding coordinates and text contents.
  2. Audio and video files produce time-aligned speech transcripts via local speech-to-text.
  3. Video files are decomposed into sampled keyframes with timestamps using OpenCV/FFmpeg.
  4. All extracted outputs are strictly tagged as "Observed Data" distinct from inferences.
**Plans**: 3 plans

Plans:
- [x] 02-01: Versioned Extraction Schema, EXIF Timezone Discipline, and Artifact Security
- [x] 02-02: Boundary-Anchored Video Keyframes, PyAV Audio Demuxing, and Artifact Provenance
- [x] 02-03: Dual-Engine OCR, faster-whisper Speech Transcription, and Pipeline Integration

### Phase 3: Persistent Historical Media Indexing & Perceptual Hashing
**Goal**: Implement the persistent local historical media index, perceptual hashing (pHash/dHash), and MediaAsset vs EvidenceSubmission decoupling.
**Mode:** mvp
**Depends on**: Phase 2
**Requirements**: HIST-01, HIST-02, HIST-03, HIST-04, HIST-05, HIST-06
**Success Criteria** (what must be TRUE):
  1. Perceptual index survives application restarts and updates incrementally without full re-indexing.
  2. Exact duplicate file submissions reuse the existing MediaAsset while creating distinct EvidenceSubmissions preserving separate contexts.
  3. Media matching returns one of 6 discrete classifications (EXACT_FILE_MATCH, NEAR_DUPLICATE, SAME_PHOTOGRAPH_MODIFIED, POSSIBLE_VISUAL_SIMILARITY, INSUFFICIENT_MATCH_EVIDENCE, NO_LOCAL_MATCH_FOUND) with raw measurements and without arbitrary confidence percentages.
  4. External reverse-image search reports "EXTERNAL REVERSE-IMAGE SEARCH UNAVAILABLE" honestly without returning fabricated or mocked hits.
**Plans**: 3 plans

Plans:
- [x] 03-01: Persistent Fingerprint Schema, Preprocessing V1, Descriptor Store, and Hasher Indexer
- [x] 03-02: Candidate Retrieval, Geometric ORB+RANSAC Verification, and Six-Classification Match Engine
- [x] 03-03: Matching REST APIs, Cross-Investigation Privacy, Multi-Frame Video Tracking, and Expanded Benchmark

### Phase 4: Historical vs Current Contextual Verification Engine
**Goal**: Build the context comparison engine that detects conflicts between earlier recorded media context and newly claimed context.
**Mode:** mvp
**Depends on**: Phase 3
**Requirements**: CONT-01, CONT-02, CONT-03, CONT-04, CONT-05
**Success Criteria** (what must be TRUE):
  1. System compares newly claimed event, date, location, caption, and attribution against historical records.
  2. Temporal and geographical conflicts are detected and highlighted as evidence-backed findings (e.g. capture date predating claimed event date).
  3. System distinguishes legitimate archival reuse from misleading recycling without false-positive accusations.
**Plans**: TBD

### Phase 5: Media Authenticity & Deepfake Model Detection Engine
**Goal**: Implement the auditable Model Registry and real execution of image, facial, and video manipulation detectors.
**Mode:** mvp
**Depends on**: Phase 2
**Requirements**: AUTH-01, AUTH-02, AUTH-03, AUTH-04, AUTH-05, AUTH-06
**Success Criteria** (what must be TRUE):
  1. Model Registry records checkpoint identity, runtime, modality, and execution status.
  2. Loaded deepfake/manipulation models execute actual inference on images and sampled video frames.
  3. Raw scores are categorized as "Model Output" without equating them to verified truth.
  4. Uninstalled or unexecutable checkpoints report an explicit "UNAVAILABLE" status with limitations.
**Plans**: TBD

### Phase 6: Claim Extraction, Normalization & Multilingual Processing
**Goal**: Extract verifiable factual claims from text, captions, OCR, and transcripts with multilingual support.
**Mode:** mvp
**Depends on**: Phase 2
**Requirements**: CLAM-01, CLAM-02, CLAM-03, CLAM-04, CLAM-05
**Success Criteria** (what must be TRUE):
  1. Factual assertions are extracted with associated entities, events, dates, locations, and numbers.
  2. Normalized claims are generated for matching while verbatim text and detected language are preserved.
  3. System supports multilingual inputs with explicit handling for English, Hindi, and Telugu.
**Plans**: TBD

### Phase 7: Retrieval-First Fact Verification & Source Independence
**Goal**: Implement public-source retrieval, fact-check matching, and source independence analysis.
**Mode:** mvp
**Depends on**: Phase 6
**Requirements**: RETR-01, RETR-02, RETR-03, RETR-04, RETR-05
**Success Criteria** (what must be TRUE):
  1. System retrieves public sources and fact-checks relevant to extracted claims.
  2. System detects syndicated reporting and common wire sources, avoiding false multi-source independence.
  3. Claims are assigned cautious statuses (SUPPORTED, CONTRADICTED, MISLEADING / CONTEXT MISSING, UNVERIFIED, INSUFFICIENT EVIDENCE) and system abstains when evidence is missing.
**Plans**: TBD

### Phase 8: Claim Lineage & Interactive Relationship Graph
**Goal**: Build the data-backed Claim Lineage model and interactive graph connecting submissions, claims, media, and sources.
**Mode:** mvp
**Depends on**: Phase 4, Phase 7
**Requirements**: LINE-01, LINE-02, LINE-03, LINE-04, LINE-05
**Success Criteria** (what must be TRUE):
  1. Every graph edge represents a specific record-backed relationship type (SAME_CLAIM, CLAIM_VARIANT, EXACT_MEDIA_MATCH, HISTORICAL_CONTEXT_CONFLICT, etc.).
  2. Selecting any node or edge reveals the supporting evidence ID, matching method, and observed vs inferred status.
  3. An interactive timeline arranges media capture, publication, submission, and claimed event dates chronologically.
**Plans**: TBD

### Phase 9: Coordinated Misinformation Intelligence Engine
**Goal**: Implement explainable coordination signal analysis and graph community detection.
**Mode:** mvp
**Depends on**: Phase 8
**Requirements**: CORD-01, CORD-02, CORD-03, CORD-04
**Success Criteria** (what must be TRUE):
  1. System detects caption similarity, claim clustering, media reuse, URL overlap, and temporal posting bursts.
  2. NetworkX community detection groups related submissions into explainable clusters.
  3. System reports cautious behavioral findings (e.g. SHARED CONTENT PATTERN) without making unverified bot/actor accusations.
**Plans**: TBD

### Phase 10: Real-Time Event Pipeline & Labeled Simulation Mode
**Goal**: Build genuine event-driven progress notifications and a reproducible, clearly labeled 15-20 account simulation dataset.
**Mode:** mvp
**Depends on**: Phase 9
**Requirements**: SIML-01, SIML-02, SIML-03, SIML-04, SIML-05
**Success Criteria** (what must be TRUE):
  1. WebSockets/SSE stream real backend processing state without artificial frontend delays.
  2. Controlled simulation dataset (15-20 fictional accounts, 30-50 posts) processes through the exact same ingestion and relationship pipeline.
  3. All simulated records prominently display the "SIMULATED" badge across all UI views and API payloads.
  4. Users can promote a detected cluster directly into a new formal investigation.
**Plans**: TBD

### Phase 11: Incident Prioritization & Human Review Workbench
**Goal**: Build explainable case prioritization and investigator decision recording with append-only audit history.
**Mode:** mvp
**Depends on**: Phase 1, Phase 8
**Requirements**: WORK-01, WORK-02, WORK-03, WORK-04
**Success Criteria** (what must be TRUE):
  1. System computes explainable case priority (LOW, MEDIUM, HIGH, URGENT REVIEW) citing specific driving factors.
  2. Investigators can record notes, mark evidence relevance, and enter final verdicts.
  3. Investigators can dispute automated findings while keeping original model outputs intact.
  4. Every human review action is preserved in an immutable, timestamped audit log.
**Plans**: TBD

### Phase 12: Intelligence Workbench UI, Case Reporting & End-to-End Scenarios
**Goal**: Deliver the polished Next.js workbench interface, exportable case reports, and 5 verified demonstration scenarios.
**Mode:** mvp
**Depends on**: Phase 5, Phase 10, Phase 11
**Requirements**: UIUX-01, UIUX-02, UIUX-03, UIUX-04, UIUX-05, REPO-01, REPO-02, REPO-03, REPO-04, REPO-05, REPO-06, REPO-07
**Success Criteria** (what must be TRUE):
  1. Responsive, calm, three-pane intelligence workbench (Navigation, Claim Lineage/Timeline, Inspector) is fully functional.
  2. Dedicated side-by-side Historical Media Comparison view highlights metadata differences and contextual conflicts.
  3. Comprehensive case reports can be exported (JSON/Markdown/HTML) with full chain of custody.
  4. All 5 demo scenarios (A: Historical Conflict, B: Archival Reuse, C: Claim Verification, D: Coordinated Activity, E: Media Authenticity) execute end-to-end reliably.
**Plans**: TBD

## Progress

**Execution Order:**
Phases execute in numeric order: 1 → 2 → 3 → 4 → 5 → 6 → 7 → 8 → 9 → 10 → 11 → 12

| Phase | Plans Complete | Status | Completed |
|-------|----------------|--------|-----------|
| 1. Foundation & Vertical Slice Intake Pipeline | 3/3 | Complete | 2026-11-13 |
| 2. Multimodal Extraction & Media Preprocessing | 0/TBD | Not started | - |
| 3. Persistent Historical Media Indexing & Perceptual Hashing | 0/TBD | Not started | - |
| 4. Historical vs Current Contextual Verification Engine | 0/TBD | Not started | - |
| 5. Media Authenticity & Deepfake Model Detection Engine | 0/TBD | Not started | - |
| 6. Claim Extraction, Normalization & Multilingual Processing | 0/TBD | Not started | - |
| 7. Retrieval-First Fact Verification & Source Independence | 0/TBD | Not started | - |
| 8. Claim Lineage & Interactive Relationship Graph | 0/TBD | Not started | - |
| 9. Coordinated Misinformation Intelligence Engine | 0/TBD | Not started | - |
| 10. Real-Time Event Pipeline & Labeled Simulation Mode | 0/TBD | Not started | - |
| 11. Incident Prioritization & Human Review Workbench | 0/TBD | Not started | - |
| 12. Intelligence Workbench UI, Case Reporting & End-to-End Scenarios | 0/TBD | Not started | - |

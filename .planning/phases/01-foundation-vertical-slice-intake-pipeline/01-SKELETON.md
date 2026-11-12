# Walking Skeleton — TRUTHNET AI

**Phase:** 1
**Generated:** 2026-11-13

## Capability Proven End-to-End

An investigator can create an investigation, submit multimodal evidence items (files, text, URLs), verify their byte-for-byte streaming SHA-256 calculation and persistent decoupling into MediaAsset and EvidenceSubmission records, and inspect the investigation and evidence status via authenticated/typed REST endpoints.

## Architectural Decisions

| Decision | Choice | Rationale |
|---|---|---|
| Backend Framework | FastAPI 0.110+ (Python 3.10+) | High performance, native async support, automatic OpenAPI/Swagger documentation, robust validation |
| Data Layer | SQLite 3 with WAL Mode + SQLAlchemy 2.0 Async | Local-first, zero-infrastructure footprint, robust multi-reader concurrent write capability, clean migration path |
| File Storage Engine | Content-Addressed Local Filesystem (`data/uploads/{hash[:2]}/{hash}.{ext}`) | Deduplicated physical storage with streaming SHA-256 verification and directory sharding |
| API Structure | Versioned Modular REST API (`backend/app/api/v1/`) | Clean separation of concerns with Pydantic v2 schemas and centralized dependency injection |
| Error Boundaries | Isolated Per-Item Processing State | Prevents a single corrupt file or unreachable URL from aborting an investigation |

## Stack Touched in Phase 1

- [x] Project scaffold (Python backend directory structure, configuration, requirements, pytest harness)
- [x] Routing — `/api/v1/health`, `/api/v1/investigations/`, `/api/v1/investigations/{id}/evidence/`
- [x] Database — SQLite database creation with WAL mode, foreign keys, and tables for `investigations`, `media_assets`, `evidence_submissions`
- [x] Storage — Streaming upload handler writing to disk and computing SHA-256 in a single pass
- [x] Test Suite — Automated pytest integration suite verifying end-to-end evidence ingestion and persistence

## Out of Scope (Deferred to Later Slices)

- Deepfake / authenticity model inference (Phase 5)
- Perceptual hashing and cross-investigation historical rediscovery (Phase 3)
- Contextual diffing engine (Phase 4)
- Web search / fact-check source retrieval (Phase 7)
- Claim Lineage interactive graph and timeline UI (Phase 8, 12)
- Frontend client application (Phase 12)

## Subsequent Slice Plan

Each later phase adds one vertical slice on top of this skeleton without altering its architectural decisions:

- Phase 2: Multimodal Extraction & Media Preprocessing (metadata, OCR, whisper, keyframes)
- Phase 3: Persistent Historical Media Indexing & Perceptual Hashing (pHash/dHash, 6-level match classification)
- Phase 4: Historical vs Current Contextual Verification Engine (claimed vs historical metadata diffing)
- Phase 5: Media Authenticity & Deepfake Model Detection Engine (model registry, real inference)
- Phase 6: Claim Extraction, Normalization & Multilingual Processing (English, Hindi, Telugu)
- Phase 7: Retrieval-First Fact Verification & Source Independence (fact-checks, wire repetition detection)
- Phase 8: Claim Lineage & Interactive Relationship Graph (record-backed edges, timeline)
- Phase 9: Coordinated Misinformation Intelligence Engine (NetworkX community detection, burst detection)
- Phase 10: Real-Time Event Pipeline & Labeled Simulation Mode (WebSockets, synthetic demonstration)
- Phase 11: Incident Prioritization & Human Review Workbench (audit trail, priority scoring)
- Phase 12: Intelligence Workbench UI, Case Reporting & End-to-End Scenarios (Next.js, PDF/HTML reports, 5 demo scenarios)

# Phase 1: Foundation & Vertical Slice Intake Pipeline - Context

**Gathered:** 2026-11-13
**Status:** Ready for planning

<domain>
## Phase Boundary

Phase 1 delivers the foundational backend modular monolith and end-to-end evidence intake pipeline for TRUTHNET AI. It establishes the FastAPI application structure, SQLite database with SQLAlchemy models (WAL mode enabled), investigation lifecycle management (CRUD), file storage management with streaming SHA-256 calculation, and asynchronous intake for multimodal evidence (text, image, audio, video, public URLs) with isolated per-item failure handling.

</domain>

<decisions>
## Implementation Decisions

### Architecture & Service Structure
- **D-01:** Modular monolith using Python 3.10+, FastAPI, Pydantic v2, and SQLAlchemy with SQLite. — **Reversibility:** one-way — Core framework and persistence foundation for the entire backend.
- **D-02:** Local filesystem storage under `data/uploads/` structured by investigation and content hash, with strictly sanitized filenames and preserved original binaries. — **Reversibility:** costly — Changes would require migrating stored file references.
- **D-03:** Async background worker pipeline using `asyncio` task queues for intake and validation, persisting progress state per evidence item. — **Reversibility:** reversible — Worker queue abstraction can adapt to other mechanisms if needed.

### Database Contracts & Decoupling
- **D-04:** Immediate decoupling between `MediaAsset` (immutable binary identity, SHA-256, storage path, byte count) and `EvidenceSubmission` (mutable investigative context, claimed event, claimed date, claimed location, caption, source URL, language, submission timestamp). — **Reversibility:** one-way — Fundamental architectural decision required for duplicate media reuse and contextual verification.
- **D-05:** SQLite WAL (Write-Ahead Logging) mode and foreign key constraints enabled at connection time to support concurrent async reads/writes without locking errors. — **Reversibility:** reversible — Database connection pragma configuration.

### Evidence Ingestion & Fault Isolation
- **D-06:** Streaming SHA-256 computation during file upload chunking before disk write to prevent memory exhaustion on large video/audio files. — **Reversibility:** reversible — Ingestion stream utility implementation.
- **D-07:** Resilient per-item processing status: `PENDING`, `EXTRACTING`, `ANALYZING`, `COMPLETED`, `FAILED`. Any single item failure logs errors on that item record and sets status `FAILED` without terminating or blocking other items in the investigation. — **Reversibility:** costly — Impacts all downstream pipeline consumers.

### Antigravity's Discretion
- Database migration approach: lightweight SQLAlchemy metadata creation for development prototype with clear migration hook.
- Input validation thresholds: 100MB max file size for video/audio, 20MB for images, with MIME-type verification via magic bytes.
- CORS configuration supporting local Next.js frontend (default `http://localhost:3000`).

</decisions>

<canonical_refs>
## Canonical References

**Downstream agents MUST read these before planning or implementing.**

### Project Specifications
- `.planning/PROJECT.md` — Core value, non-negotiable engineering principles (Section 1), 5-category distinction, and constraints.
- `.planning/REQUIREMENTS.md` — INTK-01 through INTK-05 definitions and acceptance criteria.
- `.planning/ROADMAP.md` — Phase 1 scope and success criteria.

### Data Models & Contracts
- `backend/app/models/` — SQLAlchemy database entities (`Investigation`, `EvidenceSubmission`, `MediaAsset`).
- `backend/app/schemas/` — Pydantic request and response schemas for investigations and evidence intake.
</canonical_refs>

<specific_guidance>
## Specific Guidance

1. **Balanced Vertical Slice**: Focus squarely on building the solid foundation and intake pipeline first. Do not jump ahead to historical matching or deepfake inference in Phase 1 before the intake contracts, persistence, and error boundaries are tested and solid.
2. **Strict Category Discipline**: Ensure database fields and API responses cleanly separate observed metadata (file size, SHA-256, MIME type, submission timestamp) from user-claimed context (alleged date, location, event, caption).
3. **Automated Verification**: Include automated unit and integration tests verifying:
   - Creating investigations and retrieving them.
   - Uploading image, audio, video, text, and URL evidence.
   - Exact SHA-256 hashing and MediaAsset record creation.
   - Multiple evidence submissions linking to one investigation.
   - Fault tolerance when an invalid file or unreachable URL is submitted.
</specific_guidance>

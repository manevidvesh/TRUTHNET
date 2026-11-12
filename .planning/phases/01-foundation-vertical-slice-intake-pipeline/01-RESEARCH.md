# Phase 1: Foundation & Vertical Slice Intake Pipeline - Research

**Researched:** 2026-11-13
**Domain:** FastAPI backend architecture, asynchronous evidence intake, SQLite WAL persistence, streaming file hashing
**Confidence:** HIGH

<user_constraints>
## User Constraints (from CONTEXT.md)

### Locked Decisions
- **D-01:** Modular monolith using Python 3.10+, FastAPI, Pydantic v2, and SQLAlchemy with SQLite.
- **D-02:** Local filesystem storage under `data/uploads/` structured by investigation and content hash, with strictly sanitized filenames and preserved original binaries.
- **D-03:** Async background worker pipeline using `asyncio` task queues for intake and validation, persisting progress state per evidence item.
- **D-04:** Immediate decoupling between `MediaAsset` (immutable binary identity, SHA-256, storage path, byte count) and `EvidenceSubmission` (mutable investigative context, claimed event, claimed date, claimed location, caption, source URL, language, submission timestamp).
- **D-05:** SQLite WAL (Write-Ahead Logging) mode and foreign key constraints enabled at connection time to support concurrent async reads/writes without locking errors.
- **D-06:** Streaming SHA-256 computation during file upload chunking before disk write to prevent memory exhaustion on large video/audio files.
- **D-07:** Resilient per-item processing status: PENDING, EXTRACTING, ANALYZING, COMPLETED, FAILED. Any single item failure logs errors on that item record without terminating or blocking other items in the investigation.

### Antigravity's Discretion
- SQLite connection pool settings: `poolclass=StaticPool` for in-memory tests, default queue pool with WAL mode for file database.
- Input validation thresholds: 100MB max file size for video/audio, 20MB for images, with MIME-type verification.
- CORS configuration supporting local Next.js frontend (default `http://localhost:3000`).

### Deferred Ideas (OUT OF SCOPE)
- Direct cloud storage integration (AWS S3, Google Cloud Storage) — keep local-first for offline reliability.
- Distributed Celery/Redis queues — unnecessary overhead; local asyncio queues provide sufficient concurrency.
</user_constraints>

<architectural_responsibility_map>
## Architectural Responsibility Map

| Capability | Primary Tier | Secondary Tier | Rationale |
|------------|-------------|----------------|-----------|
| Investigation Management (CRUD) | API/Backend | Database/Storage | High-level container for cases, stored in SQLite |
| Multimodal Evidence Intake | API/Backend | Local Storage | Streaming file ingestion, MIME validation, SHA-256 hashing |
| Binary Storage & Deduplication | Database/Storage | Local Storage | MediaAsset record decoupled from EvidenceSubmission |
| Async Processing Pipeline | API/Backend | Database/Storage | Non-blocking execution state updates per evidence item |
</architectural_responsibility_map>

<research_summary>
## Summary

Phase 1 establishes the core backend foundation and vertical intake pipeline for TRUTHNET AI. The architecture utilizes Python 3.10+, FastAPI for asynchronous API endpoints, SQLAlchemy 2.0 with async SQLite (via `aiosqlite`) or standard SQLite with WAL mode (`PRAGMA journal_mode=WAL; PRAGMA foreign_keys=ON;`), and Pydantic v2 for data validation.

The evidence intake engine is built around the fundamental requirement of separating `MediaAsset` (the immutable physical media file identified by byte-for-byte SHA-256) from `EvidenceSubmission` (the contextual, human- or user-provided claim metadata). This enables the same physical media file to be submitted across multiple investigations or multiple times within the same investigation with conflicting dates, locations, or captions without clobbering history.

Evidence ingestion streams uploaded chunks (64KB chunks) to calculate SHA-256 in a single pass while writing to an isolated file path (`data/uploads/{sha256[:2]}/{sha256}.{ext}`). Each evidence item is tracked with fine-grained status (`PENDING`, `COMPLETED`, `FAILED`), and processing errors are localized to the specific item.

**Primary recommendation:** Build a clean, modular Python package structure (`backend/app/{core, models, schemas, api, services, storage}`) with automated pytest tests verifying multi-item intake, streaming SHA-256 calculation, and database persistence.
</research_summary>

<standard_stack>
## Standard Stack

### Core
| Library | Version | Purpose | Why Standard |
|---------|---------|---------|--------------|
| `fastapi` | >=0.110.0 | Async web framework | High-performance, automatic OpenAPI docs, native Pydantic v2 integration |
| `uvicorn` | >=0.28.0 | ASGI web server | Production-grade lightweight server for FastAPI |
| `sqlalchemy` | >=2.0.28 | ORM & database toolkit | Industry standard Python ORM with modern typed 2.0 declarative syntax |
| `pydantic` | >=2.6.0 | Schema validation | High speed (Rust core), type-safe request/response contracts |
| `aiosqlite` | >=0.20.0 | Async SQLite driver | Non-blocking database I/O for FastAPI async routes |
| `python-multipart` | >=0.0.9 | Form & file upload parsing | Standard ASGI parser for streaming multipart/form-data |

### Supporting
| Library | Version | Purpose | When to Use |
|---------|---------|---------|-------------|
| `pytest` | >=8.0.0 | Testing framework | Unit and integration test suite |
| `httpx` | >=0.27.0 | Async HTTP client | Ingesting public URLs and testing FastAPI via AsyncClient |
| `filetype` | >=1.2.0 | Lightweight MIME detection | Detecting genuine MIME types from file header magic bytes |

**Installation:**
```bash
pip install fastapi uvicorn sqlalchemy aiosqlite pydantic python-multipart httpx filetype pytest
```
</standard_stack>

<architecture_patterns>
## Architecture Patterns

### Intake Pipeline Data Flow
```
User / Client
   │
   ├─► POST /api/v1/investigations/ (Creates investigation)
   │
   └─► POST /api/v1/investigations/{id}/evidence (Uploads files/text/URLs)
          │
          ▼
   StorageManager (Streams chunks, computes SHA-256, validates magic bytes)
          │
          ▼
   MediaAsset (Find or Create by SHA-256)
          │
          ▼
   EvidenceSubmission (Creates record linked to Investigation & MediaAsset with contextual metadata)
          │
          ▼
   Background Worker (Sets PENDING -> COMPLETED / FAILED, emits event)
```

### Database Schema Pattern
```sql
CREATE TABLE media_assets (
    id TEXT PRIMARY KEY,
    sha256_hash TEXT NOT NULL UNIQUE,
    mime_type TEXT NOT NULL,
    file_path TEXT NOT NULL,
    file_size_bytes INTEGER NOT NULL,
    created_at TIMESTAMP NOT NULL
);

CREATE TABLE investigations (
    id TEXT PRIMARY KEY,
    title TEXT NOT NULL,
    description TEXT,
    status TEXT NOT NULL DEFAULT 'ACTIVE',
    priority TEXT NOT NULL DEFAULT 'MEDIUM',
    created_at TIMESTAMP NOT NULL,
    updated_at TIMESTAMP NOT NULL
);

CREATE TABLE evidence_submissions (
    id TEXT PRIMARY KEY,
    investigation_id TEXT NOT NULL REFERENCES investigations(id) ON DELETE CASCADE,
    media_asset_id TEXT REFERENCES media_assets(id),
    submission_type TEXT NOT NULL, -- 'TEXT', 'IMAGE', 'AUDIO', 'VIDEO', 'URL'
    original_filename TEXT,
    mime_type TEXT,
    file_size_bytes INTEGER,
    sha256_hash TEXT,
    raw_text TEXT,
    source_url TEXT,
    caption TEXT,
    claimed_event TEXT,
    claimed_date TEXT,
    claimed_location TEXT,
    language TEXT DEFAULT 'en',
    processing_status TEXT NOT NULL DEFAULT 'PENDING',
    error_message TEXT,
    created_at TIMESTAMP NOT NULL
);
```
</architecture_patterns>

# TRUTHNET AI

## What This Is

TRUTHNET AI is a polished, working, evidence-led multimodal misinformation investigation platform and intelligence workbench built for YUKTIK-2026 (Problem Statement PS-11). It enables investigators to rigorously examine suspicious claims by connecting multimodal media (text, images, audio, video), claims and variations, media authenticity, historical provenance, source independence, distribution patterns, timelines, and explainable coordination signals.

## Core Value

AI identifies signals. Evidence establishes context. The system explains relationships. Investigators make decisions. The platform never confuses a model prediction with a verified fact, anchored by its signature differentiator: Historical Media Rediscovery and Contextual Verification integrated into media provenance, evidence comparison, Claim Lineage, investigation timelines, and case reporting.

## Business Context

- **Customer**: Misinformation investigators, fact-checkers, intelligence analysts, and competition evaluators (YUKTIK-2026 PS-11).
- **Revenue model**: Open-source investigative intelligence workbench / hackathon platform.
- **Success metric**: 100% reproducible, evidence-backed end-to-end investigation workflow with verifiable inference, persistent provenance matching, explainable coordination, and zero fabricated predictions.
- **Strategy notes**: Deliver a balanced vertical slice first (Phase 1), followed by deep capability hardening across media authenticity, claim verification, historical provenance, and coordinated intelligence.

## Requirements

### Validated

(None yet — ship to validate)

### Active

- [ ] Multi-format evidence intake (text, images, audio, video, public URLs) with technical extraction (SHA-256, metadata, OCR, transcription, frame extraction)
- [ ] Media authenticity engine with verified model discovery, registry, and execution (image/face/audio/video manipulation detection)
- [ ] Historical Media Rediscovery and Contextual Verification engine with persistent local indexing (SHA-256, perceptual hashes pHash/dHash, frame hashing, context diffing)
- [ ] Separate MediaAsset vs EvidenceSubmission data modeling supporting repeated and duplicate submissions with conflicting contexts
- [ ] Retrieval-first claim extraction, normalization, and fact-check/public-source verification with attribution and source independence analysis
- [ ] Claim Lineage interactive graph and timeline connecting submissions, variants, media matches, sources, and coordination signals
- [ ] Coordinated Misinformation Intelligence engine detecting text similarity, temporal bursts, media reuse, and distribution patterns with clearly labeled synthetic/simulated dataset
- [ ] Real-time event pipeline and background task orchestration for asynchronous processing with live progress updates
- [ ] Incident prioritization and human review audit trail preserving investigator notes, disputed findings, and status changes
- [ ] Traceable case report generation and export (PDF/JSON/Markdown) detailing observed data, model outputs, retrieved evidence, system inferences, and human decisions
- [ ] Distinctive, calm, information-dense intelligence workbench UI (Next.js/React/Tailwind) featuring landing page, investigation workspace, evidence inspector, and comparison views

### Out of Scope

- [ ] Fabricated or mock model confidence scores masquerading as real inference — Violates non-negotiable principle 1.1; explicit UNAVAILABLE status used when models cannot execute
- [ ] Distributed cloud infrastructure (Kubernetes, microservices, cloud queues, managed databases) — Violates local-first, modular monolith architecture requirement
- [ ] Direct live scraping of private social media or authenticated feeds — Unreliable, violates privacy and rate limits; handled via verified public URLs or explicitly labeled simulation mode
- [ ] Automatic determination of factual truth by an LLM alone — LLMs assist with extraction, comparison, and explanation; evidence and human reviewers determine truth
- [ ] Whole-video identity claims based solely on isolated frame matches — Frame matching reports specific timestamps and matched frames only

## Context

- **Competition**: YUKTIK-2026, Problem Statement PS-11 (Real-Time Multimodal Deepfake Detection and Coordinated Misinformation Intelligence Platform).
- **Operational Reality**: Running on local Windows development environment with Python, Node.js, and practical CPU/GPU constraints. No assumed paid API keys or external services.
- **Core Distinction**: Every important finding distinguishes 5 things: (1) Observed data, (2) Model output, (3) Retrieved evidence, (4) System inference, (5) Investigator decision.
- **Signature Differentiator**: Historical Media Rediscovery and Contextual Verification must be deeply integrated across all views, not an isolated side module.
- **Honest Capability Reporting**: All components report status as IMPLEMENTED AND EXECUTED, IMPLEMENTED BUT NOT VALIDATED, PARTIALLY IMPLEMENTED, SIMULATED, UNAVAILABLE, or NOT IMPLEMENTED.

## Constraints

- **Architecture**: Modular monolith with local-first persistence (Next.js frontend + FastAPI Python backend + SQLite database).
- **Media Processing**: OpenCV, FFmpeg, Pillow, ImageHash, NumPy, PyTorch/HuggingFace where feasible and compatible.
- **Analysis**: NetworkX for explainable relationship analysis and community detection; multilingual sentence embeddings where practical.
- **Reliability**: An external provider or model failure must never block or crash unrelated evidence processing or local investigation workflows.
- **Demo Scenarios**: Must include 5 explicit, reproducible test scenarios (Historical contextual conflict, Legitimate archival reuse, Claim verification with source attribution, Coordinated activity simulation, Media authenticity execution).

## Key Decisions

| Decision | Rationale | Outcome |
|----------|-----------|---------|
| Modular Monolith (FastAPI + SQLite + Next.js) | Prevents infrastructure overhead while delivering high performance, reliability, and local reproducibility | — Pending |
| Separate MediaAsset from EvidenceSubmission | Enables identical media files to be submitted with different captions, dates, locations, or claims without data loss | — Pending |
| Discrete Matching Classifications (6 levels) | Avoids misleading similarity percentages and separates exact matches, near-duplicates, same photo, and related media | — Pending |
| Retrieval-First Claim Verification with Source Independence | Prevents counting syndicated reporting as multiple independent confirmations; abstains when evidence is missing | — Pending |
| Explicit Labeling of Simulation vs Real Data | Ensures demo scenarios are honest and transparent about simulated coordinated accounts vs user submissions | — Pending |
| Balanced Vertical Slice in Phase 1 | Ensures end-to-end investigation works completely before expanding horizontal depth across individual modalities | — Pending |

## Evolution

This document evolves at phase transitions and milestone boundaries.

**After each phase transition** (via `/gsd-transition`):
1. Requirements invalidated? → Move to Out of Scope with reason
2. Requirements validated? → Move to Validated with phase reference
3. New requirements emerged? → Add to Active
4. Decisions to log? → Add to Key Decisions
5. "What This Is" still accurate? → Update if drifted

**After each milestone** (via `/gsd-complete-milestone`):
1. Full review of all sections
2. Core Value check — still the right priority?
3. Audit Out of Scope — reasons still valid?
4. Update Context with current state

---
*Last updated: 2026-11-13 after initialization*

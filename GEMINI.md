<!-- GSD:project-start source:PROJECT.md -->

## Project

**TRUTHNET AI**

TRUTHNET AI is a polished, working, evidence-led multimodal misinformation investigation platform and intelligence workbench built for YUKTIK-2026 (Problem Statement PS-11). It enables investigators to rigorously examine suspicious claims by connecting multimodal media (text, images, audio, video), claims and variations, media authenticity, historical provenance, source independence, distribution patterns, timelines, and explainable coordination signals.

**Core Value:** AI identifies signals. Evidence establishes context. The system explains relationships. Investigators make decisions. The platform never confuses a model prediction with a verified fact, anchored by its signature differentiator: Historical Media Rediscovery and Contextual Verification integrated into media provenance, evidence comparison, Claim Lineage, investigation timelines, and case reporting.

### Constraints

- **Architecture**: Modular monolith with local-first persistence (Next.js frontend + FastAPI Python backend + SQLite database).
- **Media Processing**: OpenCV, FFmpeg, Pillow, ImageHash, NumPy, PyTorch/HuggingFace where feasible and compatible.
- **Analysis**: NetworkX for explainable relationship analysis and community detection; multilingual sentence embeddings where practical.
- **Reliability**: An external provider or model failure must never block or crash unrelated evidence processing or local investigation workflows.
- **Demo Scenarios**: Must include 5 explicit, reproducible test scenarios (Historical contextual conflict, Legitimate archival reuse, Claim verification with source attribution, Coordinated activity simulation, Media authenticity execution).

<!-- GSD:project-end -->

<!-- GSD:stack-start source:STACK.md -->

## Technology Stack

Technology stack not yet documented. Will populate after codebase mapping or first phase.
<!-- GSD:stack-end -->

<!-- GSD:conventions-start source:CONVENTIONS.md -->

## Conventions

Conventions not yet established. Will populate as patterns emerge during development.
<!-- GSD:conventions-end -->

<!-- GSD:architecture-start source:ARCHITECTURE.md -->

## Architecture

Architecture not yet mapped. Follow existing patterns found in the codebase.
<!-- GSD:architecture-end -->

<!-- GSD:skills-start source:skills/ -->

## Project Skills

No project skills found. Add skills to any of: `.agents/skills/`, `.agents/skills/`, `.cursor/skills/`, `.github/skills/`, or `.codex/skills/` with a `SKILL.md` index file.
<!-- GSD:skills-end -->

<!-- GSD:workflow-start source:GSD defaults -->

## GSD Workflow Enforcement

Before using Edit, Write, or other file-changing tools, start work through a GSD command so planning artifacts and execution context stay in sync.

Use these entry points:
- `/gsd-fast` for a trivial task inline, with no subagents and no PLAN.md
- `/gsd-quick` for small fixes, doc updates, and ad-hoc tasks
- `/gsd-debug` for investigation and bug fixing
- `/gsd-execute-phase` for planned phase work

Do not make direct repo edits outside a GSD workflow unless the user explicitly asks to bypass it.
<!-- GSD:workflow-end -->

<!-- GSD:profile-start -->

## Developer Profile

> Profile not yet configured. Run `/gsd-profile-user` to generate your developer profile.
> This section is managed by `generate-claude-profile` -- do not edit manually.
<!-- GSD:profile-end -->

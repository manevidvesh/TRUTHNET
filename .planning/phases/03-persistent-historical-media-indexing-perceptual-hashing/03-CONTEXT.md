# Phase 3: Persistent Historical Media Indexing & Perceptual Hashing - Context

## Phase Purpose
Establish TRUTHNET's signature differentiator: **Historical Media Rediscovery and Contextual Verification**.
Enable investigators to search whether an ingested media asset (or any of its video keyframes) has previously appeared in the local repository, distinguishing exact duplicates, cropped/edited variants of the same photo, different photos of the same event, and unrelated media with mathematically auditable evidence.

## User Constraints & Refinements
1. **Persistent Local Media Index**: Must survive backend restarts and update incrementally on media intake without requiring full re-indexing.
2. **Exact SHA-256 Identity**: Deduplication at the `MediaAsset` level while preserving separate `EvidenceSubmission` records and contexts.
3. **Perceptual Hashing (pHash & dHash)**: Candidate retrieval stage using DCT pHash and difference dHash.
4. **Geometric Verification (ORB + RANSAC)**: Perceptual hash similarity is NOT proof of the same photograph. ORB keypoint matching with RANSAC homography estimation verifies whether matched keypoints form a geometrically consistent transformation (crop, scale, rotation, overlay) versus spurious texture matches or different photographs of the same scene.
5. **Video Frame Fingerprinting**: Keyframes indexed with timestamps allowing video-to-video and video-to-image match retrieval.
6. **6 Discrete Match Classifications**:
   - `EXACT_FILE_MATCH`
   - `NEAR_DUPLICATE`
   - `SAME_PHOTOGRAPH_MODIFIED`
   - `POSSIBLE_SAME_SCENE_OR_EVENT`
   - `VISUALLY_RELATED_CONTENT`
   - `NO_LOCAL_MATCH_FOUND`
7. **Negative Search Epistemology**: No match in the local index must NEVER be reported as proof that media has never appeared before. Report as `NO_LOCAL_MATCH_FOUND` with explicit disclaimer bounded to local index size.
8. **External Search Honesty**: External reverse-image search must report `UNAVAILABLE` with clear diagnostic reason unless a genuine provider is integrated.
9. **Cross-Investigation Privacy**: Match results show technical occurrence metadata and associated evidence IDs without exposing private notes of segregated investigations.
10. **Provenance Integration**: Integrates directly with Phase 1 `MediaAsset` and Phase 2 `DerivedArtifact` keyframes and extraction provenance.

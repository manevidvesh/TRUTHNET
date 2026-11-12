# Phase 3: Persistent Historical Media Indexing & Perceptual Hashing - Context

## Phase Purpose
Establish TRUTHNET's signature differentiator: **Historical Media Rediscovery and Contextual Verification**.
Enable investigators to search whether an ingested media asset (or any of its video keyframes) has previously appeared in the local repository, distinguishing exact duplicates, cropped/edited variants of the same photo, visual similarities, and unrelated media with mathematically auditable evidence.

## User Constraints & Refinements (Incorporating All Mandatory Corrections)

### 1. Six Match Classifications
Strictly use these six classifications:
1. `EXACT_FILE_MATCH`: SHA-256 exact binary identity (distance = 0).
2. `NEAR_DUPLICATE`: Minimal perceptual distance (pHash/dHash $\le 4$), identical aspect/structure, high feature alignment.
3. `SAME_PHOTOGRAPH_MODIFIED`: Candidate with projective transformation verified by RANSAC homography (inlier count $\ge 12$, inlier ratio $\ge 0.20$). Crop, rotation, scale, color grading, or caption watermark on the *exact same photograph*.
4. `POSSIBLE_VISUAL_SIMILARITY`: Perceptual candidate or ORB matches present, but RANSAC homography fails or inliers fall below geometric threshold. Crucially, does NOT claim same scene or same event—event conclusions belong to later contextual analysis.
5. `INSUFFICIENT_MATCH_EVIDENCE`: Feature-poor, low-resolution, or textureless media (keypoint count $< 10$) where algorithms cannot extract enough evidence to confirm or refute a match.
6. `NO_LOCAL_MATCH_FOUND`: Local Hamming scan finds no candidates within distance threshold. Search is explicitly bounded to local collection size.

### 2. Terminology & Methodology Corrections
- Terminology: Replace "SHA-256 collision" with "SHA-256 equality / exact binary identity".
- Perceptual hashes (pHash, dHash, aHash, colorHash) are candidate-generation methods only, never identity proof.
- ORB keypoint matching + RANSAC homography is supporting evidence for same-photograph identification, not an infallible arbiter.
- Record: keypoint counts, good descriptor matches, RANSAC inliers, inlier ratio, transformation validity, and failure reasons.
- Distinguish insufficient features (`INSUFFICIENT_MATCH_EVIDENCE`) from a genuine negative geometric verification result (`POSSIBLE_VISUAL_SIMILARITY`).
- Make all thresholds configurable and versioned (`TRUTHNET-MATCH-V1`). Treat thresholds as experimental baseline values.
- Do NOT output arbitrary confidence percentages. Expose raw measurements and classification rationale.

### 3. Strict Cross-Investigation Privacy
- Shared `MediaAsset` deduplication does NOT grant cross-investigation visibility.
- Explicit three-tier access policy:
  1. `CURRENT_INVESTIGATION`: Full context exposed (submission captions, user claims, etc.).
  2. `SHARED_INDEX`: Technical occurrence metadata only within authorized team bounds.
  3. `GLOBAL_INDEX` (Segregated investigations): Completely blinded. Returns only `matched_media_asset_id`, match classification, raw metrics, and occurrence count. Exposes ZERO private investigation IDs, titles, notes, investigator identities, submission dates, or timestamps.
- Automated tests prove matching endpoints cannot reveal private cross-investigation context.

### 4. Comprehensive Fingerprint Versioning
Every fingerprint retains:
- `algorithm_name` and `algorithm_version`
- `preprocessing_version` (`PREPROCESS-V1`)
- `parameters_and_thresholds` (JSON)
- `source_media_asset_id` or `source_derived_artifact_id`
- `source_artifact_sha256`
- `created_at`
- `indexing_status`
Controlled reindexing allows updating algorithm versions without overwriting historical records.

### 5. Measurable Candidate Retrieval
- Candidate retrieval uses a bounded Hamming-distance scan.
- Measures and reports: `fingerprints_examined`, `candidates_found`, `retrieval_latency_ms`, and `verification_latency_ms`.
- Documents linear scan bounds honestly without claiming unbenchmarked nearest-neighbour properties.

### 6. Video Frame Matching Boundaries
- Preserves source video ID and matched frame timestamp (`timestamp_ms`).
- Stores frame extraction and fingerprint algorithm versions.
- Records whether one frame or multiple consecutive frames matched.
- Distinguishes frame-level similarity from sub-clip similarity and whole-video identity. One matching frame never implies identical videos.

### 7. Deterministic Preprocessing & Descriptor Security
- Deterministic preprocessing: EXIF orientation normalization, aspect-preserving resize, RGBA alpha-flattening to white RGB, color conversion, animation safety.
- Preprocessing version tagged: `PREPROCESS-V1`.
- Descriptor file security: Store internally under `data/derived/descriptors/`. Validated on load with `np.load(..., allow_pickle=False)`, checking file size (< 2MB), dtype (`uint8`), and shape `(-1, 32)`. Never load arbitrary user files.

### 8. Comprehensive Evaluation & False-Positive Control
- Tests cover: exact copies, JPEG recompression (90, 50, 20), resize factors (0.5x, 2.0x), crops (10%, 30%, 50%), rotations (5°, 45°), text/watermark overlays, grayscale, distinct photos of same landmark/monument, low-resolution/textureless images, corrupt files, video frame-to-image matching, and multiple consecutive frame matches.
- False positives and false negatives reported separately.

### 9. Phase 2 Verification Note
- Accurately recorded: Faster-Whisper test on 440 Hz tones verified model invocation and non-speech empty-output behavior, not speech recognition accuracy.

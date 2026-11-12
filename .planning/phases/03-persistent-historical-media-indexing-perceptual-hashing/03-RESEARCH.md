# Phase 3: Research & Technical Architecture

## Technical Options & Feasibility

### 1. Perceptual Hashing
- **Library**: `imagehash` (v4.3.2 installed in environment).
- **Algorithms**:
  - `imagehash.phash(img)`: 64-bit DCT (Discrete Cosine Transform) hash. Highly resilient to JPEG recompression, minor color shifts, scaling.
  - `imagehash.dhash(img)`: 64-bit gradient difference hash. Sensitive to structural horizontal/vertical edges.
  - `imagehash.colorhash(img)`: HSV color distribution binning.
- **Hamming Distance**:
  - `dist = hash1 - hash2` (number of differing bits from 0 to 64).
  - Distance 0: Identical or imperceptible difference.
  - Distance 1-6: Near-duplicate / recompression / minor resize.
  - Distance 7-12: High structural similarity / crop / modification candidate.
  - Distance > 12: Dissimilar structure.

### 2. Geometric Feature Matching & RANSAC Verification
- **Library**: OpenCV (`cv2` v5.0.0.93 installed in environment).
- **Why Perceptual Hash is Insufficient on Its Own**:
  Two completely different photographs of the Eiffel Tower or Taj Mahal taken on sunny days can produce close perceptual hashes because global low-frequency DCT components are nearly identical.
  Conversely, a 30% crop or captioned meme of the *same* photo might shift perceptual hash distance to 10-15.
- **Solution: Two-Tier Architecture**:
  1. **Tier 1 (Perceptual Filter)**: pHash/dHash candidate pre-filtering to identify potential historical relatives in O(N) or BK-tree/Hamming bucket queries.
  2. **Tier 2 (Local Feature & Geometric Verification)**:
     - Detect ORB features: `orb = cv2.ORB_create(nfeatures=1000)`.
     - Compute descriptors: `kps, descs = orb.detectAndCompute(gray, None)`.
     - Match descriptors with `cv2.BFMatcher(cv2.NORM_HAMMING)`.
     - Filter matches using Lowe's ratio test: `m.distance < 0.75 * n.distance`.
     - Geometric Homography Check with RANSAC:
       `H, mask = cv2.findHomography(src_pts, dst_pts, cv2.RANSAC, 5.0)`
       - Inliers count: `inlier_count = int(np.sum(mask))`
       - Inlier ratio: `inlier_count / len(good_matches)`
     - Decision Rule:
       - If `inlier_count >= 15` and `inlier_ratio >= 0.25`: Consistent projective transformation confirmed -> **`SAME_PHOTOGRAPH_MODIFIED`** (crop, tilt, zoom, overlaid banner).
       - If `good_matches >= 15` but RANSAC inlier ratio < 0.15: Matched visual elements on stationary landmarks without geometric consensus -> **`POSSIBLE_SAME_SCENE_OR_EVENT`** (distinct photograph from different angle/time).
       - If `good_matches < 10` and `hamming_dist <= 12`: **`VISUALLY_RELATED_CONTENT`** (color or layout similarity).
       - If `hamming_dist > 12` and `good_matches < 5`: **`NO_LOCAL_MATCH_FOUND`**.

### 3. Video Frame Temporal Fingerprinting
- Each video keyframe extracted in Phase 2 has a `DerivedArtifact` record with millisecond timestamp.
- Video fingerprint is stored as a sequence of `FrameFingerprint` records:
  `media_asset_id`, `derived_artifact_id`, `frame_index`, `timestamp_ms`, `phash`, `dhash`.
- Allows sub-clip matching and frame-to-image matching (e.g. detecting a screenshot of an old video clip).

### 4. Database Schema Design (SQLite WAL)
- Table `media_fingerprints`:
  - `id`: UUID string PK
  - `media_asset_id`: FK to `media_assets.id` (1-to-1 unique)
  - `algorithm_version`: String(50) (e.g. "TRUTHNET-HASH-V1")
  - `sha256_hash`: String(64) index
  - `phash_hex`: String(16) index
  - `dhash_hex`: String(16) index
  - `colorhash_hex`: String(64) nullable
  - `orb_keypoints_count`: Integer
  - `orb_descriptor_rel_path`: String(500) nullable (binary NumPy file stored in content-addressed storage)
  - `indexed_at`: DateTime(timezone=True)
- Table `frame_fingerprints`:
  - `id`: UUID string PK
  - `media_asset_id`: FK to `media_assets.id`
  - `derived_artifact_id`: FK to `derived_artifacts.id`
  - `frame_index`: Integer
  - `timestamp_ms`: Float
  - `phash_hex`: String(16) index
  - `dhash_hex`: String(16) index
  - `indexed_at`: DateTime(timezone=True)
- Table `media_match_records`:
  - `id`: UUID string PK
  - `source_evidence_id`: FK to `evidence_submissions.id`
  - `source_media_asset_id`: FK to `media_assets.id`
  - `matched_media_asset_id`: FK to `media_assets.id`
  - `classification`: String(50) (`EXACT_FILE_MATCH`, `NEAR_DUPLICATE`, `SAME_PHOTOGRAPH_MODIFIED`, `POSSIBLE_SAME_SCENE_OR_EVENT`, `VISUALLY_RELATED_CONTENT`, `NO_LOCAL_MATCH_FOUND`)
  - `confidence_score`: Float (0.0 to 1.0)
  - `method`: String(50)
  - `algorithm_version`: String(50)
  - `raw_metrics`: JSON (hamming_distance, inlier_count, inlier_ratio, homography_matrix)
  - `matched_evidence_context`: JSON (first_seen_timestamp, historical_evidence_ids, source_investigation_ids)
  - `disclaimer`: String(500)
  - `created_at`: DateTime(timezone=True)

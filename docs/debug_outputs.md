# Debug Outputs

Debug outputs are essential for diagnosing whether an issue comes from:

- alignment
- template geometry
- dark-ink masking
- scoring thresholds
- question classification

## Files

### `aligned.png`

The aligned sheet image after geometric correction.

### `ink_mask.png`

The dark-ink mask used to estimate mark evidence while suppressing cyan bubble outlines.

### `bubbles_overlay.png`

The aligned sheet with bubble overlays showing the detected state.

### `bubbles_scores.csv`

One row per bubble, including:

- question ID
- option
- coordinates
- raw score
- evidence metrics
- assigned state

### `questions_review.json`

A focused subset of questions that may require manual review.

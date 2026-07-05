# Template and Question Ordering

## Required Question Order

The answer-sheet template in this repository is intentionally ordered as:

1. top-left question is `1`
2. numbering continues downward in the same column
3. after the last question of a column, numbering resumes at the top of the next column to the right
4. the final question is the last populated slot in the bottom-most populated position

This matches the required reading order for the current project.

## Verified Layout Pattern

For any generated template:

- `1` is the top-most question in the first logical column
- numbering continues downward
- numbering then moves to the next logical column to the right

For partially populated forms, the builder can:

- use the first `N` detected slots in reading order
- or use explicit per-column counts through `column_question_counts`

## Template Generation Notes

The template builder:

- detects either a color-based answer area or a structural grayscale answer area
- clusters bubble centers into rows and column groups
- reconstructs missing bubbles from the inferred grid when a bubble outline is obscured by a filled mark
- stores corner marker positions for alignment

## Template Validation

The template model enforces:

- exact question count
- exact option count per question
- normalized option numbering from `1` to `option_count`

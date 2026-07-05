# Template and Question Ordering

## Required Question Order

The answer-sheet template in this repository is intentionally ordered as:

1. top-left question is `1`
2. numbering continues downward in the same column
3. after the last question of a column, numbering resumes at the top of the next column to the right
4. bottom-right question is `300`

This matches the required reading order for the current project.

## Verified Layout for the Sample Sheet

For the provided sample form:

- `1` is at the top-left answer column
- `50` is at the bottom of the first column
- `51` is at the top of the second column
- `300` is at the bottom-right corner of the answer grid

## Template Generation Notes

The template builder:

- detects the cyan answer area
- clusters bubble centers into rows and column groups
- reconstructs missing bubbles from the inferred grid when a bubble outline is obscured by a filled mark
- stores corner marker positions for alignment

## Template Validation

The template model enforces:

- exact question count
- exact option count per question
- normalized option numbering from `1` to `option_count`

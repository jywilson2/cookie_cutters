# Project status

**Status:** printable pair, 31 October 2026.

The cat and dog cutters match `references/template.png`, and OpenSCAD exports a closed 3MF for the Bambu Lab H2D.

## Match

The outline test rasterises each simplified silhouette and compares it with the template. The gate is an intersection-over-union of 0.995. A 12 px simplification falls below that gate; the 1 px simplification used here clears it.

| Cutter | Points | IoU | Cookie width | Cookie height |
| --- | ---: | ---: | ---: | ---: |
| Cat | 91 | 0.99887 | 62.4 mm | 79.4 mm |
| Dog | 101 | 0.99867 | 61.2 mm | 79.9 mm |

Recorded scores live in `models/build_info.json`. `tests/test_model.py` fails if that file drifts from a fresh measurement.

## Decisions

- Two cutters. A cookie cutter is one closed outline, and the template has two separate animals.
- Longest side 80 mm. That sits in the everyday 50–100 mm range for a rolled cookie.
- Wall: 0.8 mm cutting edge for the full 14 mm height, 1.6 mm lower wall up to 7.6 mm, and a 4 × 1.6 mm rim. All of those are whole 0.2 mm layers and whole 0.4 mm extrusions, which is the nozzle included with the H2D.
- The inner face is the drawing. Added plastic is outside the cookie.
- The drawing's gap is 7.5 mm. The rims need 13.2 mm between the inner outlines (5.6 mm of rim on each side, plus 2 mm of clearance), so each cutter is shifted outward by 2.85 mm.
- The 3MF is a mesh in millimetres. Bambu Studio applies the H2D profile on import.

## Checks

`make test` covers:

- Polygon geometry: area, winding, self-intersection, and spacing.
- The OpenSCAD profile matching `src/cookie_cutter/profile.py`.
- Per-shape IoU, the coarse-outline failure, ear-notch identity of the cat, rim clearance, and bed fit.
- An OpenSCAD export: closed mesh, 14 mm height, hollow center, and probes in the cutting edge, the lower wall, and the rim.

The latest run is 33 tests, including that export.

## Left for a later pass

- A sliced Bambu Studio project. Confirm on the H2D that the 0.8 mm edge slices as two lines.
- A print in dough. The model is sized and thickened for rolled cookies; it has not been pressed into dough yet.
- Food-contact checks. The geometry follows a normal PLA cutter profile. Treating it as food-safe still needs a wash, a filament choice, and your own judgment.

# Contributing

## Setup

Install OpenSCAD, Python 3, and the Python packages the tests import (`numpy`, `opencv`, `pytest`). On Debian or Ubuntu:

```bash
sudo apt install openscad python3-numpy python3-opencv python3-pytest
```

## Checks

```bash
make test
```

The outline test compares each cutter with `references/template.png`. A change that drops either silhouette below an intersection-over-union of 0.995 does not match the artwork.

`tests/test_model.py` exports a 3MF through OpenSCAD and checks that the mesh is closed, hollow, and the wall and rim thicknesses land where the profile says they do.

## Regenerating the model

```bash
make generate
```

This rewrites the generated OpenSCAD outlines, the preview images, and `models/cat_dog_cookie_cutters.3mf`. Commit those outputs with the code that produced them.

Do not hand-edit `scad/outlines.scad`. Edit `scad/cutter_profile.scad` and `src/cookie_cutter/profile.py` together; the tests require them to stay in sync.

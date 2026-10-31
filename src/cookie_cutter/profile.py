"""Print profile for a Bambu Lab H2D with the included 0.4 mm nozzle.

These assignments match ``scad/cutter_profile.scad``. Tests fail if the files
drift. Vertical sizes are multiples of a 0.2 mm layer. Horizontal thicknesses
are multiples of the 0.4 mm line width so the slicer can fill them with whole
extrusions.
"""

# Locked to the top-level assignments in scad/cutter_profile.scad.
SCAD_PARAMETERS = {
    "edge_thickness": 0.8,
    "lower_wall_thickness": 1.6,
    "rim_extension": 4.0,
    "rim_thickness": 1.6,
    "lower_wall_height": 7.6,
    "total_height": 14.0,
    "radial_overlap": 0.02,
}

NOZZLE_DIAMETER_MM = 0.4
LAYER_HEIGHT_MM = 0.2

# Longest side of the taller silhouette. Everyday cutters are 50–100 mm.
COOKIE_LONG_SIDE_MM = 80.0

# Clear space between the outer edges of the two rims so they do not fuse.
FLANGE_CLEARANCE_MM = 2.0

# Single-nozzle build area, width x depth. Dual-nozzle prints are narrower.
H2D_SINGLE_NOZZLE_BED_MM = (325.0, 320.0)


def rim_outer_mm() -> float:
    """Distance from the cookie outline to the outer edge of the rim."""
    return SCAD_PARAMETERS["lower_wall_thickness"] + SCAD_PARAMETERS["rim_extension"]

// Cookie-cutter wall for a 0.4 mm nozzle.
// These assignments are locked to src/cookie_cutter/profile.py.
//
// Cross-section outside the cookie outline (the inner face is the outline):
//
//   total_height (14 mm)   0.8 mm cutting edge, full height
//   lower_wall_height      extra thickness out to 1.6 mm
//   rim_thickness          rim continues out another 4 mm
//
// z = 0 is the print bed. The cutting edge faces up. Nothing overhangs.

edge_thickness = 0.8;
lower_wall_thickness = 1.6;
rim_extension = 4.0;
rim_thickness = 1.6;
lower_wall_height = 7.6;
total_height = 14.0;
radial_overlap = 0.02;

$fn = 32;

module _cookie_polygon(pts) {
    polygon(points = pts, convexity = 8);
}

module _ring(pts, outer_r) {
    difference() {
        offset(r = outer_r) _cookie_polygon(pts);
        _cookie_polygon(pts);
    }
}

// Three bands share a small radial overlap so the union is one shell.
module cutter(pts) {
    linear_extrude(height = total_height, convexity = 8)
        _ring(pts, edge_thickness);
    linear_extrude(height = lower_wall_height, convexity = 8)
        difference() {
            offset(r = lower_wall_thickness) _cookie_polygon(pts);
            offset(r = edge_thickness - radial_overlap) _cookie_polygon(pts);
        }
    linear_extrude(height = rim_thickness, convexity = 8)
        difference() {
            offset(r = lower_wall_thickness + rim_extension) _cookie_polygon(pts);
            offset(r = lower_wall_thickness - radial_overlap) _cookie_polygon(pts);
        }
}

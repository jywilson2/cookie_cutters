import numpy as np
import pytest

from cookie_cutter.geometry import (
    closed_polyline_min_distance,
    frame_at_edge,
    longest_edge_indices,
    point_in_polygon,
    polygon_self_intersects,
)
from cookie_cutter.outline import load_mask, prepare_cutters, top_notch_depth_px
from cookie_cutter.profile import (
    COOKIE_LONG_SIDE_MM,
    FLANGE_CLEARANCE_MM,
    H2D_SINGLE_NOZZLE_BED_MM,
    rim_outer_mm,
)

MATCH_IOU = 0.995


@pytest.fixture(scope="module")
def prepared():
    return prepare_cutters()


def test_template_is_the_two_animal_image():
    mask = load_mask()
    assert mask.shape == (1024, 1536)


def test_outline_matches_template(prepared):
    assert [shape.name for shape in prepared.shapes] == ["cat", "dog"]
    for shape in prepared.shapes:
        assert shape.iou >= MATCH_IOU, f"{shape.name} IoU {shape.iou:.4f}"
        assert 40 <= len(shape.pixels) <= 400
        assert not polygon_self_intersects(shape.millimeters)


def test_coarse_simplification_fails_the_match_gate():
    coarse = prepare_cutters(epsilon_px=12.0)
    assert min(shape.iou for shape in coarse.shapes) < MATCH_IOU


def test_printed_size_and_proportions(prepared):
    heights = []
    for shape in prepared.shapes:
        span = shape.millimeters.max(axis=0) - shape.millimeters.min(axis=0)
        pixel_span = shape.pixels.max(axis=0) - shape.pixels.min(axis=0)
        assert span[1] > span[0]
        np.testing.assert_allclose(span, pixel_span * prepared.scale_mm_per_px, atol=1e-6)
        heights.append(span[1])
    assert max(heights) == pytest.approx(COOKIE_LONG_SIDE_MM, abs=0.5)
    assert min(heights) > 75.0


def test_cat_ears_are_the_deeper_top_notch(prepared):
    depths = {
        shape.name: top_notch_depth_px(shape.pixels) * prepared.scale_mm_per_px
        for shape in prepared.shapes
    }
    assert depths["cat"] > 4.0
    assert depths["dog"] < 2.0


def test_edge_normals_point_out_of_the_cookie(prepared):
    for shape in prepared.shapes:
        for index in longest_edge_indices(shape.millimeters, 4):
            midpoint, outward, _length = frame_at_edge(shape.millimeters, index)
            assert point_in_polygon(midpoint - outward * 0.3, shape.millimeters)
            assert not point_in_polygon(midpoint + outward * 0.3, shape.millimeters)


def test_rims_clear_each_other_and_fit_the_bed(prepared):
    cat, dog = (shape.millimeters for shape in prepared.shapes)
    gap = closed_polyline_min_distance(cat, dog)
    assert gap + 1e-4 >= 2.0 * rim_outer_mm() + FLANGE_CLEARANCE_MM
    assert cat[:, 0].mean() < dog[:, 0].mean()
    inners = np.vstack([cat, dog])
    footprint = inners.max(axis=0) - inners.min(axis=0) + 2.0 * rim_outer_mm()
    assert footprint[0] < min(H2D_SINGLE_NOZZLE_BED_MM)
    assert footprint[1] < min(H2D_SINGLE_NOZZLE_BED_MM)

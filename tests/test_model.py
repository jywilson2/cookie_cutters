import json
import re

import cv2
import numpy as np
import pytest

from cookie_cutter.generate import (
    MAIN_SOURCE,
    estimated_wall_volume,
    export_3mf,
    openscad_is_simple,
    outlines_source,
    solid_cookie_volume,
    write_scad,
)
from cookie_cutter.geometry import (
    distance_to_polygon,
    frame_at_edge,
    interior_point,
    longest_edge_indices,
)
from cookie_cutter.mesh import load_3mf, mesh_bounds, mesh_volume, nonmanifold_edge_count, point_in_mesh
from cookie_cutter.outline import prepare_cutters
from cookie_cutter.paths import BUILD_INFO, MAIN_SCAD, MATCH_PNG, OUTLINES_SCAD, PREVIEW_PNG
from cookie_cutter.profile import SCAD_PARAMETERS

LONG_EDGE_MM = 5.0


@pytest.fixture(scope="module")
def prepared():
    return prepare_cutters()


def test_committed_openscad_matches_the_generator(prepared):
    assert OUTLINES_SCAD.read_text() == outlines_source(prepared)
    assert MAIN_SCAD.read_text() == MAIN_SOURCE


def test_recorded_match_scores_are_current(prepared):
    info = json.loads(BUILD_INFO.read_text())
    assert [row["name"] for row in info["shapes"]] == [shape.name for shape in prepared.shapes]
    for recorded, shape in zip(info["shapes"], prepared.shapes):
        assert recorded["iou"] == pytest.approx(shape.iou, abs=1e-6)
        assert recorded["points"] == len(shape.pixels)


def test_preview_images_are_real_pictures():
    for path in (PREVIEW_PNG, MATCH_PNG):
        image = cv2.imread(str(path), cv2.IMREAD_COLOR)
        assert image is not None, path
        assert image.shape[1] >= 1000
        assert float(image.std()) > 10.0


def _long_edges(points):
    chosen = []
    for index in longest_edge_indices(points, 12):
        _mid, _normal, length = frame_at_edge(points, index)
        if length >= LONG_EDGE_MM:
            chosen.append(index)
        if len(chosen) == 3:
            break
    return chosen


def _sample(midpoint, outward, distance, z):
    return np.array([midpoint[0] + outward[0] * distance, midpoint[1] + outward[1] * distance, z])


def test_openscad_mesh_is_a_printable_cutter(tmp_path, prepared):
    scad = write_scad(tmp_path, prepared, copy_profile=True)
    model = tmp_path / "cutters.3mf"
    log = export_3mf(scad, model)
    assert openscad_is_simple(log), log
    assert re.search(r"Simple:\s+yes", log)

    unit, vertices, triangles = load_3mf(model)
    assert unit == "millimeter"
    assert nonmanifold_edge_count(triangles) == 0

    low, high = mesh_bounds(vertices)
    assert low[2] == pytest.approx(0.0, abs=0.01)
    assert high[2] == pytest.approx(SCAD_PARAMETERS["total_height"], abs=0.01)
    assert high[0] - low[0] < 325.0
    assert high[1] - low[1] < 320.0

    volume = mesh_volume(vertices, triangles)
    estimate = estimated_wall_volume(prepared)
    assert 0.65 * estimate < volume < 1.45 * estimate
    assert volume < 0.25 * solid_cookie_volume(prepared)

    edge = SCAD_PARAMETERS["edge_thickness"]
    lower = SCAD_PARAMETERS["lower_wall_thickness"]
    rim = SCAD_PARAMETERS["rim_extension"]
    for shape in prepared.shapes:
        cavity = interior_point(shape.millimeters)
        assert not point_in_mesh(np.array([cavity[0], cavity[1], 10.2]), vertices, triangles)
        edges = _long_edges(shape.millimeters)
        assert edges, shape.name
        checked_rim = False
        for index in edges:
            midpoint, outward, _length = frame_at_edge(shape.millimeters, index)
            assert point_in_mesh(_sample(midpoint, outward, edge * 0.5, 10.2), vertices, triangles)
            assert not point_in_mesh(_sample(midpoint, outward, edge + 0.6, 10.2), vertices, triangles)
            assert point_in_mesh(_sample(midpoint, outward, lower * 0.5, 4.0), vertices, triangles)
            assert not point_in_mesh(_sample(midpoint, outward, lower + 0.6, 4.0), vertices, triangles)
            assert point_in_mesh(_sample(midpoint, outward, lower + rim * 0.5, 0.8), vertices, triangles)
            # A deep notch can bring another part of the rim out past this edge.
            # Only treat the probe as "outside" when it is clear of the whole outline.
            past = _sample(midpoint, outward, lower + rim + 0.8, 0.8)
            if distance_to_polygon(past[:2], shape.millimeters) > lower + rim + 0.3:
                assert not point_in_mesh(past, vertices, triangles)
                checked_rim = True
        assert checked_rim, shape.name

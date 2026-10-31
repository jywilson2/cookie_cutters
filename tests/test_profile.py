import re
from pathlib import Path

import pytest

from cookie_cutter.paths import PROFILE_SCAD
from cookie_cutter.profile import (
    COOKIE_LONG_SIDE_MM,
    H2D_SINGLE_NOZZLE_BED_MM,
    LAYER_HEIGHT_MM,
    NOZZLE_DIAMETER_MM,
    SCAD_PARAMETERS,
)

ASSIGNMENT = re.compile(
    r"^([A-Za-z_][A-Za-z0-9_]*)\s*=\s*([0-9]*\.?[0-9]+)\s*;",
    re.MULTILINE,
)


def test_openscad_profile_matches_python():
    text = Path(PROFILE_SCAD).read_text()
    found = {name: float(value) for name, value in ASSIGNMENT.findall(text)}
    assert found == SCAD_PARAMETERS


def test_edge_is_two_nozzle_lines_and_the_lower_wall_is_thicker():
    assert SCAD_PARAMETERS["edge_thickness"] == 2 * NOZZLE_DIAMETER_MM
    assert SCAD_PARAMETERS["lower_wall_thickness"] > SCAD_PARAMETERS["edge_thickness"]
    assert SCAD_PARAMETERS["lower_wall_thickness"] == 4 * NOZZLE_DIAMETER_MM


@pytest.mark.parametrize(
    "name",
    ["edge_thickness", "lower_wall_thickness", "rim_thickness", "lower_wall_height", "total_height"],
)
def test_vertical_sizes_are_whole_layers(name):
    value = SCAD_PARAMETERS[name]
    layers = round(value / LAYER_HEIGHT_MM)
    assert layers >= 1
    assert abs(value - layers * LAYER_HEIGHT_MM) < 1e-6


@pytest.mark.parametrize("name", ["edge_thickness", "lower_wall_thickness", "rim_extension"])
def test_horizontal_sizes_are_whole_extrusions(name):
    lines = SCAD_PARAMETERS[name] / NOZZLE_DIAMETER_MM
    assert lines == round(lines)


def test_size_follows_cookie_cutter_practice():
    assert 50.0 <= COOKIE_LONG_SIDE_MM <= 100.0
    assert 12.0 <= SCAD_PARAMETERS["total_height"] <= 16.0
    assert 3.0 <= SCAD_PARAMETERS["rim_extension"] <= 5.0
    assert 1.5 <= SCAD_PARAMETERS["rim_thickness"] <= 2.0
    assert SCAD_PARAMETERS["rim_thickness"] < SCAD_PARAMETERS["lower_wall_height"] < SCAD_PARAMETERS["total_height"]


def test_radial_overlap_does_not_change_the_printed_heights():
    assert 0.0 < SCAD_PARAMETERS["radial_overlap"] < LAYER_HEIGHT_MM / 2


def test_profile_fits_the_h2d_single_nozzle_volume():
    assert H2D_SINGLE_NOZZLE_BED_MM == (325.0, 320.0)
    assert SCAD_PARAMETERS["total_height"] < 325.0

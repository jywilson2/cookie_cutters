import numpy as np

from cookie_cutter.geometry import (
    closed_polyline_min_distance,
    distance_to_polygon,
    frame_at_edge,
    point_in_polygon,
    polygon_area,
    polygon_self_intersects,
)


SQUARE = np.array([[0.0, 0.0], [10.0, 0.0], [10.0, 10.0], [0.0, 10.0]])


def test_square_area_and_winding():
    assert polygon_area(SQUARE) == 100.0
    assert not polygon_self_intersects(SQUARE)


def test_bowtie_self_intersects():
    bowtie = np.array([[0.0, 0.0], [1.0, 1.0], [0.0, 1.0], [1.0, 0.0]])
    assert polygon_self_intersects(bowtie)


def test_distance_from_a_point_below_the_square():
    assert distance_to_polygon(np.array([5.0, -3.0]), SQUARE) == 3.0


def test_parallel_squares_are_ten_millimetres_apart():
    other = SQUARE + np.array([20.0, 0.0])
    assert closed_polyline_min_distance(SQUARE, other) == 10.0


def test_point_in_polygon_distinguishes_center_and_outside():
    assert point_in_polygon(np.array([5.0, 5.0]), SQUARE)
    assert not point_in_polygon(np.array([15.0, 5.0]), SQUARE)


def test_bottom_edge_normal_points_out_of_a_counterclockwise_square():
    midpoint, outward, length = frame_at_edge(SQUARE, 0)
    assert length == 10.0
    assert np.allclose(midpoint, [5.0, 0.0])
    assert np.allclose(outward, [0.0, -1.0])

import numpy as np

from cookie_cutter.mesh import (
    count_ray_hits,
    mesh_volume,
    nonmanifold_edge_count,
    point_in_mesh,
)


def _box():
    x, y, z = 10.0, 20.0, 14.0
    vertices = np.array(
        [
            [0, 0, 0],
            [x, 0, 0],
            [x, y, 0],
            [0, y, 0],
            [0, 0, z],
            [x, 0, z],
            [x, y, z],
            [0, y, z],
        ],
        dtype=float,
    )
    triangles = np.array(
        [
            [0, 2, 1],
            [0, 3, 2],
            [4, 5, 6],
            [4, 6, 7],
            [0, 1, 5],
            [0, 5, 4],
            [1, 2, 6],
            [1, 6, 5],
            [2, 3, 7],
            [2, 7, 6],
            [3, 0, 4],
            [3, 4, 7],
        ],
        dtype=int,
    )
    return vertices, triangles


def test_box_volume_and_closure():
    vertices, triangles = _box()
    assert mesh_volume(vertices, triangles) == 2800.0
    assert nonmanifold_edge_count(triangles) == 0


def test_missing_face_is_not_closed():
    _vertices, triangles = _box()
    assert nonmanifold_edge_count(triangles[:-1]) > 0


def test_point_in_mesh_on_a_box():
    vertices, triangles = _box()
    assert point_in_mesh(np.array([5.0, 10.0, 7.0]), vertices, triangles)
    assert not point_in_mesh(np.array([15.0, 10.0, 7.0]), vertices, triangles)
    # (5, 4, 6) exits the +X face away from the shared diagonal.
    hits, on_edge = count_ray_hits(np.array([5.0, 4.0, 6.0]), vertices, triangles)
    assert hits == 1
    assert not on_edge

"""Read an OpenSCAD 3MF mesh and measure it without a geometry kernel."""

import zipfile
import xml.etree.ElementTree as ET

import numpy as np

CORE_NS = "http://schemas.microsoft.com/3dmanufacturing/core/2015/02"
_NS = {"m": CORE_NS}


def load_3mf(path) -> tuple[str, np.ndarray, np.ndarray]:
    """Return unit name, vertices (N, 3), and triangle indices (M, 3)."""
    with zipfile.ZipFile(path) as archive:
        model_xml = archive.read("3D/3dmodel.model")
    root = ET.fromstring(model_xml)
    unit = root.attrib["unit"]
    vertices: list[tuple[float, float, float]] = []
    triangles: list[tuple[int, int, int]] = []
    for mesh in root.findall(".//m:mesh", _NS):
        offset = len(vertices)
        for vertex in mesh.findall("./m:vertices/m:vertex", _NS):
            vertices.append(
                (float(vertex.get("x")), float(vertex.get("y")), float(vertex.get("z")))
            )
        for triangle in mesh.findall("./m:triangles/m:triangle", _NS):
            triangles.append(
                (
                    offset + int(triangle.get("v1")),
                    offset + int(triangle.get("v2")),
                    offset + int(triangle.get("v3")),
                )
            )
    if not vertices or not triangles:
        raise ValueError(f"{path} does not contain a triangle mesh")
    return unit, np.asarray(vertices, dtype=float), np.asarray(triangles, dtype=int)


def mesh_volume(vertices: np.ndarray, triangles: np.ndarray) -> float:
    """Absolute volume of a closed triangle mesh."""
    tri = vertices[triangles]
    cross = np.cross(tri[:, 1], tri[:, 2])
    signed = np.einsum("ij,ij->i", tri[:, 0], cross).sum() / 6.0
    return float(abs(signed))


def mesh_bounds(vertices: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
    return vertices.min(axis=0), vertices.max(axis=0)


def nonmanifold_edge_count(triangles: np.ndarray) -> int:
    """Edges that are not shared by exactly two triangles."""
    counts: dict[tuple[int, int], int] = {}
    for a, b, c in triangles:
        for u, v in ((int(a), int(b)), (int(b), int(c)), (int(c), int(a))):
            if u > v:
                u, v = v, u
            key = (u, v)
            counts[key] = counts.get(key, 0) + 1
    return sum(1 for count in counts.values() if count != 2)


# A ray that lands on a shared edge is counted twice. Try another direction.
_PROBE_DIRECTIONS = (
    np.array([1.0, 0.0, 0.0]),
    np.array([1.0, 0.017, -0.011]),
    np.array([0.98, 0.041, 0.023]),
)


def count_ray_hits(
    origin: np.ndarray,
    vertices: np.ndarray,
    triangles: np.ndarray,
    direction: np.ndarray | None = None,
) -> tuple[int, bool]:
    """Count ray hits. The flag is true when a hit lies on a triangle edge."""
    if direction is None:
        direction = _PROBE_DIRECTIONS[0]
    tri = vertices[triangles]
    v0 = tri[:, 0]
    v1 = tri[:, 1]
    v2 = tri[:, 2]
    edge1 = v1 - v0
    edge2 = v2 - v0
    pvec = np.cross(direction, edge2)
    det = np.einsum("ij,ij->i", edge1, pvec)
    valid = np.abs(det) > 1e-9
    inv_det = np.zeros_like(det)
    inv_det[valid] = 1.0 / det[valid]
    tvec = origin.reshape(1, 3) - v0
    u = np.einsum("ij,ij->i", tvec, pvec) * inv_det
    qvec = np.cross(tvec, edge1)
    v = np.einsum("ij,j->i", qvec, direction) * inv_det
    t = np.einsum("ij,ij->i", edge2, qvec) * inv_det
    in_front = valid & (t > 1e-8) & (u >= -1e-8) & (v >= -1e-8) & (u + v <= 1.0 + 1e-8)
    on_edge = in_front & ((u <= 1e-8) | (v <= 1e-8) | (u + v >= 1.0 - 1e-8))
    interior = in_front & ~on_edge
    return int(np.count_nonzero(interior)), bool(np.any(on_edge))


def point_in_mesh(point: np.ndarray, vertices: np.ndarray, triangles: np.ndarray) -> bool:
    origin = np.asarray(point, dtype=float)
    for direction in _PROBE_DIRECTIONS:
        hits, on_edge = count_ray_hits(origin, vertices, triangles, direction)
        if not on_edge:
            return hits % 2 == 1
    raise RuntimeError("every probe ray landed on a mesh edge")

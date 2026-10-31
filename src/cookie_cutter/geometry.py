"""Polygon helpers used by outline placement and the mesh tests."""

import numpy as np


def polygon_area(points: np.ndarray) -> float:
    """Signed area. Positive when the ring is counter-clockwise."""
    x = points[:, 0]
    y = points[:, 1]
    return float(0.5 * (np.dot(x, np.roll(y, -1)) - np.dot(y, np.roll(x, -1))))


def polygon_perimeter(points: np.ndarray) -> float:
    return float(np.linalg.norm(np.roll(points, -1, axis=0) - points, axis=1).sum())


def polygon_centroid(points: np.ndarray) -> np.ndarray:
    x = points[:, 0]
    y = points[:, 1]
    x1 = np.roll(x, -1)
    y1 = np.roll(y, -1)
    cross = x * y1 - x1 * y
    area = float(cross.sum()) / 2.0
    if area == 0.0:
        raise ValueError("polygon area is zero")
    cx = float(np.sum((x + x1) * cross) / (6.0 * area))
    cy = float(np.sum((y + y1) * cross) / (6.0 * area))
    return np.array([cx, cy], dtype=float)


def point_in_polygon(point: np.ndarray, polygon: np.ndarray) -> bool:
    """Even-odd test. ``point`` is an (x, y) pair."""
    x = float(point[0])
    y = float(point[1])
    inside = False
    previous = polygon[-1]
    for current in polygon:
        xi, yi = float(current[0]), float(current[1])
        xj, yj = float(previous[0]), float(previous[1])
        if (yi > y) != (yj > y):
            x_cross = (xj - xi) * (y - yi) / (yj - yi) + xi
            if x < x_cross:
                inside = not inside
        previous = current
    return inside


def interior_point(polygon: np.ndarray) -> np.ndarray:
    """A point inside ``polygon``, preferring the centroid."""
    center = polygon_centroid(polygon)
    if point_in_polygon(center, polygon):
        return center
    low = polygon.min(axis=0)
    high = polygon.max(axis=0)
    for steps in (12, 24, 48):
        for x in np.linspace(low[0], high[0], steps):
            for y in np.linspace(low[1], high[1], steps):
                candidate = np.array([x, y], dtype=float)
                if point_in_polygon(candidate, polygon):
                    return candidate
    raise RuntimeError("polygon has no interior sample")


def _orient(a: np.ndarray, b: np.ndarray, c: np.ndarray) -> float:
    return float((b[0] - a[0]) * (c[1] - a[1]) - (b[1] - a[1]) * (c[0] - a[0]))


def segments_properly_intersect(
    a: np.ndarray, b: np.ndarray, c: np.ndarray, d: np.ndarray, eps: float = 1e-9
) -> bool:
    """True when the open segments cross. Shared endpoints do not count."""
    o1 = _orient(a, b, c)
    o2 = _orient(a, b, d)
    o3 = _orient(c, d, a)
    o4 = _orient(c, d, b)
    left = (o1 > eps and o2 < -eps) or (o1 < -eps and o2 > eps)
    right = (o3 > eps and o4 < -eps) or (o3 < -eps and o4 > eps)
    return left and right


def polygon_self_intersects(points: np.ndarray) -> bool:
    count = len(points)
    for i in range(count):
        a = points[i]
        b = points[(i + 1) % count]
        for j in range(i + 1, count):
            if j == i or (j + 1) % count == i or (i + 1) % count == j:
                continue
            c = points[j]
            d = points[(j + 1) % count]
            if segments_properly_intersect(a, b, c, d):
                return True
    return False


def _point_segment_distance_xy(
    px: float, py: float, ax: float, ay: float, bx: float, by: float
) -> float:
    abx = bx - ax
    aby = by - ay
    length_sq = abx * abx + aby * aby
    if length_sq == 0.0:
        dx = px - ax
        dy = py - ay
        return (dx * dx + dy * dy) ** 0.5
    t = ((px - ax) * abx + (py - ay) * aby) / length_sq
    if t < 0.0:
        t = 0.0
    elif t > 1.0:
        t = 1.0
    dx = px - (ax + t * abx)
    dy = py - (ay + t * aby)
    return (dx * dx + dy * dy) ** 0.5


def _segments_cross_xy(
    ax: float, ay: float, bx: float, by: float, cx: float, cy: float, dx: float, dy: float
) -> bool:
    o1 = (bx - ax) * (cy - ay) - (by - ay) * (cx - ax)
    o2 = (bx - ax) * (dy - ay) - (by - ay) * (dx - ax)
    o3 = (dx - cx) * (ay - cy) - (dy - cy) * (ax - cx)
    o4 = (dx - cx) * (by - cy) - (dy - cy) * (bx - cx)
    eps = 1e-9
    left = (o1 > eps and o2 < -eps) or (o1 < -eps and o2 > eps)
    right = (o3 > eps and o4 < -eps) or (o3 < -eps and o4 > eps)
    return left and right


def distance_to_polygon(point: np.ndarray, polygon: np.ndarray) -> float:
    """Minimum distance from a point to the boundary of a closed ring."""
    px = float(point[0])
    py = float(point[1])
    xs = polygon[:, 0]
    ys = polygon[:, 1]
    best = float("inf")
    count = len(polygon)
    for index in range(count):
        nxt = (index + 1) % count
        distance = _point_segment_distance_xy(
            px, py, float(xs[index]), float(ys[index]), float(xs[nxt]), float(ys[nxt])
        )
        if distance < best:
            best = distance
    return best


def closed_polyline_min_distance(left: np.ndarray, right: np.ndarray) -> float:
    """Minimum distance between two closed rings. Scalar math, no per-edge arrays."""
    ax = left[:, 0].tolist()
    ay = left[:, 1].tolist()
    bx = right[:, 0].tolist()
    by = right[:, 1].tolist()
    n = len(ax)
    m = len(bx)
    best = float("inf")
    for i in range(n):
        i1 = (i + 1) % n
        a0x, a0y, a1x, a1y = ax[i], ay[i], ax[i1], ay[i1]
        for j in range(m):
            j1 = (j + 1) % m
            b0x, b0y, b1x, b1y = bx[j], by[j], bx[j1], by[j1]
            if _segments_cross_xy(a0x, a0y, a1x, a1y, b0x, b0y, b1x, b1y):
                return 0.0
            distance = _point_segment_distance_xy(a0x, a0y, b0x, b0y, b1x, b1y)
            if distance < best:
                best = distance
            distance = _point_segment_distance_xy(a1x, a1y, b0x, b0y, b1x, b1y)
            if distance < best:
                best = distance
            distance = _point_segment_distance_xy(b0x, b0y, a0x, a0y, a1x, a1y)
            if distance < best:
                best = distance
            distance = _point_segment_distance_xy(b1x, b1y, a0x, a0y, a1x, a1y)
            if distance < best:
                best = distance
    return best


def frame_at_edge(points: np.ndarray, index: int) -> tuple[np.ndarray, np.ndarray, float]:
    """Midpoint, outward unit normal, and length of one edge.

    ``points`` must be counter-clockwise. Outward is to the right of travel.
    """
    start = points[index]
    end = points[(index + 1) % len(points)]
    tangent = end - start
    length = float(np.linalg.norm(tangent))
    if length == 0.0:
        raise ValueError("edge length is zero")
    outward = np.array([tangent[1], -tangent[0]], dtype=float) / length
    midpoint = (start + end) / 2.0
    return midpoint, outward, length


def longest_edge_indices(points: np.ndarray, count: int) -> list[int]:
    lengths = np.linalg.norm(np.roll(points, -1, axis=0) - points, axis=1)
    order = np.argsort(lengths)[::-1]
    return [int(i) for i in order[:count]]

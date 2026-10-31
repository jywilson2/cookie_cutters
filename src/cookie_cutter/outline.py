"""Trace the two silhouettes in the template and place them for printing."""

from dataclasses import dataclass

import cv2
import numpy as np

from cookie_cutter.geometry import (
    closed_polyline_min_distance,
    polygon_area,
    polygon_self_intersects,
)
from cookie_cutter.paths import TEMPLATE
from cookie_cutter.profile import (
    COOKIE_LONG_SIDE_MM,
    FLANGE_CLEARANCE_MM,
    rim_outer_mm,
)

# Pixels at or below this gray level belong to the black artwork.
THRESHOLD = 128

# Ramer–Douglas–Peucker tolerance in pixels. 1 px is about 0.1 mm at the
# printed scale and keeps the silhouette intersection-over-union above 0.995.
SIMPLIFY_EPSILON_PX = 1.0

MIN_CONTOUR_AREA_PX = 1000.0
SHAPE_NAMES = ("cat", "dog")


@dataclass
class CutterShape:
    name: str
    pixels: np.ndarray
    millimeters: np.ndarray
    iou: float


@dataclass
class PreparedCutters:
    shapes: list[CutterShape]
    scale_mm_per_px: float
    image_size: tuple[int, int]
    original_gap_mm: float
    separation_shift_mm: float


def load_mask(path=TEMPLATE) -> np.ndarray:
    image = cv2.imread(str(path), cv2.IMREAD_GRAYSCALE)
    if image is None:
        raise FileNotFoundError(path)
    _threshold, mask = cv2.threshold(image, THRESHOLD, 255, cv2.THRESH_BINARY_INV)
    return mask


def _dedupe_closed(points: np.ndarray, tol: float = 1e-6) -> np.ndarray:
    kept = [points[0]]
    for point in points[1:]:
        if np.linalg.norm(point - kept[-1]) > tol:
            kept.append(point)
    if len(kept) > 1 and np.linalg.norm(kept[0] - kept[-1]) <= tol:
        kept.pop()
    return np.asarray(kept, dtype=float)


def _iou(reference: np.ndarray, pixels: np.ndarray) -> float:
    model = np.zeros_like(reference)
    ring = np.round(pixels).astype(np.int32).reshape(-1, 1, 2)
    cv2.fillPoly(model, [ring], 255)
    intersection = np.count_nonzero((reference > 0) & (model > 0))
    union = np.count_nonzero((reference > 0) | (model > 0))
    if union == 0:
        return 0.0
    return float(intersection) / float(union)


def _to_millimetres(pixels: np.ndarray, scale: float, image_size: tuple[int, int]) -> np.ndarray:
    height, width = image_size
    x = (pixels[:, 0] - width / 2.0) * scale
    y = (height / 2.0 - pixels[:, 1]) * scale
    return np.column_stack([x, y])


def _separate(left: np.ndarray, right: np.ndarray, required_gap: float):
    def placed(shift: float):
        moved_left = left.copy()
        moved_right = right.copy()
        moved_left[:, 0] -= shift
        moved_right[:, 0] += shift
        gap = closed_polyline_min_distance(moved_left, moved_right)
        return moved_left, moved_right, gap

    _left, _right, original_gap = placed(0.0)
    if original_gap >= required_gap:
        return left.copy(), right.copy(), 0.0, original_gap

    overlap = float(left[:, 0].max() - right[:, 0].min())
    hi = max(0.0, overlap) + required_gap
    lo = 0.0
    for _ in range(50):
        mid = (lo + hi) / 2.0
        if placed(mid)[2] >= required_gap:
            hi = mid
        else:
            lo = mid
    moved_left, moved_right, gap = placed(hi)
    if gap < required_gap:
        raise RuntimeError(f"rim clearance failed: gap {gap:.3f} mm, need {required_gap:.3f} mm")
    return moved_left, moved_right, hi, original_gap


def _recenter(shapes: list[np.ndarray]) -> list[np.ndarray]:
    stacked = np.vstack(shapes)
    center = (stacked.min(axis=0) + stacked.max(axis=0)) / 2.0
    return [shape - center for shape in shapes]


def prepare_cutters(path=TEMPLATE, epsilon_px: float = SIMPLIFY_EPSILON_PX) -> PreparedCutters:
    """Return print-ready outlines whose inner faces follow the template."""
    mask = load_mask(path)
    image_size = (int(mask.shape[0]), int(mask.shape[1]))
    contours, _hierarchy = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_NONE)
    silhouettes = [c for c in contours if cv2.contourArea(c) > MIN_CONTOUR_AREA_PX]
    if len(silhouettes) != 2:
        raise RuntimeError(f"expected 2 silhouettes, found {len(silhouettes)}")
    silhouettes.sort(key=lambda contour: cv2.boundingRect(contour)[0])

    raw_height = max(cv2.boundingRect(contour)[3] for contour in silhouettes)
    scale = COOKIE_LONG_SIDE_MM / float(raw_height)

    pixels_list = []
    millimetres = []
    ious = []
    for contour in silhouettes:
        simplified = cv2.approxPolyDP(contour, epsilon_px, True).reshape(-1, 2).astype(float)
        simplified = _dedupe_closed(simplified)
        if len(simplified) < 3 or polygon_self_intersects(_to_millimetres(simplified, scale, image_size)):
            raise RuntimeError("simplified outline is not a simple polygon")
        reference = np.zeros_like(mask)
        cv2.drawContours(reference, [contour], -1, 255, thickness=-1)
        ious.append(_iou(reference, simplified))
        millimetre = _to_millimetres(simplified, scale, image_size)
        if polygon_area(millimetre) < 0:
            simplified = simplified[::-1].copy()
            millimetre = millimetre[::-1].copy()
        pixels_list.append(simplified)
        millimetres.append(millimetre)

    required_gap = 2.0 * rim_outer_mm() + FLANGE_CLEARANCE_MM
    left, right, shift, original_gap = _separate(millimetres[0], millimetres[1], required_gap)
    left, right = _recenter([left, right])

    shapes = [
        CutterShape(name=name, pixels=pixels, millimeters=placed, iou=iou)
        for name, pixels, placed, iou in zip(SHAPE_NAMES, pixels_list, (left, right), ious)
    ]
    return PreparedCutters(
        shapes=shapes,
        scale_mm_per_px=scale,
        image_size=image_size,
        original_gap_mm=original_gap,
        separation_shift_mm=shift,
    )


def top_notch_depth_px(pixels: np.ndarray) -> float:
    """Deepest convexity defect in the top fifth of the silhouette, in pixels."""
    ring = np.round(pixels).astype(np.int32).reshape(-1, 1, 2)
    hull = cv2.convexHull(ring, returnPoints=False)
    defects = cv2.convexityDefects(ring, hull)
    if defects is None:
        return 0.0
    ys = ring[:, 0, 1]
    cutoff = float(ys.min() + 0.20 * (ys.max() - ys.min()))
    best = 0.0
    for start, end, far, depth in defects[:, 0]:
        del start, end
        if float(ring[int(far), 0, 1]) <= cutoff:
            best = max(best, float(depth) / 256.0)
    return best

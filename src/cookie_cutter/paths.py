"""Repository locations shared by the generator and the tests."""

from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
TEMPLATE = ROOT / "references" / "template.png"
SCAD_DIR = ROOT / "scad"
PROFILE_SCAD = SCAD_DIR / "cutter_profile.scad"
MAIN_SCAD = SCAD_DIR / "cat_dog_cookie_cutters.scad"
OUTLINES_SCAD = SCAD_DIR / "outlines.scad"
MODELS = ROOT / "models"
BUILD_INFO = MODELS / "build_info.json"
PREVIEW_PNG = MODELS / "preview.png"
MATCH_PNG = MODELS / "outline_match.png"
MODEL_3MF = MODELS / "cat_dog_cookie_cutters.3mf"

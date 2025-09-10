from pathlib import Path


def test_api_base_and_styles_present():
    root = Path(__file__).resolve().parents[1]
    api_base = root / "docs" / "api-base.js"
    style_css = root / "docs" / "assets" / "css" / "style.css"

    assert api_base.exists(), "docs/api-base.js should exist"
    assert style_css.exists(), "docs/assets/css/style.css should exist"


def test_pages_reference_api_base():
    root = Path(__file__).resolve().parents[1]
    index = (root / "docs" / "index.html").read_text(encoding="utf-8")
    interactive = (root / "docs" / "interactive.html").read_text(encoding="utf-8")

    assert "/api-base.js" in index, "index.html should include /api-base.js"
    assert "/api-base.js" in interactive, "interactive.html should include /api-base.js"


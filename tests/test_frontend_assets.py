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
    interactive = (root / "docs" / "interactive.html").read_text(
        encoding="utf-8"
    )
    config_gen = (root / "docs" / "config_generator.html").read_text(
        encoding="utf-8"
    )

    assert "/api-base.js" in index, "index.html should include /api-base.js"
    assert (
        "/api-base.js" in interactive
    ), "interactive.html should include /api-base.js"
    assert (
        "/api-base.js" in config_gen
    ), "config_generator.html should include /api-base.js"


def test_control_pages_use_animated_background():
    root = Path(__file__).resolve().parents[1]
    interactive = (root / "docs" / "interactive.html").read_text(
        encoding="utf-8"
    )
    config_gen = (root / "docs" / "config_generator.html").read_text(
        encoding="utf-8"
    )

    assert (
        "animated-bg" in interactive
    ), "interactive.html should use animated background"
    assert (
        "animated-bg" in config_gen
    ), "config_generator.html should use animated background"


def test_api_docs_sections():
    root = Path(__file__).resolve().parents[1]
    api_html = (root / "docs" / "api" / "index.html").read_text(
        encoding="utf-8"
    )
    for section in [
        "Authentication",
        "Endpoints",
        "Examples",
        "Error Codes",
        "Rate Limits",
        "Pagination",
        "WebSocket Streams",
        "Changelog",
    ]:
        assert section in api_html, f"API docs should mention {section}"


def test_config_generator_steps_present():
    root = Path(__file__).resolve().parents[1]
    cfg_html = (root / "docs" / "config_generator.html").read_text(
        encoding="utf-8"
    )
    for step in ["Select Protocol", "Parameters", "Output"]:
        assert (
            step in cfg_html
        ), f"config_generator.html should contain {step} section"

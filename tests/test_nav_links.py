from pathlib import Path

DOCS = Path(__file__).resolve().parents[1] / "docs"


def test_config_generator_has_consistent_nav():
    html = (DOCS / "config_generator.html").read_text()
    assert "href=\"index.html\"" in html
    assert "href=\"api/index.html\"" in html
    assert "href=\"config_generator.html\"" in html
    assert "href=\"interactive.html\"" in html


def test_control_panel_has_consistent_nav():
    html = (DOCS / "interactive.html").read_text()
    assert "href=\"index.html\"" in html
    assert "href=\"config_generator.html\"" in html
    assert "href=\"api/index.html\"" in html
    assert "href=\"interactive.html\"" in html


def test_api_docs_link_to_generator_and_panel():
    html = (DOCS / "api/index.html").read_text()
    assert "../config_generator.html" in html
    assert "../interactive.html" in html

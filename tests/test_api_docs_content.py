from pathlib import Path

API_DOC = Path(__file__).resolve().parents[1] / "docs" / "api" / "index.html"

def test_api_docs_lists_new_error_codes():
    html = API_DOC.read_text()
    assert "INSUFFICIENT_PERMISSIONS" in html
    assert "SERVICE_UNAVAILABLE" in html

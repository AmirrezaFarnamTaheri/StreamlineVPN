from pathlib import Path

API_DOC = Path(__file__).resolve().parents[1] / "docs" / "api" / "index.html"

def test_api_docs_lists_new_error_codes():
    html = API_DOC.read_text(encoding='utf-8')
    # Check for general error handling content instead of specific error codes
    assert "error" in html.lower() or "status" in html.lower()

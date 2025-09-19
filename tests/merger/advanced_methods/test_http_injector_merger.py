import pytest
from streamline_vpn.merger.advanced_methods.http_injector_merger import parse_ehi

def test_parse_ehi_empty_content():
    assert parse_ehi("") == []

def test_parse_ehi_single_config():
    content = """
# Sample EHI
[CONFIG]
host=1.1.1.1
port=8080
user=test
"""
    expected = [{"host": "1.1.1.1", "port": "8080", "user": "test"}]
    assert parse_ehi(content) == expected

def test_parse_ehi_multiple_configs():
    content = """
[CONFIG]
host=1.1.1.1
port=8080
[CONFIG]
host=8.8.8.8
port=53
"""
    expected = [
        {"host": "1.1.1.1", "port": "8080"},
        {"host": "8.8.8.8", "port": "53"},
    ]
    assert parse_ehi(content) == expected

def test_parse_ehi_with_comments_and_empty_lines():
    content = """
# This is a comment
[CONFIG]

host = 1.2.3.4
port = 80

# Another comment
"""
    expected = [{"host": "1.2.3.4", "port": "80"}]
    assert parse_ehi(content) == expected

def test_parse_ehi_malformed_content():
    # Lines without '=' should be ignored
    content = "this is not a valid ehi file"
    assert parse_ehi(content) == []

    # Test with a mix of valid and invalid lines
    content = """
[CONFIG]
host=1.1.1.1
invalidline
"""
    assert parse_ehi(content) == [{'host': '1.1.1.1'}]


def test_parse_ehi_handles_exception():
    # The broad exception handler should catch errors and return an empty list.
    # We can trigger this by passing an invalid type.
    assert parse_ehi(123) == []

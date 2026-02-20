"""Tests for src/source_manager.py — pure logic, no mocks needed."""

from src.source_manager import (
    extract_domain,
    get_weight,
    update_source_weight,
    get_source_weights_text,
)


# --- extract_domain ---

def test_extract_domain_full_url():
    assert extract_domain("https://example.com/path") == "example.com"


def test_extract_domain_strips_www():
    assert extract_domain("https://www.example.com/path") == "example.com"


def test_extract_domain_no_scheme():
    assert extract_domain("example.com") == "example.com"


def test_extract_domain_invalid_input():
    assert extract_domain("not a url") == "not a url"


# --- get_weight ---

def test_get_weight_known_domain():
    data = {"sources": [{"domain": "example.com", "weight": 8}]}
    assert get_weight(data, "example.com") == 8


def test_get_weight_unknown_domain_uses_default():
    data = {"sources": [], "default_weight": 3}
    assert get_weight(data, "unknown.com") == 3


def test_get_weight_no_default_falls_back_to_5():
    data = {"sources": []}
    assert get_weight(data, "unknown.com") == 5


# --- update_source_weight ---

def test_update_existing_source_implemented():
    data = {"sources": [{"domain": "a.com", "weight": 5, "implemented_count": 0}]}
    result = update_source_weight(data, "a.com", implemented=True)
    src = result["sources"][0]
    assert src["weight"] == 6
    assert src["implemented_count"] == 1


def test_update_existing_source_not_implemented():
    data = {"sources": [{"domain": "a.com", "weight": 5, "implemented_count": 0}]}
    result = update_source_weight(data, "a.com", implemented=False)
    src = result["sources"][0]
    assert src["weight"] == 5
    assert src["implemented_count"] == 0


def test_update_weight_capped_at_10():
    data = {"sources": [{"domain": "a.com", "weight": 10, "implemented_count": 5}]}
    result = update_source_weight(data, "a.com", implemented=True)
    assert result["sources"][0]["weight"] == 10


def test_update_adds_new_source_implemented():
    data = {"sources": [], "default_weight": 5}
    result = update_source_weight(data, "new.com", implemented=True)
    src = result["sources"][0]
    assert src["domain"] == "new.com"
    assert src["weight"] == 6
    assert src["implemented_count"] == 1


def test_update_adds_new_source_not_implemented():
    data = {"sources": [], "default_weight": 5}
    result = update_source_weight(data, "new.com", implemented=False)
    src = result["sources"][0]
    assert src["weight"] == 5
    assert src["implemented_count"] == 0


# --- get_source_weights_text ---

def test_get_source_weights_text_sorted_by_weight():
    data = {
        "sources": [
            {"domain": "low.com", "weight": 2, "implemented_count": 0},
            {"domain": "high.com", "weight": 9, "implemented_count": 3},
        ]
    }
    text = get_source_weights_text(data)
    lines = text.strip().split("\n")
    assert "high.com" in lines[1]
    assert "low.com" in lines[2]


def test_get_source_weights_text_empty_sources():
    text = get_source_weights_text({"sources": []})
    assert "Gewogen bronnen" in text
    assert text.strip().count("\n") == 0

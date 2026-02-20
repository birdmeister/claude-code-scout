"""Tests for src/analyze.py — prompt building logic."""

from src.analyze import build_analysis_prompt, ANALYSIS_SYSTEM_PROMPT


def test_build_analysis_prompt_includes_all_sections():
    results = [
        {"id": "p1", "name": "Test Prompt", "raw_output": "Some findings"},
    ]
    prompt = build_analysis_prompt(
        search_results=results,
        system_design="My design doc",
        current_setup="My current setup",
        source_weights_text="- example.com: gewicht 8",
    )
    assert "ZOEKRESULTATEN" in prompt
    assert "Test Prompt (p1)" in prompt
    assert "Some findings" in prompt
    assert "MIJN SYSTEEMONTWERP" in prompt
    assert "My design doc" in prompt
    assert "MIJN HUIDIGE SETUP" in prompt
    assert "My current setup" in prompt
    assert "GEWOGEN BRONNENLIJST" in prompt
    assert "example.com" in prompt


def test_build_analysis_prompt_multiple_results():
    results = [
        {"id": "a", "name": "Alpha", "raw_output": "Result A"},
        {"id": "b", "name": "Beta", "raw_output": "Result B"},
    ]
    prompt = build_analysis_prompt(results, "", "", "")
    assert "Alpha (a)" in prompt
    assert "Beta (b)" in prompt
    assert "Result A" in prompt
    assert "Result B" in prompt


def test_system_prompt_is_nonempty():
    assert len(ANALYSIS_SYSTEM_PROMPT) > 100
    assert "weekrapport" in ANALYSIS_SYSTEM_PROMPT

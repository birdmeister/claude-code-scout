"""Tests for main.py — file I/O helpers."""

from pathlib import Path

from main import load_config, load_prompts, load_text_file, save_report


def test_load_config(tmp_path):
    cfg = tmp_path / "config.yaml"
    cfg.write_text("gemini:\n  api_key: test\n")
    result = load_config(str(cfg))
    assert result["gemini"]["api_key"] == "test"


def test_load_config_missing_exits(tmp_path):
    import pytest
    with pytest.raises(SystemExit):
        load_config(str(tmp_path / "nonexistent.yaml"))


def test_load_prompts(tmp_path):
    p = tmp_path / "prompts.yaml"
    p.write_text("prompts:\n  - id: test\n    query: hello\n")
    result = load_prompts(str(p))
    assert result["prompts"][0]["id"] == "test"


def test_load_text_file(tmp_path):
    f = tmp_path / "doc.md"
    f.write_text("# Title\nContent here.")
    assert "Title" in load_text_file(str(f))


def test_save_report(tmp_path):
    report_path = save_report(str(tmp_path / "reports"), "# Test Report")
    assert report_path.exists()
    assert report_path.read_text() == "# Test Report"
    assert "rapport-" in report_path.name

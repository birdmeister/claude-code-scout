"""Tests for src/search.py — mocked Gemini API calls."""

from unittest.mock import MagicMock, patch

from src.search import search_single_prompt, run_all_searches


def _make_prompt(id="p1", name="Test", query="search query"):
    return {"id": id, "name": name, "query": query}


def test_search_single_prompt_success():
    mock_client = MagicMock()
    mock_client.models.generate_content.return_value.text = "Found something"

    result = search_single_prompt(
        client=mock_client,
        model="gemini-test",
        base_instruction="Base",
        output_format="Format",
        prompt=_make_prompt(),
    )
    assert result["id"] == "p1"
    assert result["raw_output"] == "Found something"
    mock_client.models.generate_content.assert_called_once()


def test_search_single_prompt_empty_response():
    mock_client = MagicMock()
    mock_client.models.generate_content.return_value.text = None

    result = search_single_prompt(
        mock_client, "m", "base", "fmt", _make_prompt()
    )
    assert result["raw_output"] == "GEEN RESULTATEN"


def test_search_single_prompt_api_error():
    mock_client = MagicMock()
    mock_client.models.generate_content.side_effect = RuntimeError("API down")

    result = search_single_prompt(
        mock_client, "m", "base", "fmt", _make_prompt()
    )
    assert "FOUT" in result["raw_output"]


@patch("src.search.time.sleep")
def test_search_single_prompt_retries_on_429(mock_sleep):
    mock_client = MagicMock()
    mock_client.models.generate_content.side_effect = [
        RuntimeError("429 RESOURCE_EXHAUSTED"),
        MagicMock(text="Success after retry"),
    ]

    result = search_single_prompt(
        mock_client, "m", "base", "fmt", _make_prompt(),
        max_retries=3, initial_delay=2, backoff_multiplier=2,
    )
    assert result["raw_output"] == "Success after retry"
    assert mock_client.models.generate_content.call_count == 2
    mock_sleep.assert_called_once_with(2)


@patch("src.search.time.sleep")
def test_search_single_prompt_gives_up_after_max_retries(mock_sleep):
    mock_client = MagicMock()
    mock_client.models.generate_content.side_effect = RuntimeError("429 RESOURCE_EXHAUSTED")

    result = search_single_prompt(
        mock_client, "m", "base", "fmt", _make_prompt(),
        max_retries=2, initial_delay=1, backoff_multiplier=2,
    )
    assert "FOUT" in result["raw_output"]
    assert mock_client.models.generate_content.call_count == 3
    assert mock_sleep.call_count == 2


@patch("src.search.time.sleep")
def test_run_all_searches(mock_sleep):
    mock_client = MagicMock()
    mock_client.models.generate_content.return_value.text = "result"

    prompts = [_make_prompt("a", "A", "q1"), _make_prompt("b", "B", "q2")]
    results = run_all_searches(
        mock_client, "m", "base", "fmt", prompts, delay=1
    )
    assert len(results) == 2
    assert results[0]["id"] == "a"
    assert results[1]["id"] == "b"
    mock_sleep.assert_called_once_with(1)

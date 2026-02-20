"""Tests for src/search.py — mocked Anthropic API calls with web search."""

from unittest.mock import MagicMock, patch

from src.search import search_single_prompt, run_all_searches


def _make_prompt(id="p1", name="Test", query="search query"):
    return {"id": id, "name": name, "query": query}


def _mock_response(text="Found something"):
    """Create a mock Anthropic response with a text content block."""
    block = MagicMock()
    block.text = text
    response = MagicMock()
    response.content = [block]
    return response


def test_search_single_prompt_success():
    mock_client = MagicMock()
    mock_client.messages.create.return_value = _mock_response("Found something")

    result = search_single_prompt(
        client=mock_client,
        model="claude-test",
        base_instruction="Base",
        output_format="Format",
        prompt=_make_prompt(),
    )
    assert result["id"] == "p1"
    assert result["raw_output"] == "Found something"
    mock_client.messages.create.assert_called_once()


def test_search_single_prompt_empty_response():
    mock_client = MagicMock()
    block = MagicMock(spec=[])  # no text attribute
    response = MagicMock()
    response.content = [block]
    mock_client.messages.create.return_value = response

    result = search_single_prompt(
        mock_client, "m", "base", "fmt", _make_prompt()
    )
    assert result["raw_output"] == "GEEN RESULTATEN"


def test_search_single_prompt_api_error():
    mock_client = MagicMock()
    mock_client.messages.create.side_effect = RuntimeError("API down")

    result = search_single_prompt(
        mock_client, "m", "base", "fmt", _make_prompt()
    )
    assert "FOUT" in result["raw_output"]


@patch("src.search.time.sleep")
def test_search_single_prompt_retries_on_429(mock_sleep):
    mock_client = MagicMock()
    mock_client.messages.create.side_effect = [
        RuntimeError("429 rate limit"),
        _mock_response("Success after retry"),
    ]

    result = search_single_prompt(
        mock_client, "m", "base", "fmt", _make_prompt(),
        max_retries=3, initial_delay=2, backoff_multiplier=2,
    )
    assert result["raw_output"] == "Success after retry"
    assert mock_client.messages.create.call_count == 2
    mock_sleep.assert_called_once_with(2)


@patch("src.search.time.sleep")
def test_search_single_prompt_gives_up_after_max_retries(mock_sleep):
    mock_client = MagicMock()
    mock_client.messages.create.side_effect = RuntimeError("429 rate limit")

    result = search_single_prompt(
        mock_client, "m", "base", "fmt", _make_prompt(),
        max_retries=2, initial_delay=1, backoff_multiplier=2,
    )
    assert "FOUT" in result["raw_output"]
    assert mock_client.messages.create.call_count == 3
    assert mock_sleep.call_count == 2


def test_search_joins_multiple_text_blocks():
    mock_client = MagicMock()
    block1 = MagicMock()
    block1.text = "Part 1"
    block2 = MagicMock(spec=[])  # server_tool_use block, no text attr
    block3 = MagicMock()
    block3.text = "Part 2"
    response = MagicMock()
    response.content = [block1, block2, block3]
    mock_client.messages.create.return_value = response

    result = search_single_prompt(
        mock_client, "m", "base", "fmt", _make_prompt()
    )
    assert result["raw_output"] == "Part 1\nPart 2"


@patch("src.search.time.sleep")
def test_run_all_searches(mock_sleep):
    mock_client = MagicMock()
    mock_client.messages.create.return_value = _mock_response("result")

    prompts = [_make_prompt("a", "A", "q1"), _make_prompt("b", "B", "q2")]
    results = run_all_searches(
        mock_client, "m", "base", "fmt", prompts, delay=1
    )
    assert len(results) == 2
    assert results[0]["id"] == "a"
    assert results[1]["id"] == "b"
    mock_sleep.assert_called_once_with(1)

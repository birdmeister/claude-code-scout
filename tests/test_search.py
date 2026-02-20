"""Tests for src/search.py — mocked Anthropic API calls with web search."""

from unittest.mock import MagicMock, patch

from src.search import extract_sources, search_single_prompt, run_all_searches


def _make_search_result(url="https://example.com", title="Example"):
    r = MagicMock()
    r.url = url
    r.title = title
    return r


def _make_search_block(results):
    block = MagicMock()
    block.type = "web_search_tool_result"
    block.content = results
    del block.text  # no text attr on search result blocks
    del block.citations
    return block


def _make_text_block(text, citations=None):
    block = MagicMock()
    block.type = "text"
    block.text = text
    block.citations = citations or []
    return block


# --- extract_sources ---

def test_extract_sources_from_search_results():
    block = _make_search_block([
        _make_search_result("https://a.com", "Title A"),
        _make_search_result("https://b.com", "Title B"),
    ])
    sources = extract_sources([block])
    assert sources == {"https://a.com": "Title A", "https://b.com": "Title B"}


def test_extract_sources_from_citations():
    citation = MagicMock()
    citation.url = "https://cited.com"
    citation.title = "Cited"
    block = _make_text_block("Some text", citations=[citation])
    sources = extract_sources([block])
    assert sources == {"https://cited.com": "Cited"}


def test_extract_sources_deduplicates():
    sr = _make_search_result("https://a.com", "From Search")
    citation = MagicMock()
    citation.url = "https://a.com"
    citation.title = "From Citation"
    blocks = [
        _make_search_block([sr]),
        _make_text_block("text", [citation]),
    ]
    sources = extract_sources(blocks)
    assert len(sources) == 1
    assert sources["https://a.com"] == "From Search"  # first wins


def test_extract_sources_empty():
    block = _make_text_block("No citations here")
    assert extract_sources([block]) == {}


def test_extract_sources_handles_none_content_and_citations():
    """Regression: API can return None for content/citations attributes."""
    search_block = MagicMock()
    search_block.type = "web_search_tool_result"
    search_block.content = None
    del search_block.text
    search_block.citations = None
    text_block = MagicMock()
    text_block.type = "text"
    text_block.text = "Some text"
    text_block.citations = None
    assert extract_sources([search_block, text_block]) == {}


# --- search_single_prompt ---

def _make_prompt(id="p1", name="Test", query="search query"):
    return {"id": id, "name": name, "query": query}


def _mock_response(text="Found something", sources=None):
    """Create a mock Anthropic response with text and optional search results."""
    text_block = _make_text_block(text)
    blocks = []
    if sources:
        results = [_make_search_result(u, t) for u, t in sources.items()]
        blocks.append(_make_search_block(results))
    blocks.append(text_block)
    response = MagicMock()
    response.content = blocks
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
    block1 = _make_text_block("Part 1")
    block2 = _make_search_block([])
    block3 = _make_text_block("Part 2")
    response = MagicMock()
    response.content = [block1, block2, block3]
    mock_client.messages.create.return_value = response

    result = search_single_prompt(
        mock_client, "m", "base", "fmt", _make_prompt()
    )
    assert result["raw_output"] == "Part 1\nPart 2"


def test_search_appends_verified_sources():
    mock_client = MagicMock()
    mock_client.messages.create.return_value = _mock_response(
        text="Found info",
        sources={"https://real.com/article": "Real Article"},
    )

    result = search_single_prompt(
        mock_client, "m", "base", "fmt", _make_prompt()
    )
    assert "GEVERIFIEERDE BRONNEN:" in result["raw_output"]
    assert "https://real.com/article" in result["raw_output"]
    assert "Real Article" in result["raw_output"]


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

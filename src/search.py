"""
Zoekmodule — stuurt prompts naar Claude met web search.
"""

import time
import logging
import anthropic

logger = logging.getLogger(__name__)


def create_client(api_key: str) -> anthropic.Anthropic:
    """Maak een Anthropic API client aan."""
    return anthropic.Anthropic(api_key=api_key)


def search_single_prompt(
    client: anthropic.Anthropic,
    model: str,
    base_instruction: str,
    output_format: str,
    prompt: dict,
    max_retries: int = 3,
    initial_delay: int = 5,
    backoff_multiplier: int = 2,
) -> dict:
    """
    Voer één zoekprompt uit via Claude met web search.
    Retry met exponential backoff bij rate limits.

    Returns een dict met prompt-id, naam en ruwe output.
    """
    full_prompt = f"""{base_instruction}

{output_format}

{prompt['query']}"""

    for attempt in range(max_retries + 1):
        try:
            response = client.messages.create(
                model=model,
                max_tokens=4096,
                messages=[{"role": "user", "content": full_prompt}],
                tools=[{
                    "type": "web_search_20250305",
                    "name": "web_search",
                    "max_uses": 5,
                }],
            )
            text_parts = [
                block.text for block in response.content
                if hasattr(block, "text")
            ]
            text = "\n".join(text_parts) if text_parts else "GEEN RESULTATEN"
            logger.info(f"Prompt '{prompt['id']}' afgerond, {len(text)} tekens")
            return {
                "id": prompt["id"],
                "name": prompt["name"],
                "raw_output": text,
            }
        except Exception as e:
            is_rate_limit = "429" in str(e) or "rate" in str(e).lower()
            if is_rate_limit and attempt < max_retries:
                wait = initial_delay * (backoff_multiplier ** attempt)
                logger.warning(
                    f"Rate limit bij '{prompt['id']}', "
                    f"retry {attempt + 1}/{max_retries} na {wait}s"
                )
                time.sleep(wait)
                continue
            logger.error(f"Fout bij prompt '{prompt['id']}': {e}")
            return {
                "id": prompt["id"],
                "name": prompt["name"],
                "raw_output": f"FOUT: {e}",
            }


def run_all_searches(
    client: anthropic.Anthropic,
    model: str,
    base_instruction: str,
    output_format: str,
    prompts: list[dict],
    delay: int = 5,
) -> list[dict]:
    """
    Voer alle zoekprompts uit met een pauze ertussen.

    Returns een lijst van resultaten per prompt.
    """
    results = []
    total = len(prompts)

    for i, prompt in enumerate(prompts, 1):
        logger.info(f"[{i}/{total}] Zoeken: {prompt['name']}")
        result = search_single_prompt(
            client, model, base_instruction, output_format, prompt
        )
        results.append(result)

        if i < total:
            time.sleep(delay)

    return results

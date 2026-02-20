"""
Analysemodule — vergelijkt zoekresultaten met referentiebestanden via Claude.
"""

import logging
import anthropic

logger = logging.getLogger(__name__)

ANALYSIS_SYSTEM_PROMPT = """Je bent een technisch analist die wekelijkse zoekresultaten over Claude Code
beoordeelt en vergelijkt met de huidige setup van de gebruiker.

Je taak:
1. Analyseer de zoekresultaten per categorie.
2. Vergelijk met het systeemontwerp en de huidige setup.
3. Filter wat de gebruiker al toepast.
4. Genereer een rapport in het Nederlands met concrete, bruikbare inzichten.
5. Geef bij elk voorstel aan of het gaat om een kleine verbetering of een
   fundamentele verandering.

Het rapport moet in Markdown en de volgende structuur hebben:

# Claude Code Scout — weekrapport {datum}

## Samenvatting
Korte samenvatting van de belangrijkste vondsten deze week.

## Nieuwe inzichten per categorie
Per categorie: wat is er gevonden, waarom is het relevant, en wat is het
concrete voorstel. Sla categorieën zonder resultaten over.

Gebruik per voorstel dit format:

### [Categorienaam]

**Voorstel:** [korte beschrijving]
**Bron:** [auteur, domein, url — gebruik ALLEEN URLs uit de GEVERIFIEERDE BRONNEN sectie]
**Type:** [klein/fundamenteel]
**Toelichting:** [waarom dit relevant is voor de gebruiker]

```yaml
# Implementatie-instructie (indien van toepassing)
```

## Bronnen om in de gaten te houden
Nieuwe auteurs of domeinen die opvallend goed materiaal leverden.

## Paradigma-check
Inzichten die bestaande aannames ter discussie stellen.

BELANGRIJK: Elke zoekresultaat bevat een "GEVERIFIEERDE BRONNEN" sectie met URLs die
daadwerkelijk bestaan. Gebruik UITSLUITEND deze URLs in het rapport. Genereer NOOIT
zelf URLs — gebruik alleen wat er letterlijk in de GEVERIFIEERDE BRONNEN staat.
Als er geen geverifieerde URL beschikbaar is voor een bron, vermeld dan alleen het
domein zonder URL.
"""


def create_client(api_key: str) -> anthropic.Anthropic:
    """Maak een Anthropic API client aan."""
    return anthropic.Anthropic(api_key=api_key)


def build_analysis_prompt(
    search_results: list[dict],
    system_design: str,
    current_setup: str,
    source_weights_text: str,
) -> str:
    """Bouw de analyseprompt op uit zoekresultaten en referentiebestanden."""

    results_text = ""
    for result in search_results:
        results_text += f"\n\n--- {result['name']} ({result['id']}) ---\n"
        results_text += result["raw_output"]

    return f"""Hieronder vind je de zoekresultaten van deze week, mijn systeemontwerp,
mijn huidige setup, en mijn gewogen bronnenlijst.

Genereer op basis hiervan het weekrapport.

## ZOEKRESULTATEN

{results_text}

## MIJN SYSTEEMONTWERP

{system_design}

## MIJN HUIDIGE SETUP

{current_setup}

## GEWOGEN BRONNENLIJST

{source_weights_text}
"""


def analyze_results(
    client: anthropic.Anthropic,
    model: str,
    search_results: list[dict],
    system_design: str,
    current_setup: str,
    source_weights_text: str,
) -> str:
    """
    Stuur zoekresultaten en referentiebestanden naar Claude voor analyse.

    Returns het gegenereerde Markdown-rapport.
    """
    user_prompt = build_analysis_prompt(
        search_results, system_design, current_setup, source_weights_text
    )

    try:
        response = client.messages.create(
            model=model,
            max_tokens=8192,
            system=ANALYSIS_SYSTEM_PROMPT,
            messages=[{"role": "user", "content": user_prompt}],
        )
        report = response.content[0].text
        logger.info(f"Rapport gegenereerd: {len(report)} tekens")
        return report
    except Exception as e:
        logger.error(f"Fout bij analyse: {e}")
        return f"# Fout bij het genereren van het rapport\n\n{e}"

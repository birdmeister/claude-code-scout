"""
Bronbeheer — houdt de gewogen bronnenlijst bij.

Bronnen die leiden tot implementaties krijgen hogere scores.
Nieuwe bronnen worden automatisch toegevoegd.
"""

import logging
from urllib.parse import urlparse

import yaml

logger = logging.getLogger(__name__)


def load_source_weights(path: str) -> dict:
    """Laad de bronnenlijst uit een YAML-bestand."""
    with open(path, "r") as f:
        return yaml.safe_load(f)


def save_source_weights(path: str, data: dict) -> None:
    """Sla de bronnenlijst op naar een YAML-bestand."""
    with open(path, "w") as f:
        yaml.dump(data, f, default_flow_style=False, allow_unicode=True)
    logger.info(f"Bronnenlijst opgeslagen: {path}")


def extract_domain(url: str) -> str:
    """Haal het domein uit een URL."""
    try:
        parsed = urlparse(url)
        domain = parsed.netloc or parsed.path
        # Verwijder www. prefix
        if domain.startswith("www."):
            domain = domain[4:]
        return domain
    except Exception:
        return url


def get_weight(source_data: dict, domain: str) -> int:
    """Zoek het gewicht van een domein, of geef de standaardwaarde."""
    for source in source_data.get("sources", []):
        if source["domain"] == domain:
            return source["weight"]
    return source_data.get("default_weight", 5)


def update_source_weight(source_data: dict, domain: str, implemented: bool) -> dict:
    """
    Werk het gewicht van een bron bij.

    Als de bron tot implementatie leidt: verhoog gewicht (max 10).
    De bron wordt toegevoegd als die nog niet bestaat.
    """
    found = False
    for source in source_data.get("sources", []):
        if source["domain"] == domain:
            found = True
            if implemented:
                source["implemented_count"] = source.get("implemented_count", 0) + 1
                source["weight"] = min(10, source.get("weight", 5) + 1)
                logger.info(
                    f"Bron '{domain}' verhoogd naar gewicht {source['weight']}"
                )
            break

    if not found:
        default_weight = source_data.get("default_weight", 5)
        new_source = {
            "domain": domain,
            "weight": default_weight + (1 if implemented else 0),
            "implemented_count": 1 if implemented else 0,
            "notes": "Automatisch toegevoegd",
        }
        source_data.setdefault("sources", []).append(new_source)
        logger.info(f"Nieuwe bron '{domain}' toegevoegd")

    return source_data


def get_source_weights_text(source_data: dict) -> str:
    """Genereer een leesbare tekst van de bronnenlijst voor de analyseprompt."""
    lines = ["Gewogen bronnen (hoger = waardevoller):"]
    for source in sorted(
        source_data.get("sources", []),
        key=lambda s: s.get("weight", 0),
        reverse=True,
    ):
        lines.append(
            f"- {source['domain']}: gewicht {source.get('weight', 5)}, "
            f"{source.get('implemented_count', 0)}x geïmplementeerd"
        )
    return "\n".join(lines)

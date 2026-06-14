#!/usr/bin/env python3
"""
Claude Code Scout — wekelijkse leermachine.

Dit script wordt via cronjob gestart en doorloopt de volgende stappen:
1. Laad zoekprompts en referentiebestanden
2. Stuur prompts naar Claude met web search
3. Stuur resultaten + referentiebestanden naar Claude voor analyse
4. Sla het rapport op en verstuur het per e-mail
"""

import logging
import sys
from datetime import datetime
from pathlib import Path

import yaml

from src.search import create_client, run_all_searches
from src.analyze import analyze_results
from src.source_manager import load_source_weights, get_source_weights_text
from src.email_sender import send_report

# Logging instellen
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler("scout.log"),
    ],
)
logger = logging.getLogger("scout")


def load_config(path: str = "config.yaml") -> dict:
    """Laad configuratie uit YAML."""
    config_path = Path(path)
    if not config_path.exists():
        logger.error(
            f"Config niet gevonden: {path}. "
            "Kopieer config.example.yaml naar config.yaml en vul je gegevens in."
        )
        sys.exit(1)
    with open(config_path) as f:
        return yaml.safe_load(f)


def load_prompts(path: str) -> dict:
    """Laad zoekprompts uit YAML."""
    with open(path) as f:
        return yaml.safe_load(f)


def load_text_file(path: str) -> str:
    """Laad een tekstbestand."""
    with open(path) as f:
        return f.read()


def save_report(reports_dir: str, report: str) -> Path:
    """Sla het rapport op met datum in de bestandsnaam."""
    reports_path = Path(reports_dir)
    reports_path.mkdir(parents=True, exist_ok=True)
    date_str = datetime.now().strftime("%Y-%m-%d")
    report_file = reports_path / f"rapport-{date_str}.md"
    report_file.write_text(report, encoding="utf-8")
    logger.info(f"Rapport opgeslagen: {report_file}")
    return report_file


def main():
    logger.info("=== Claude Code Scout gestart ===")

    # Configuratie laden
    config = load_config()
    prompts_data = load_prompts(config["paths"]["prompts"])
    system_design = load_text_file(config["paths"]["system_design"])
    current_setup = load_text_file(config["paths"]["current_setup"])
    source_data = load_source_weights(config["paths"]["source_weights"])
    source_weights_text = get_source_weights_text(source_data)

    # Stap 1: zoeken via Claude met web search
    logger.info("Stap 1: zoekfase via Claude")
    anthropic_client = create_client(config["anthropic"]["api_key"])
    search_results = run_all_searches(
        client=anthropic_client,
        model=config["anthropic"].get("search_model", config["anthropic"]["model"]),
        base_instruction=prompts_data["base_instruction"],
        output_format=prompts_data["output_format"],
        prompts=prompts_data["prompts"],
        delay=config["search"].get("delay_between_calls", 5),
    )

    results_with_content = [
        r for r in search_results
        if "GEEN RESULTATEN" not in r["raw_output"]
        and not r["raw_output"].startswith("FOUT:")
    ]
    logger.info(
        f"Zoekfase klaar: {len(results_with_content)}/{len(search_results)} "
        "prompts leverden resultaten op"
    )

    if not results_with_content:
        logger.warning("Geen resultaten gevonden. Rapport wordt niet gegenereerd.")
        return

    # Stap 2: analyse via Claude
    logger.info("Stap 2: analysefase via Claude")
    report = analyze_results(
        client=anthropic_client,
        model=config["anthropic"]["model"],
        search_results=results_with_content,
        system_design=system_design,
        current_setup=current_setup,
        source_weights_text=source_weights_text,
    )

    # Stap 3: rapport opslaan
    report_path = save_report(config["paths"]["reports_dir"], report)

    # Stap 3b: publicatie-kopie opslaan in git repo
    pub_dir = config["paths"].get("publications_dir")
    if pub_dir:
        pub_path = save_report(pub_dir, report)
        logger.info(f"Publicatie opgeslagen: {pub_path}")

    # Stap 4: e-mail versturen
    logger.info("Stap 3: rapport versturen per e-mail")
    email_cfg = config["email"]
    email_sent = send_report(
        provider=email_cfg.get("provider", "resend"),
        from_address=email_cfg["from_address"],
        to_address=email_cfg["to_address"],
        subject_prefix=email_cfg["subject_prefix"],
        report_markdown=report,
        api_key=email_cfg.get("resend_api_key"),
        smtp_host=email_cfg.get("smtp_host"),
        smtp_port=email_cfg.get("smtp_port", 587),
        smtp_user=email_cfg.get("smtp_user"),
        smtp_password=email_cfg.get("smtp_password"),
    )

    if email_sent:
        logger.info("Klaar. Rapport verstuurd.")
    else:
        logger.warning(f"E-mail niet verstuurd. Rapport staat in: {report_path}")

    logger.info("=== Claude Code Scout afgerond ===")


if __name__ == "__main__":
    main()

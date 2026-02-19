# Claude Code Scout

Een wekelijkse leermachine die automatisch zoekt naar nieuwe inzichten over Claude Code, deze vergelijkt met je huidige setup, en een rapport genereert met concrete verbetervoorstellen.

Gebaseerd op het concept van [Martijn Aslander](https://www.linkedin.com/in/aslfrm/).

## Hoe het werkt

1. **Zoekfase** — 21 gespecialiseerde prompts gaan via de Gemini API (met Google Search grounding) het web af op zoek naar recente artikelen over Claude Code.
2. **Analysefase** — de resultaten worden samen met je referentiebestanden naar Claude gestuurd, die een rapport genereert met inzichten die je nog niet toepast.
3. **Rapportage** — het Markdown-rapport wordt opgeslagen en per e-mail verstuurd.
4. **Leereffect** — bronnen die leiden tot implementaties krijgen automatisch meer gewicht in volgende zoekrondes.

## Installatie op je server

```bash
# Clone de repo
git clone git@github.com:JOUW_GEBRUIKERSNAAM/claude-code-scout.git
cd claude-code-scout

# Python virtual environment
python3 -m venv venv
source venv/bin/activate

# Dependencies
pip install -r requirements.txt

# Configuratie
cp config.example.yaml config.yaml
# Vul je API keys en e-mailinstellingen in:
nano config.yaml
```

## Referentiebestanden invullen

Er zijn drie bestanden in `reference/` die je moet aanpassen:

- **`system_design.md`** — beschrijf het ontwerp en de doelen van je Claude Code omgeving
- **`current_setup.md`** — beschrijf wat je al gebruikt (commands, hooks, skills, MCP servers, etc.)
- **`source_weights.yaml`** — begint met een paar standaardbronnen, groeit vanzelf mee

Hoe beter je deze bestanden invult, hoe relevanter het rapport wordt.

## Handmatig draaien (testen)

```bash
cd /pad/naar/claude-code-scout
source venv/bin/activate
python main.py
```

Het rapport verschijnt in de `reports/` map en in je inbox.

## Cronjob instellen (vrijdagavond 21:00)

```bash
crontab -e
```

Voeg deze regel toe:

```cron
0 21 * * 5 cd /pad/naar/claude-code-scout && /pad/naar/claude-code-scout/venv/bin/python main.py >> /pad/naar/claude-code-scout/cron.log 2>&1
```

Vervang `/pad/naar/claude-code-scout` door het daadwerkelijke pad op je server.

## Structuur

```
claude-code-scout/
├── main.py                    # Hoofdscript (cronjob entry point)
├── config.example.yaml        # Voorbeeldconfiguratie
├── requirements.txt           # Python dependencies
├── prompts/
│   └── search_prompts.yaml    # 21 zoekprompts per Claude Code aspect
├── reference/
│   ├── system_design.md       # Jouw systeemontwerp
│   ├── current_setup.md       # Wat je al toepast
│   └── source_weights.yaml    # Gewogen bronnenlijst (groeit mee)
├── reports/                   # Gegenereerde rapporten
└── src/
    ├── search.py              # Gemini zoekmodule
    ├── analyze.py             # Claude analysemodule
    ├── source_manager.py      # Bronbeheer
    └── email_sender.py        # E-mailverzending
```

## Brongewichten bijwerken

Na het doorlopen van een rapport kun je brongewichten bijwerken door `source_weights.yaml` aan te passen. Bronnen die tot implementaties leiden geef je een hoger gewicht (max 10). Dit kan handmatig, of je bouwt er later een interactieve stap voor.

## E-mail via Hetzner

Als je Hetzner gebruikt, kun je SMTP instellen via een externe mailprovider (bijv. Mailgun, Brevo/Sendinblue, of je eigen domein met SMTP). Hetzner blokkeert standaard poort 25 voor uitgaande mail, maar poort 587 (STARTTLS) werkt wel met een externe SMTP-server.

## Later uitbreiden

Het systeem is bewust modulair opgezet. Mogelijke uitbreidingen:

- Extra onderwerpen naast Claude Code (eigen promptsets toevoegen)
- Interactieve review via CLI in plaats van handmatig rapport doorlopen
- Automatische bronweging na implementatie
- Kwartaal-reset van brongewichten (anti-echokamer, zoals beschreven door Aslander)

# Daedalus
![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)
![Python](https://img.shields.io/badge/python-3.13%2B-blue)

**Daedalus** is a lightweight, general purpose, ergonomic research agent built for surfacing papers and assisting in research. 

# Getting Started
Run setup.py in our uv environment to get started to securely store your credentials in a `.env`.
```
uv sync
uv run scripts/setup_env.py
```

Then run the research agent and enter a topic when prompted.
```
uv run main.py
```

The current paper surfacing flow uses `scripts/paper_search.py` to search arXiv and Crossref metadata, dedupe and rank the results, and pass the top papers into the LLM as grounding context. `CROSSREF_MAILTO` is optional, but adding it during setup is recommended for polite Crossref API usage.

For example:
```
Research topic: vision-language-action models for robot manipulation
```

To surface papers through Discord, add your Discord bot token during setup and run the bot.
```
uv run scripts/discord_bot.py
```

The bot registers global `/papers` and `/research` commands. Global Discord commands can take time to appear after startup. `/papers` returns surfaced metadata, while `/research` asks the LLM to write grounded notes from the surfaced papers.
```
/papers topic: vision-language-action models for robot manipulation after_date: 2024-01-01 before_date: 2026-12-31 article_count: 5
/research topic: vision-language-action models for robot manipulation after_date: 2024-01-01 before_date: 2026-12-31 article_count: 5
```

# Architecture
We plan on using a Python + Redis + Postgres/Database setup. Currently, only a very basic MVP for the Python backend has been setup. First and foremost, we're planning to support third party & local LLM services, and quick and easy setup with VPS and local setups. 

# Repository Directory
We plan to follow a readability-first principled approach to this repository. Most of our code will be designed to be readable and ergonomic.

## Roadmap
**In-Progress/Partially Implemented**
- [x] Setup for tokens through `setup_env.py`. Note: this is currently very barebones.
- [X] Migrate Scripts and codebase into src and proper directory structure

**Open:**

- [ ] Basic Agent paper surfacing
- [ ] Support multiple model switching within API
- [ ] Hide API Key during input via setup
- [ ] Streamline setup through a proper TUI with React + Ink
- [ ] Repository Directory writeup
- [ ] Database integration
# Daedalus
**Daedalus** is a lightweight, general purpose, ergonomic research agent built for surfacing papers and assisting in research. 

# Getting Started
Run setup.py in our uv environment to get started to securely store your credentials in a `.env`.
```
uv sync
uv run setup.py
```

# Architecture
We plan on using a Python + Redis + Postgres/Database setup. Currently, only a very basic MVP for the Python backend has been setup. First and foremost, we're planning to support third party & local LLM services, and quick and easy setup with VPS and local setups. 

# Repository Directory
We plan to follow a readability-first principled approach to this repository. Most of our code will be designed to be readable and ergonomic.

## Roadmap
**Implemented**
- [ ] Setup for tokens through `setup.py`. Note: this is currently very barebones.

**Open issues:**
- [ ] Basic Agent paper surfacing
- [ ] Support multiple model switching within API
- [ ] Hide API Key during input via setup
- [ ] Streamline setup through a proper TUI with React + Ink
- [ ] Repository Directory writeup
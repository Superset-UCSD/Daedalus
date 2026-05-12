FROM ghcr.io/astral-sh/uv:alpine

WORKDIR /app
COPY .env .env
COPY pyproject.toml pyproject.toml
COPY DaedalusBot/ .

RUN ls

RUN uv sync --no-dev

ENTRYPOINT ["uv", "run", "daedalus_bot/discord_bot.py"]
FROM ghcr.io/astral-sh/uv:alpine

WORKDIR /app

# env set up
COPY pyproject.toml pyproject.toml
RUN uv sync --no-dev

# copy code
COPY DaedalusSearch/ .

ENTRYPOINT ["uv", "run", "fastapi", "dev", "--host", "0.0.0.0"]
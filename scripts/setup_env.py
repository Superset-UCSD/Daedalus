from pathlib import Path

env_path = Path(".env")
gitignore_path = Path(".gitignore")

base_url = input("Input your LLM base URL: ").strip()
api_key = input("Input your API Key: ").strip()
model = input("Input your desired Model ID: ").strip()
discord_bot_token = input("Input your Discord Bot Token (optional): ").strip()
crossref_mailto = input("Input your Crossref mailto (optional): ").strip()

base_url = base_url or "http://localhost:1234/v1"
api_key = api_key or "not-needed"
model = model or "local-model"
discord_bot_token = discord_bot_token or ""
crossref_mailto = crossref_mailto or ""

env_path.write_text(
    f'''LLM_BASE_URL="{base_url}"
LLM_API_KEY="{api_key}"
LLM_MODEL="{model}"
DISCORD_BOT_TOKEN="{discord_bot_token}"
CROSSREF_MAILTO="{crossref_mailto}"
''',
    encoding="utf-8",
)

gitignore = gitignore_path.read_text(encoding="utf-8") if gitignore_path.exists() else ""

if ".env" not in gitignore.splitlines():
    gitignore_path.write_text(gitignore.rstrip() + "\n.env\n", encoding="utf-8")

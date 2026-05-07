import asyncio
import os

import discord
from discord import app_commands
from dotenv import load_dotenv

from paper_search import search_arxiv, search_crossref, surface_papers


def format_discord_papers(topic: str, papers: list[dict]) -> str:
    if not papers:
        return f"No papers found for: {topic}\nTry a more specific research topic."

    lines = [f"Top papers for: {topic}"]
    for index, paper in enumerate(papers, start=1):
        authors = ", ".join(paper.get("authors", [])[:3]) or "Unknown authors"
        if len(paper.get("authors", [])) > 3:
            authors += ", et al."

        lines.append("")
        lines.append(f"{index}. {paper.get('title') or 'Untitled'}")
        lines.append(f"   {paper.get('year') or 'Unknown year'} | {paper.get('source') or 'unknown'} | {authors}")
        if paper.get("doi"):
            lines.append(f"   DOI: {paper['doi']}")
        if paper.get("url"):
            lines.append(f"   {paper['url']}")

    message = "\n".join(lines)
    if len(message) <= 1900:
        return message

    shorter_lines = lines[:1]
    for line in lines[1:]:
        if len("\n".join(shorter_lines + [line, "\nResults truncated."])) > 1900:
            break
        shorter_lines.append(line)

    return "\n".join(shorter_lines + ["", "Results truncated."])


load_dotenv()

discord_token = os.getenv("DISCORD_BOT_TOKEN")
crossref_mailto = os.getenv("CROSSREF_MAILTO") or None

intents = discord.Intents.default()
client = discord.Client(intents=intents)
tree = app_commands.CommandTree(client)


@tree.command(name="papers", description="Surface papers for a research topic.")
@app_commands.describe(topic="Research topic to search.")
async def papers(interaction: discord.Interaction, topic: str) -> None:
    topic = topic.strip()
    if not topic:
        await interaction.response.send_message("Please enter a research topic.", ephemeral=True)
        return

    await interaction.response.defer(thinking=True)

    arxiv_results = search_arxiv(topic, limit=12)
    crossref_results = search_crossref(topic, limit=12, mailto=crossref_mailto)
    surfaced = surface_papers(arxiv_results + crossref_results, query=topic, limit=5)

    await interaction.followup.send(format_discord_papers(topic, surfaced))


@client.event
async def on_ready() -> None:
    print("Syncing global Discord commands...", flush=True)
    try:
        await asyncio.wait_for(tree.sync(), timeout=30)
    except TimeoutError:
        print("Discord command sync timed out. The bot is connected, but /papers may not be registered yet.", flush=True)
        return

    print(f"Daedalus Discord bot is ready as {client.user}.", flush=True)


if __name__ == "__main__":
    if not discord_token:
        raise SystemExit("DISCORD_BOT_TOKEN is required. Run scripts/setup_env.py first.")

    client.run(discord_token)

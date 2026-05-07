import asyncio
import os
from datetime import datetime

import discord
from discord import app_commands
from dotenv import load_dotenv
from openai import OpenAI

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
        date = paper.get("published_date") or paper.get("year") or "Unknown date"
        lines.append(f"   {date} | {paper.get('source') or 'unknown'} | {authors}")
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


def format_discord_research_notes(topic: str, papers: list[dict], notes: str) -> list[str]:
    paper_lines = format_discord_papers(topic, papers).splitlines()
    messages = [notes.strip()[:1900] or "No research notes were returned."]

    paper_message = "\n".join(paper_lines)
    if len(paper_message) <= 1900:
        messages.append(paper_message)
    else:
        messages.append("\n".join(paper_lines[:20] + ["", "Paper list truncated."]))

    return messages


def parse_discord_date(value: str | None) -> str | None:
    if not value:
        return None

    try:
        return datetime.strptime(value, "%Y-%m-%d").date().isoformat()
    except ValueError:
        raise ValueError("Dates must use YYYY-MM-DD.") from None


def clamp_article_count(value: int) -> int:
    return max(1, min(value, 10))


load_dotenv()

discord_token = os.getenv("DISCORD_BOT_TOKEN")
crossref_mailto = os.getenv("CROSSREF_MAILTO") or None
llm_client = OpenAI(
    base_url=os.getenv("LLM_BASE_URL", "http://localhost:1234/v1"),
    api_key=os.getenv("LLM_API_KEY", "not-needed"),
)
llm_model = os.getenv("LLM_MODEL", "local-model")

intents = discord.Intents.default()
client = discord.Client(intents=intents)
tree = app_commands.CommandTree(client)


@tree.command(name="papers", description="Surface papers for a research topic.")
@app_commands.describe(
    topic="Research topic to search.",
    after_date="Optional lower date bound: YYYY-MM-DD.",
    before_date="Optional upper date bound: YYYY-MM-DD.",
    article_count="Number of papers to return, from 1 to 10.",
)
async def papers(
    interaction: discord.Interaction,
    topic: str,
    after_date: str | None = None,
    before_date: str | None = None,
    article_count: int = 5,
) -> None:
    topic = topic.strip()
    if not topic:
        await interaction.response.send_message("Please enter a research topic.", ephemeral=True)
        return

    try:
        after_date = parse_discord_date(after_date)
        before_date = parse_discord_date(before_date)
    except ValueError as error:
        await interaction.response.send_message(str(error), ephemeral=True)
        return

    if after_date and before_date and after_date > before_date:
        await interaction.response.send_message("after_date must be before before_date.", ephemeral=True)
        return

    await interaction.response.defer(thinking=True)

    article_count = clamp_article_count(article_count)
    source_limit = max(article_count * 4, 12)
    arxiv_results = search_arxiv(topic, limit=source_limit)
    crossref_results = search_crossref(topic, limit=source_limit, mailto=crossref_mailto)
    surfaced = surface_papers(
        arxiv_results + crossref_results,
        query=topic,
        limit=article_count,
        after_date=after_date,
        before_date=before_date,
    )

    await interaction.followup.send(format_discord_papers(topic, surfaced))


@tree.command(name="research", description="Use Daedalus to write grounded research notes for a topic.")
@app_commands.describe(
    topic="Research topic to search.",
    after_date="Optional lower date bound: YYYY-MM-DD.",
    before_date="Optional upper date bound: YYYY-MM-DD.",
    article_count="Number of papers to ground on, from 1 to 10.",
)
async def research(
    interaction: discord.Interaction,
    topic: str,
    after_date: str | None = None,
    before_date: str | None = None,
    article_count: int = 5,
) -> None:
    topic = topic.strip()
    if not topic:
        await interaction.response.send_message("Please enter a research topic.", ephemeral=True)
        return

    try:
        after_date = parse_discord_date(after_date)
        before_date = parse_discord_date(before_date)
    except ValueError as error:
        await interaction.response.send_message(str(error), ephemeral=True)
        return

    if after_date and before_date and after_date > before_date:
        await interaction.response.send_message("after_date must be before before_date.", ephemeral=True)
        return

    await interaction.response.defer(thinking=True)

    article_count = clamp_article_count(article_count)
    source_limit = max(article_count * 4, 12)
    arxiv_results = search_arxiv(topic, limit=source_limit)
    crossref_results = search_crossref(topic, limit=source_limit, mailto=crossref_mailto)
    surfaced = surface_papers(
        arxiv_results + crossref_results,
        query=topic,
        limit=article_count,
        after_date=after_date,
        before_date=before_date,
    )

    paper_context = format_discord_papers(topic, surfaced)
    response = llm_client.chat.completions.create(
        model=llm_model,
        messages=[
            {
                "role": "system",
                "content": (
                    "You are Daedalus, a careful AI research assistant. "
                    "Use only the provided paper metadata as grounding. "
                    "Do not invent papers or citations. "
                    "If the metadata is weak, say what should be searched next."
                ),
            },
            {
                "role": "user",
                "content": f"""
Research topic:
{topic}

Paper metadata:
{paper_context}

Return:
1. A short research area summary
2. Why these papers matter
3. Suggested next search queries
4. Open research directions
""",
            },
        ],
        temperature=0.2,
    )

    notes = response.choices[0].message.content or ""
    for message in format_discord_research_notes(topic, surfaced, notes):
        await interaction.followup.send(message)


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

from scripts.discord_bot import format_discord_papers


def test_format_discord_papers_lists_top_papers() -> None:
    message = format_discord_papers(
        "robot manipulation",
        [
            {
                "title": "Vision Language Action Models",
                "authors": ["Ada", "Grace", "Alan", "Katherine"],
                "year": 2026,
                "source": "arxiv",
                "doi": "10.1234/example",
                "url": "https://example.com/paper",
            }
        ],
    )

    assert "Top papers for: robot manipulation" in message
    assert "1. Vision Language Action Models" in message
    assert "Ada, Grace, Alan, et al." in message
    assert "DOI: 10.1234/example" in message
    assert "https://example.com/paper" in message


def test_format_discord_papers_handles_empty_results() -> None:
    message = format_discord_papers("unknown topic", [])

    assert "No papers found for: unknown topic" in message
    assert "Try a more specific research topic." in message

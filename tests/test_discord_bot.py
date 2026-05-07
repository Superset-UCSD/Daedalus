from scripts.discord_bot import format_discord_papers, format_discord_research_notes, parse_discord_date


def test_format_discord_papers_lists_top_papers() -> None:
    message = format_discord_papers(
        "robot manipulation",
        [
            {
                "title": "Vision Language Action Models",
                "authors": ["Ada", "Grace", "Alan", "Katherine"],
                "year": 2026,
                "published_date": "2026-01-01",
                "source": "arxiv",
                "doi": "10.1234/example",
                "url": "https://example.com/paper",
            }
        ],
    )

    assert "Top papers for: robot manipulation" in message
    assert "1. Vision Language Action Models" in message
    assert "2026-01-01" in message
    assert "Ada, Grace, Alan, et al." in message
    assert "DOI: 10.1234/example" in message
    assert "https://example.com/paper" in message


def test_format_discord_papers_handles_empty_results() -> None:
    message = format_discord_papers("unknown topic", [])

    assert "No papers found for: unknown topic" in message
    assert "Try a more specific research topic." in message


def test_parse_discord_date_requires_iso_date() -> None:
    assert parse_discord_date("2026-05-07") == "2026-05-07"
    assert parse_discord_date(None) is None

    try:
        parse_discord_date("05/07/2026")
    except ValueError as error:
        assert str(error) == "Dates must use YYYY-MM-DD."
    else:
        raise AssertionError("Expected invalid Discord date to fail.")


def test_format_discord_research_notes_returns_notes_and_papers() -> None:
    messages = format_discord_research_notes(
        "robot manipulation",
        [
            {
                "title": "Vision Language Action Models",
                "authors": ["Ada"],
                "year": 2026,
                "published_date": "2026-01-01",
                "source": "arxiv",
                "doi": None,
                "url": "https://example.com/paper",
            }
        ],
        "Grounded research notes.",
    )

    assert messages[0] == "Grounded research notes."
    assert "Top papers for: robot manipulation" in messages[1]
    assert "Vision Language Action Models" in messages[1]

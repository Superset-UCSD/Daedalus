from datetime import UTC, datetime

from DaedalusSearch.src.paper_search import format_paper_context, surface_papers


def test_surface_papers_dedupes_by_doi_and_merges_fields() -> None:
    records = [
        {
            "title": "First copy",
            "authors": ["A. Author"],
            "year": 2024,
            "published_date": "2024-01-01",
            "abstract": "",
            "url": "https://example.com/1",
            "source": "crossref",
            "doi": "10.1234/example",
            "arxiv_id": None,
        },
        {
            "title": "Second copy",
            "authors": ["A. Author", "B. Author"],
            "year": 2024,
            "published_date": "2024-02-01",
            "abstract": "This is a longer abstract.",
            "url": "https://example.com/2",
            "source": "arxiv",
            "doi": "10.1234/EXAMPLE",
            "arxiv_id": "2401.12345v2",
        },
    ]

    surfaced = surface_papers(records, query="example", limit=5)

    assert len(surfaced) == 1
    assert surfaced[0]["doi"] == "10.1234/example"
    assert surfaced[0]["abstract"] == "This is a longer abstract."
    assert surfaced[0]["authors"] == ["A. Author", "B. Author"]


def test_surface_papers_normalizes_arxiv_versions() -> None:
    records = [
        {
            "title": "Paper",
            "authors": [],
            "year": 2024,
            "published_date": "2024-01-01",
            "abstract": "short",
            "url": "https://arxiv.org/abs/2401.12345v1",
            "source": "arxiv",
            "doi": None,
            "arxiv_id": "2401.12345v1",
        },
        {
            "title": "Paper",
            "authors": [],
            "year": 2024,
            "published_date": "2024-02-01",
            "abstract": "a longer replacement abstract",
            "url": "https://arxiv.org/abs/2401.12345v2",
            "source": "arxiv",
            "doi": None,
            "arxiv_id": "2401.12345v2",
        },
    ]

    surfaced = surface_papers(records, query="paper", limit=5)
    assert len(surfaced) == 1
    assert surfaced[0]["abstract"] == "a longer replacement abstract"


def test_surface_papers_falls_back_to_title_year() -> None:
    records = [
        {
            "title": " Vision Language Action Policy ",
            "authors": [],
            "year": 2023,
            "published_date": "2023-01-01",
            "abstract": "brief",
            "url": "",
            "source": "arxiv",
            "doi": None,
            "arxiv_id": None,
        },
        {
            "title": "vision-language action policy",
            "authors": [],
            "year": 2023,
            "published_date": "2023-01-02",
            "abstract": "more detailed abstract text",
            "url": "",
            "source": "crossref",
            "doi": None,
            "arxiv_id": None,
        },
    ]

    surfaced = surface_papers(records, query="vision language action", limit=5)
    assert len(surfaced) == 1
    assert surfaced[0]["abstract"] == "more detailed abstract text"


def test_surface_papers_ranks_relevance_recency_then_title() -> None:
    current_year = datetime.now(UTC).year
    query = "vision language action policy"
    records = [
        {
            "title": "Vision language action policy for robots",
            "authors": [],
            "year": current_year - 10,
            "published_date": f"{current_year - 10}-01-01",
            "abstract": "",
            "url": "",
            "source": "arxiv",
            "doi": None,
            "arxiv_id": None,
        },
        {
            "title": "Vision language robot planning",
            "authors": [],
            "year": current_year,
            "published_date": f"{current_year}-01-01",
            "abstract": "action grounding",
            "url": "",
            "source": "crossref",
            "doi": None,
            "arxiv_id": None,
        },
        {
            "title": "Unrelated topic",
            "authors": [],
            "year": current_year,
            "published_date": f"{current_year}-01-01",
            "abstract": "",
            "url": "",
            "source": "crossref",
            "doi": None,
            "arxiv_id": None,
        },
    ]

    surfaced = surface_papers(records, query, limit=5)

    assert surfaced[0]["title"] == "Vision language robot planning"
    assert surfaced[1]["title"] == "Vision language action policy for robots"
    assert surfaced[2]["title"] == "Unrelated topic"


def test_surface_papers_limit_and_context_formatting() -> None:
    records = [
        {
            "title": "Paper A",
            "authors": ["Alice"],
            "year": 2024,
            "published_date": "2024-01-01",
            "abstract": "",
            "url": "https://example.com/a",
            "source": "arxiv",
            "doi": None,
            "arxiv_id": "2401.00001",
        },
        {
            "title": "Paper B",
            "authors": [],
            "year": None,
            "published_date": None,
            "abstract": "",
            "url": "",
            "source": "crossref",
            "doi": "10.1/example",
            "arxiv_id": None,
        },
    ]

    selected = surface_papers(records, query="paper", limit=1)
    assert len(selected) == 1
    assert selected[0]["title"] == "Paper A"

    context = format_paper_context(records)
    assert "Candidate papers from metadata search:" in context
    assert "1. Paper A" in context
    assert "2. Paper B" in context


def test_missing_fields_do_not_break_pipeline() -> None:
    records = [{"title": "Sparse record"}]

    selected = surface_papers(records, query="vision language action", limit=5)

    assert len(selected) == 1
    assert selected[0]["title"] == "Sparse record"


def test_surface_papers_filters_by_date_window() -> None:
    records = [
        {
            "title": "Older Paper",
            "authors": [],
            "year": 2022,
            "published_date": "2022-01-01",
            "abstract": "robot policy",
            "url": "",
            "source": "arxiv",
            "doi": None,
            "arxiv_id": "2201.00001",
        },
        {
            "title": "Newer Paper",
            "authors": [],
            "year": 2024,
            "published_date": "2024-01-01",
            "abstract": "robot policy",
            "url": "",
            "source": "arxiv",
            "doi": None,
            "arxiv_id": "2401.00001",
        },
    ]

    surfaced = surface_papers(
        records,
        query="robot policy",
        limit=5,
        after_date="2023-01-01",
        before_date="2024-12-31",
    )

    assert len(surfaced) == 1
    assert surfaced[0]["title"] == "Newer Paper"

import json
import re
from datetime import UTC, datetime
from urllib.parse import quote
from urllib.request import Request, urlopen
from xml.etree import ElementTree


def search_arxiv(query: str, limit: int) -> list[dict]:
    if not query.strip() or limit <= 0:
        return []

    url = (
        "http://export.arxiv.org/api/query"
        f"?search_query=all:{quote(query.strip())}"
        f"&start=0&max_results={limit}"
        "&sortBy=relevance&sortOrder=descending"
    )

    try:
        with urlopen(Request(url, headers={"User-Agent": "Daedalus/0.1"}), timeout=10) as response:
            root = ElementTree.fromstring(response.read().decode("utf-8"))
    except Exception:
        return []

    namespaces = {
        "atom": "http://www.w3.org/2005/Atom",
        "arxiv": "http://arxiv.org/schemas/atom",
    }

    records = []
    for entry in root.findall("atom:entry", namespaces):
        title = " ".join(entry.findtext("atom:title", default="", namespaces=namespaces).split())
        abstract = " ".join(entry.findtext("atom:summary", default="", namespaces=namespaces).split())
        paper_url = " ".join(entry.findtext("atom:id", default="", namespaces=namespaces).split())
        published = " ".join(entry.findtext("atom:published", default="", namespaces=namespaces).split())
        doi = " ".join(entry.findtext("arxiv:doi", default="", namespaces=namespaces).split())

        authors = []
        for author in entry.findall("atom:author", namespaces):
            name = " ".join(author.findtext("atom:name", default="", namespaces=namespaces).split())
            if name:
                authors.append(name)

        records.append(
            {
                "title": title,
                "authors": authors,
                "year": int(published[:4]) if published[:4].isdigit() else None,
                "published_date": published[:10] if len(published) >= 10 else None,
                "abstract": abstract,
                "url": paper_url,
                "source": "arxiv",
                "doi": doi or None,
                "arxiv_id": paper_url.rsplit("/", 1)[-1] if paper_url else None,
            }
        )

    return records


def search_crossref(query: str, limit: int, mailto: str | None = None) -> list[dict]:
    if not query.strip() or limit <= 0:
        return []

    params = [f"query={quote(query.strip())}", f"rows={limit}"]
    if mailto:
        params.append(f"mailto={quote(mailto)}")

    try:
        request = Request(f"https://api.crossref.org/works?{'&'.join(params)}", headers={"User-Agent": "Daedalus/0.1"})
        with urlopen(request, timeout=10) as response:
            payload = json.loads(response.read().decode("utf-8"))
    except Exception:
        return []

    records = []
    for item in payload.get("message", {}).get("items", []):
        title = item.get("title", [""])[0]
        authors = []
        for author in item.get("author", []):
            name = f"{author.get('given', '')} {author.get('family', '')}".strip()
            if name:
                authors.append(" ".join(name.split()))

        year = None
        published_date = None
        for date_key in ("published-print", "published-online", "issued"):
            date_parts = item.get(date_key, {}).get("date-parts", [])
            if date_parts and date_parts[0] and isinstance(date_parts[0][0], int):
                year = date_parts[0][0]
                month = date_parts[0][1] if len(date_parts[0]) > 1 and isinstance(date_parts[0][1], int) else 1
                day = date_parts[0][2] if len(date_parts[0]) > 2 and isinstance(date_parts[0][2], int) else 1
                published_date = f"{year:04d}-{month:02d}-{day:02d}"
                break

        records.append(
            {
                "title": " ".join(title.split()),
                "authors": authors,
                "year": year,
                "published_date": published_date,
                "abstract": " ".join((item.get("abstract", "") or "").split()),
                "url": " ".join((item.get("URL", "") or "").split()),
                "source": "crossref",
                "doi": " ".join((item.get("DOI", "") or "").split()) or None,
                "arxiv_id": None,
            }
        )

    return records


def surface_papers(
    records: list[dict],
    query: str,
    limit: int = 5,
    after_date: str | None = None,
    before_date: str | None = None,
) -> list[dict]:
    query_tokens = set(re.sub(r"[^a-z0-9]+", " ", query.lower()).split())
    current_year = datetime.now(UTC).year
    deduped = {}

    for record in records:
        published_date = record.get("published_date")
        if (after_date or before_date) and not published_date:
            continue
        if after_date and published_date and published_date < after_date:
            continue
        if before_date and published_date and published_date > before_date:
            continue

        doi = (record.get("doi") or "").strip().lower()
        arxiv_id = re.sub(r"v\d+$", "", (record.get("arxiv_id") or "").strip().lower())
        title = re.sub(r"[^a-z0-9]+", " ", (record.get("title") or "").lower()).strip()
        key = ("doi", doi) if doi else ("arxiv", arxiv_id) if arxiv_id else ("title_year", f"{title}|{record.get('year')}")

        if key not in deduped:
            deduped[key] = dict(record)
            continue

        existing = deduped[key]
        if len(record.get("abstract", "")) > len(existing.get("abstract", "")):
            existing["abstract"] = record["abstract"]
        if len(record.get("authors", [])) > len(existing.get("authors", [])):
            existing["authors"] = record["authors"]
        for field in ("title", "year", "published_date", "url", "doi", "arxiv_id"):
            if not existing.get(field) and record.get(field):
                existing[field] = record[field]

    scored_records = []
    for record in deduped.values():
        record_text = f"{record.get('title', '')} {record.get('abstract', '')}"
        record_tokens = set(re.sub(r"[^a-z0-9]+", " ", record_text.lower()).split())
        score = len(query_tokens & record_tokens)

        year = record.get("year")
        if isinstance(year, int) and current_year - year <= 2:
            score += 2
        elif isinstance(year, int) and current_year - year <= 5:
            score += 1

        scored_records.append((score, record))

    scored_records.sort(
        key=lambda item: (
            -item[0],
            -(item[1].get("year") or 0),
            (item[1].get("title") or "").lower(),
        )
    )
    return [record for _, record in scored_records[:limit]]


def format_paper_context(records: list[dict]) -> str:
    if not records:
        return ""

    lines = ["Candidate papers from metadata search:"]
    for index, record in enumerate(records, start=1):
        lines.append(f"{index}. {record.get('title') or 'Untitled'}")
        lines.append(f"   Authors: {', '.join(record.get('authors', [])) or 'Unknown authors'}")
        lines.append(
            f"   Date: {record.get('published_date') or record.get('year') or 'Unknown date'} | "
            f"Source: {record.get('source') or 'unknown'} | "
            f"DOI: {record.get('doi') or 'N/A'}"
        )
        lines.append(f"   URL: {record.get('url') or 'N/A'}")

    return "\n".join(lines)

import os

from fastapi import APIRouter

from .model import Model
from .paper_search import (
    format_paper_context,
    search_arxiv,
    search_crossref,
    surface_papers
)


class Server:
    def __init__(self, name: str):
        self.name = name
        self.router = APIRouter()
        self.router.add_api_route("/search", self.search, methods=["POST"])
        self.model = Model() #TODO dict of model

    #  def add_model # when we add more models

    def search(self, topic:str):
        arxiv_results = search_arxiv(topic, limit=12)
        crossref_results = search_crossref(
            topic,
            limit=12,
            mailto=os.getenv("CROSSREF_MAILTO") or None,
        )

        candidate_papers = surface_papers(arxiv_results + crossref_results, query=topic, limit=5)
        paper_context = format_paper_context(candidate_papers)

        retrieval_instruction = (
            "Use the candidate paper metadata below as grounding where relevant. "
            "Do not invent citations beyond this set. "
            "If these candidates are insufficient, provide concrete next search queries."
            if paper_context
            else "Metadata retrieval returned no paper candidates. "
            "Give likely search targets and concrete next queries instead of pretending you searched."
        )
        
        response = self.model.prompt (
            [
                {
                    "role": "system",
                    "content": (
                        "You are a careful AI research assistant. "
                        "Return concise, practical research notes. "
                        "Do not invent papers or citations. "
                        "If you are unsure, say what should be searched next."
                    ),
                },
                {
                    "role": "user",
                    "content": f"""
        Find useful academic papers related to this topic:

        {topic}

        {paper_context}

        Return:

        1. A short summary of the research area
        2. 5 likely relevant papers or search targets
        3. Why each paper/search target matters
        4. Suggested next search queries
        5. Open research directions

        {retrieval_instruction}
        """,
                },
            ],
        )

        return {"message": response.choices[0].message.content}

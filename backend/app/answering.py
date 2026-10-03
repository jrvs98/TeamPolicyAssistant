import re

from app.retrieval import SearchResult


def build_grounded_answer(query: str, results: list[SearchResult]) -> tuple[str, str]:
    if not results or results[0].distance > 0.95:
        return (
            "I could not find enough evidence in the indexed policies to answer that question.",
            "fallback",
        )

    query_terms = {term for term in re.findall(r"[a-z0-9]+", query.lower()) if len(term) > 2}
    selected: list[str] = []
    for result in results[:3]:
        sentences = re.split(r"(?<=[.!?])\s+", result.content)
        matching = [sentence for sentence in sentences if query_terms.intersection(sentence.lower().split())]
        selected.append(" ".join(matching[:2]) or sentences[0])
    return " ".join(selected), "extractive"

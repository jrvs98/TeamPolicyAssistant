import re

from app.retrieval import SearchResult


def run_answer_workflow(query: str, results: list[SearchResult]) -> dict[str, object]:
    if not results:
        return {
            "answer": "I could not find enough evidence in the indexed policies to answer that question.",
            "route": "fallback",
            "steps": ["retrieve", "grade_context", "fallback"],
        }

    if results[0].distance > 0.95:
        return {
            "answer": "I could not find enough evidence in the indexed policies to answer that question.",
            "route": "fallback",
            "steps": ["retrieve", "grade_context", "fallback"],
        }

    query_terms = {term for term in re.findall(r"[a-z0-9]+", query.lower()) if len(term) > 2}
    selected: list[str] = []
    for result in results[:3]:
        sentences = re.split(r"(?<=[.!?])\s+", result.content)
        matching = [sentence for sentence in sentences if query_terms.intersection(sentence.lower().split())]
        selected.append(" ".join(matching[:2]) or sentences[0])

    answer = " ".join(selected).strip()
    if not answer:
        return {
            "answer": "I could not find enough evidence in the indexed policies to answer that question.",
            "route": "fallback",
            "steps": ["retrieve", "grade_context", "fallback"],
        }

    return {
        "answer": answer,
        "route": "extractive",
        "steps": ["retrieve", "grade_context", "generate_answer", "verify_answer"],
    }


def build_grounded_answer(query: str, results: list[SearchResult]) -> tuple[str, str]:
    workflow = run_answer_workflow(query, results)
    return str(workflow["answer"]), str(workflow["route"])

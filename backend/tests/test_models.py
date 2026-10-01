from app.models import Base


def test_roadmap_tables_are_registered() -> None:
    expected_tables = {
        "users",
        "documents",
        "document_chunks",
        "questions",
        "answers",
        "citations",
        "feedback",
        "evaluation_cases",
        "evaluation_results",
    }

    assert set(Base.metadata.tables) == expected_tables

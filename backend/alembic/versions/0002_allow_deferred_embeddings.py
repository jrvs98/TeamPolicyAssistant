"""allow embeddings to be created after text ingestion

Revision ID: 0002_allow_deferred_embeddings
Revises: 0001_initial_schema
"""
from alembic import op

revision = "0002_allow_deferred_embeddings"
down_revision = "0001_initial_schema"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.alter_column("document_chunks", "embedding", nullable=True)


def downgrade() -> None:
    op.alter_column("document_chunks", "embedding", nullable=False)
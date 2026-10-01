"""create initial policy assistant schema

Revision ID: 0001_initial_schema
"""
from alembic import op
import sqlalchemy as sa
from pgvector.sqlalchemy import Vector

revision = "0001_initial_schema"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute("CREATE EXTENSION IF NOT EXISTS vector")
    uuid = sa.dialects.postgresql.UUID(as_uuid=True)
    op.create_table("users", sa.Column("id", uuid, primary_key=True), sa.Column("subject", sa.String(255), nullable=False, unique=True), sa.Column("username", sa.String(255)), sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False))
    op.create_index("ix_users_subject", "users", ["subject"])
    op.create_table("documents", sa.Column("id", uuid, primary_key=True), sa.Column("filename", sa.String(255), nullable=False), sa.Column("content_type", sa.String(100), nullable=False), sa.Column("storage_key", sa.String(500), nullable=False, unique=True), sa.Column("status", sa.String(20), nullable=False), sa.Column("failure_reason", sa.Text()), sa.Column("uploaded_by", uuid, sa.ForeignKey("users.id"), nullable=False), sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False), sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False))
    op.create_table("document_chunks", sa.Column("id", uuid, primary_key=True), sa.Column("document_id", uuid, sa.ForeignKey("documents.id", ondelete="CASCADE"), nullable=False), sa.Column("chunk_index", sa.Integer(), nullable=False), sa.Column("content", sa.Text(), nullable=False), sa.Column("page_number", sa.Integer()), sa.Column("embedding", Vector(1536), nullable=False), sa.Column("metadata_json", sa.dialects.postgresql.JSONB(), nullable=False))
    op.create_index("ix_document_chunks_document_id", "document_chunks", ["document_id"])
    op.create_table("questions", sa.Column("id", uuid, primary_key=True), sa.Column("asked_by", uuid, sa.ForeignKey("users.id"), nullable=False), sa.Column("text", sa.Text(), nullable=False), sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False))
    op.create_table("answers", sa.Column("id", uuid, primary_key=True), sa.Column("question_id", uuid, sa.ForeignKey("questions.id", ondelete="CASCADE"), nullable=False), sa.Column("text", sa.Text(), nullable=False), sa.Column("graph_route", sa.String(100), nullable=False), sa.Column("model_name", sa.String(100)), sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False))
    op.create_table("citations", sa.Column("id", uuid, primary_key=True), sa.Column("answer_id", uuid, sa.ForeignKey("answers.id", ondelete="CASCADE"), nullable=False), sa.Column("chunk_id", uuid, sa.ForeignKey("document_chunks.id"), nullable=False), sa.Column("citation_order", sa.Integer(), nullable=False))
    op.create_table("feedback", sa.Column("id", uuid, primary_key=True), sa.Column("answer_id", uuid, sa.ForeignKey("answers.id", ondelete="CASCADE"), nullable=False), sa.Column("user_id", uuid, sa.ForeignKey("users.id"), nullable=False), sa.Column("value", sa.String(20), nullable=False), sa.Column("comment", sa.Text()), sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False))
    op.create_table("evaluation_cases", sa.Column("id", uuid, primary_key=True), sa.Column("question", sa.Text(), nullable=False), sa.Column("expected_answer", sa.Text()), sa.Column("expected_document_ids", sa.dialects.postgresql.JSONB(), nullable=False), sa.Column("should_refuse", sa.Boolean(), nullable=False))
    op.create_table("evaluation_results", sa.Column("id", uuid, primary_key=True), sa.Column("case_id", uuid, sa.ForeignKey("evaluation_cases.id", ondelete="CASCADE"), nullable=False), sa.Column("answer_id", uuid, sa.ForeignKey("answers.id")), sa.Column("metrics", sa.dialects.postgresql.JSONB(), nullable=False), sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False))


def downgrade() -> None:
    for table in ("evaluation_results", "evaluation_cases", "feedback", "citations", "answers", "questions", "document_chunks", "documents", "users"):
        op.drop_table(table)
    op.execute("DROP EXTENSION IF EXISTS vector")
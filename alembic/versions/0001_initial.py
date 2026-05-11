"""initial schema

Revision ID: 0001
Revises:
Create Date: 2026-05-11
"""
from __future__ import annotations

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision = "0001"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute('CREATE EXTENSION IF NOT EXISTS "pgcrypto";')

    op.create_table(
        "organizations",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("name", sa.String, nullable=False, unique=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )

    op.create_table(
        "users",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("email", sa.String, nullable=False, unique=True),
        sa.Column("display_name", sa.String, nullable=False),
        sa.Column("password_hash", sa.String, nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )

    op.create_table(
        "projects",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("organization_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("organizations.id"), nullable=False, index=True),
        sa.Column("name", sa.String, nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.UniqueConstraint("organization_id", "name"),
    )

    op.create_table(
        "memberships",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id"), nullable=False, index=True),
        sa.Column("organization_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("organizations.id"), nullable=False, index=True),
        sa.Column("project_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("projects.id"), nullable=True, index=True),
        sa.Column("role", sa.String, nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.UniqueConstraint("user_id", "organization_id", "project_id", "role"),
    )

    op.create_table(
        "documents",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("project_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("projects.id"), nullable=False, index=True),
        sa.Column("uploader_user_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id"), nullable=False),
        sa.Column("kind", sa.String, nullable=False),
        sa.Column("storage_key", sa.String, nullable=False),
        sa.Column("original_filename", sa.String, nullable=False),
        sa.Column("current_state", sa.String, nullable=False, server_default="UPLOADED"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )

    op.create_table(
        "document_pages",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("document_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("documents.id"), nullable=False, index=True),
        sa.Column("page_number", sa.Integer, nullable=False),
        sa.Column("text", sa.String, nullable=False, server_default=""),
        sa.Column("tokens", postgresql.JSON, nullable=False, server_default="[]"),
        sa.UniqueConstraint("document_id", "page_number"),
    )

    op.create_table(
        "extractions",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("document_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("documents.id"), nullable=False, index=True),
        sa.Column("schema_id", sa.String, nullable=False),
        sa.Column("schema_version", sa.String, nullable=False),
        sa.Column("prompt_version", sa.String, nullable=False),
        sa.Column("model", sa.String, nullable=False),
        sa.Column("model_version", sa.String, nullable=False),
        sa.Column("raw_response", postgresql.JSON, nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )

    op.create_table(
        "extraction_fields",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("extraction_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("extractions.id"), nullable=False, index=True),
        sa.Column("field_path", sa.String, nullable=False),
        sa.Column("value", postgresql.JSON, nullable=False),
        sa.Column("confidence", sa.Float, nullable=False, server_default="0"),
    )

    op.create_table(
        "citations",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("extraction_field_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("extraction_fields.id"), nullable=False, index=True),
        sa.Column("page", sa.Integer, nullable=False),
        sa.Column("bbox", postgresql.JSON, nullable=False),
        sa.Column("source_text", sa.String, nullable=False),
    )

    op.create_table(
        "review_sessions",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("document_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("documents.id"), nullable=False, index=True),
        sa.Column("opened_by_user_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id"), nullable=False),
        sa.Column("opened_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("closed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("outcome", sa.String, nullable=True),
    )

    op.create_table(
        "review_revisions",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("review_session_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("review_sessions.id"), nullable=False, index=True),
        sa.Column("parent_revision_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("review_revisions.id"), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )

    op.create_table(
        "field_edits",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("review_revision_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("review_revisions.id"), nullable=False, index=True),
        sa.Column("extraction_field_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("extraction_fields.id"), nullable=False, index=True),
        sa.Column("previous_value", postgresql.JSON, nullable=False),
        sa.Column("new_value", postgresql.JSON, nullable=False),
        sa.Column("reason", sa.String, nullable=True),
    )

    op.create_table(
        "workflow_transitions",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("document_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("documents.id"), nullable=False, index=True),
        sa.Column("from_state", sa.String, nullable=False),
        sa.Column("to_state", sa.String, nullable=False),
        sa.Column("actor_user_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id"), nullable=True),
        sa.Column("event_name", sa.String, nullable=False),
        sa.Column("event_payload", postgresql.JSON, nullable=False, server_default="{}"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )

    op.create_table(
        "vocabularies",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("slug", sa.String, nullable=False, unique=True),
        sa.Column("display_name", sa.String, nullable=False),
    )

    op.create_table(
        "vocabulary_versions",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("vocabulary_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("vocabularies.id"), nullable=False, index=True),
        sa.Column("version_label", sa.String, nullable=False),
        sa.Column("published_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.UniqueConstraint("vocabulary_id", "version_label"),
    )

    op.create_table(
        "vocabulary_terms",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("vocabulary_version_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("vocabulary_versions.id"), nullable=False, index=True),
        sa.Column("parent_term_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("vocabulary_terms.id"), nullable=True),
        sa.Column("code", sa.String, nullable=False),
        sa.Column("label", sa.String, nullable=False),
        sa.UniqueConstraint("vocabulary_version_id", "code"),
    )

    op.create_table(
        "plans",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("document_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("documents.id"), nullable=False, index=True),
        sa.Column("kind", sa.String, nullable=False),
        sa.Column("status", sa.String, nullable=False, server_default="pending"),
        sa.Column("storage_key", sa.String, nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )

    op.create_table(
        "print_jobs",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("document_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("documents.id"), nullable=True, index=True),
        sa.Column("plan_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("plans.id"), nullable=True, index=True),
        sa.Column("adapter", sa.String, nullable=False),
        sa.Column("status", sa.String, nullable=False, server_default="pending"),
        sa.Column("result_storage_key", sa.String, nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )

    op.create_table(
        "audit_log",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("event_name", sa.String, nullable=False, index=True),
        sa.Column("event_id", postgresql.UUID(as_uuid=True), nullable=False, unique=True),
        sa.Column("actor_user_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("payload", postgresql.JSON, nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )


def downgrade() -> None:
    for t in [
        "audit_log",
        "print_jobs",
        "plans",
        "vocabulary_terms",
        "vocabulary_versions",
        "vocabularies",
        "workflow_transitions",
        "field_edits",
        "review_revisions",
        "review_sessions",
        "citations",
        "extraction_fields",
        "extractions",
        "document_pages",
        "documents",
        "memberships",
        "projects",
        "users",
        "organizations",
    ]:
        op.drop_table(t)

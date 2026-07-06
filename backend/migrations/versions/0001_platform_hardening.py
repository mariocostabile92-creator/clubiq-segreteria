"""platform hardening baseline

Revision ID: 0001_platform_hardening
Revises:
Create Date: 2026-07-06
"""

from alembic import op
import sqlalchemy as sa


revision = "0001_platform_hardening"
down_revision = None
branch_labels = None
depends_on = None


def _columns(table_name):
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    return {column["name"] for column in inspector.get_columns(table_name)}


def _add_column(table_name, column):
    if column.name not in _columns(table_name):
        op.add_column(table_name, column)


def _table_exists(table_name):
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    return table_name in inspector.get_table_names()


def upgrade():
    _add_column("users", sa.Column("email_verified", sa.Boolean(), nullable=False, server_default=sa.false()))
    _add_column("users", sa.Column("email_verification_token", sa.String(), nullable=True))
    _add_column("users", sa.Column("email_verification_expires_at", sa.DateTime(), nullable=True))
    _add_column("users", sa.Column("password_reset_token", sa.String(), nullable=True))
    _add_column("users", sa.Column("password_reset_expires_at", sa.DateTime(), nullable=True))

    _add_column("clubs", sa.Column("plan", sa.String(), nullable=True, server_default="free"))
    _add_column("clubs", sa.Column("subscription_status", sa.String(), nullable=True, server_default="active"))
    _add_column("clubs", sa.Column("admin_notes", sa.Text(), nullable=True))
    _add_column("clubs", sa.Column("stripe_customer_id", sa.String(), nullable=True))
    _add_column("clubs", sa.Column("stripe_subscription_id", sa.String(), nullable=True))
    _add_column("clubs", sa.Column("current_period_end", sa.DateTime(), nullable=True))
    _add_column("clubs", sa.Column("stripe_current_period_end", sa.DateTime(), nullable=True))
    _add_column("clubs", sa.Column("stripe_last_event_id", sa.String(), nullable=True))
    _add_column("clubs", sa.Column("logo", sa.String(), nullable=True))

    _add_column("athletes", sa.Column("photo_url", sa.String(), nullable=True))

    _add_column("parent_requests", sa.Column("certificate_file_url", sa.String(), nullable=True))
    _add_column("parent_requests", sa.Column("payment_receipt_url", sa.String(), nullable=True))
    _add_column("parent_requests", sa.Column("privacy_consent", sa.Boolean(), nullable=False, server_default=sa.false()))
    _add_column("parent_requests", sa.Column("data_processing_consent", sa.Boolean(), nullable=False, server_default=sa.false()))

    if not _table_exists("communications"):
        op.create_table(
            "communications",
            sa.Column("id", sa.Integer(), primary_key=True),
            sa.Column("club_id", sa.Integer(), sa.ForeignKey("clubs.id"), nullable=False),
            sa.Column("user_id", sa.Integer(), sa.ForeignKey("users.id"), nullable=True),
            sa.Column("channel", sa.String(), nullable=False, server_default="whatsapp"),
            sa.Column("type", sa.String(), nullable=False, server_default="WhatsApp"),
            sa.Column("recipient", sa.String(), nullable=False, server_default="Contatto"),
            sa.Column("recipient_email", sa.String(), nullable=True),
            sa.Column("subject", sa.String(), nullable=True),
            sa.Column("phone", sa.String(), nullable=True),
            sa.Column("athlete", sa.String(), nullable=True),
            sa.Column("message", sa.Text(), nullable=False),
            sa.Column("direction", sa.String(), nullable=False, server_default="outbound"),
            sa.Column("status", sa.String(), nullable=False, server_default="opened"),
            sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        )

    if not _table_exists("audit_logs"):
        op.create_table(
            "audit_logs",
            sa.Column("id", sa.Integer(), primary_key=True),
            sa.Column("club_id", sa.Integer(), sa.ForeignKey("clubs.id"), nullable=True),
            sa.Column("user_id", sa.Integer(), sa.ForeignKey("users.id"), nullable=True),
            sa.Column("actor_type", sa.String(), nullable=False, server_default="system"),
            sa.Column("action", sa.String(), nullable=False),
            sa.Column("target_type", sa.String(), nullable=True),
            sa.Column("target_id", sa.String(), nullable=True),
            sa.Column("ip_address", sa.String(), nullable=True),
            sa.Column("user_agent", sa.String(), nullable=True),
            sa.Column("metadata_json", sa.Text(), nullable=True),
            sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        )


def downgrade():
    pass

"""Initial migration to create all tables.

Revision ID: 0001_create_tables
Revises: 
Create Date: 2025-08-10
"""

from alembic import op
import sqlalchemy as sa
import sqlalchemy.dialects.postgresql as psql

revision = '0001_create_tables'
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    # tenants
    op.create_table(
        'tenants',
        sa.Column('id', psql.UUID(as_uuid=True), primary_key=True),
        sa.Column('name', sa.String(), nullable=False),
        sa.Column('slug', sa.String(), nullable=False, unique=True),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.func.now()),
    )
    # users
    op.create_table(
        'users',
        sa.Column('id', psql.UUID(as_uuid=True), primary_key=True),
        sa.Column('tenant_id', psql.UUID(as_uuid=True), sa.ForeignKey('tenants.id'), nullable=False),
        sa.Column('email', sa.String(), nullable=False, unique=True),
        sa.Column('role', sa.String(), nullable=False),
        sa.Column('github_id', sa.String()),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.func.now()),
    )
    # projects
    op.create_table(
        'projects',
        sa.Column('id', psql.UUID(as_uuid=True), primary_key=True),
        sa.Column('tenant_id', psql.UUID(as_uuid=True), sa.ForeignKey('tenants.id'), nullable=False),
        sa.Column('name', sa.String(), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.func.now()),
    )
    # repos
    op.create_table(
        'repos',
        sa.Column('id', psql.UUID(as_uuid=True), primary_key=True),
        sa.Column('project_id', psql.UUID(as_uuid=True), sa.ForeignKey('projects.id'), nullable=False),
        sa.Column('provider', sa.String(), nullable=False),
        sa.Column('external_id', sa.String(), nullable=False),
        sa.Column('name', sa.String(), nullable=False),
        sa.Column('default_branch', sa.String(), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.func.now()),
    )
    # reviews
    op.create_table(
        'reviews',
        sa.Column('id', psql.UUID(as_uuid=True), primary_key=True),
        sa.Column('repo_id', psql.UUID(as_uuid=True), sa.ForeignKey('repos.id'), nullable=False),
        sa.Column('pr_number', sa.String(), nullable=False),
        sa.Column('status', sa.Enum('pending', 'running', 'completed', 'failed', name='reviewstatus'), nullable=False),
        sa.Column('stats_json', psql.JSON(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(), nullable=False, server_default=sa.func.now()),
    )
    # agent_runs
    op.create_table(
        'agent_runs',
        sa.Column('id', psql.UUID(as_uuid=True), primary_key=True),
        sa.Column('review_id', psql.UUID(as_uuid=True), sa.ForeignKey('reviews.id'), nullable=False),
        sa.Column('agent_name', sa.String(), nullable=False),
        sa.Column('status', sa.Enum('pending', 'running', 'completed', 'failed', name='agentrunstatus'), nullable=False),
        sa.Column('duration_ms', sa.Integer(), nullable=True),
        sa.Column('metrics_json', psql.JSON(), nullable=True),
        sa.Column('started_at', sa.DateTime(), nullable=True),
        sa.Column('finished_at', sa.DateTime(), nullable=True),
    )
    # findings
    op.create_table(
        'findings',
        sa.Column('id', psql.UUID(as_uuid=True), primary_key=True),
        sa.Column('review_id', psql.UUID(as_uuid=True), sa.ForeignKey('reviews.id'), nullable=False),
        sa.Column('agent_run_id', psql.UUID(as_uuid=True), sa.ForeignKey('agent_runs.id'), nullable=False),
        sa.Column('file_path', sa.String(), nullable=False),
        sa.Column('start_line', sa.Integer(), nullable=False),
        sa.Column('end_line', sa.Integer(), nullable=False),
        sa.Column('severity', sa.Enum('critical', 'high', 'medium', 'low', 'info', name='severity'), nullable=False),
        sa.Column('title', sa.String(), nullable=False),
        sa.Column('description', sa.Text(), nullable=False),
        sa.Column('suggested_fix', sa.Text(), nullable=True),
        sa.Column('confidence', sa.Float(), nullable=True),
        sa.Column('rule_id', sa.String(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.func.now()),
    )
    # audit_log
    op.create_table(
        'audit_log',
        sa.Column('id', psql.UUID(as_uuid=True), primary_key=True),
        sa.Column('tenant_id', psql.UUID(as_uuid=True), sa.ForeignKey('tenants.id'), nullable=False),
        sa.Column('user_id', psql.UUID(as_uuid=True), sa.ForeignKey('users.id'), nullable=True),
        sa.Column('action', sa.String(), nullable=False),
        sa.Column('entity', sa.String(), nullable=False),
        sa.Column('entity_id', psql.UUID(as_uuid=True), nullable=True),
        sa.Column('metadata', psql.JSON(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.func.now()),
    )
    # api_keys
    op.create_table(
        'api_keys',
        sa.Column('id', psql.UUID(as_uuid=True), primary_key=True),
        sa.Column('tenant_id', psql.UUID(as_uuid=True), sa.ForeignKey('tenants.id'), nullable=False),
        sa.Column('name', sa.String(), nullable=False),
        sa.Column('hashed_key', sa.String(), nullable=False),
        sa.Column('scopes', psql.JSON(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.func.now()),
    )


def downgrade() -> None:
    op.drop_table('api_keys')
    op.drop_table('audit_log')
    op.drop_table('findings')
    op.drop_table('agent_runs')
    op.drop_table('reviews')
    op.drop_table('repos')
    op.drop_table('projects')
    op.drop_table('users')
    op.drop_table('tenants')
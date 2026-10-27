"""create_initial_phase1_schema

Revision ID: 93fa4bfb7ff3
Revises: 
Create Date: 2026-10-27 13:34:22.456479

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '93fa4bfb7ff3'
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

TENANT_TABLES = [
    'audit_log_entries',
    'directory_departments',
    'users',
    'verification_tokens',
    'access_role_grants',
    'directory_courses',
    'identity_sessions',
    'directory_class_sections',
    'directory_enrollments',
    'outbox_events',
]



def upgrade() -> None:
    # 1. Create access_break_glass_sessions
    op.create_table('access_break_glass_sessions',
        sa.Column('id', sa.UUID(), nullable=False),
        sa.Column('operator_user_id', sa.UUID(), nullable=False),
        sa.Column('target_college_id', sa.UUID(), nullable=False),
        sa.Column('reason', sa.Text(), nullable=False),
        sa.Column('expires_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('alert_dispatched', sa.Boolean(), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint('id', name=op.f('pk_access_break_glass_sessions'))
    )
    op.create_index(op.f('ix_access_break_glass_sessions_target_college_id'), 'access_break_glass_sessions', ['target_college_id'], unique=False)

    # 2. Create audit_log_entries
    op.create_table('audit_log_entries',
        sa.Column('id', sa.UUID(), nullable=False),
        sa.Column('sequence_number', sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column('actor_id', sa.UUID(), nullable=True),
        sa.Column('action', sa.String(length=100), nullable=False),
        sa.Column('resource_type', sa.String(length=50), nullable=False),
        sa.Column('resource_id', sa.String(length=100), nullable=False),
        sa.Column('payload', sa.JSON(), nullable=False),
        sa.Column('prev_entry_hash', sa.String(length=64), nullable=False),
        sa.Column('entry_hash', sa.String(length=64), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('college_id', sa.UUID(), nullable=False),
        sa.PrimaryKeyConstraint('id', name=op.f('pk_audit_log_entries')),
        sa.UniqueConstraint('college_id', 'id', name='uq_audit_college_id'),
        sa.UniqueConstraint('college_id', 'sequence_number', name='uq_audit_college_sequence'),
        sa.UniqueConstraint('entry_hash', name=op.f('uq_audit_log_entries_entry_hash'))
    )
    op.create_index(op.f('ix_audit_log_entries_action'), 'audit_log_entries', ['action'], unique=False)
    op.create_index(op.f('ix_audit_log_entries_actor_id'), 'audit_log_entries', ['actor_id'], unique=False)
    op.create_index(op.f('ix_audit_log_entries_college_id'), 'audit_log_entries', ['college_id'], unique=False)
    op.create_index(op.f('ix_audit_log_entries_sequence_number'), 'audit_log_entries', ['sequence_number'], unique=False)
    op.create_index('ix_audit_lookup', 'audit_log_entries', ['college_id', 'action', 'resource_type', 'resource_id'], unique=False)

    # 3. Create colleges (root tenant directory)
    op.create_table('colleges',
        sa.Column('id', sa.UUID(), nullable=False),
        sa.Column('name', sa.String(length=255), nullable=False),
        sa.Column('code', sa.String(length=50), nullable=False),
        sa.Column('domain', sa.String(length=255), nullable=False),
        sa.Column('is_active', sa.Boolean(), nullable=False),
        sa.Column('settings', sa.JSON(), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint('id', name=op.f('pk_colleges'))
    )
    op.create_index(op.f('ix_colleges_code'), 'colleges', ['code'], unique=True)
    op.create_index(op.f('ix_colleges_domain'), 'colleges', ['domain'], unique=True)

    # 4. Create directory_departments
    op.create_table('directory_departments',
        sa.Column('id', sa.UUID(), nullable=False),
        sa.Column('code', sa.String(length=50), nullable=False),
        sa.Column('name', sa.String(length=255), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('college_id', sa.UUID(), nullable=False),
        sa.PrimaryKeyConstraint('id', name=op.f('pk_directory_departments')),
        sa.UniqueConstraint('college_id', 'code', name='uq_departments_college_code'),
        sa.UniqueConstraint('college_id', 'id', name='uq_departments_college_id')
    )
    op.create_index(op.f('ix_directory_departments_college_id'), 'directory_departments', ['college_id'], unique=False)

    # 5. Create outbox_events
    op.create_table('outbox_events',
        sa.Column('id', sa.UUID(), nullable=False),
        sa.Column('college_id', sa.UUID(), nullable=True),
        sa.Column('topic', sa.String(length=100), nullable=False),
        sa.Column('payload', sa.JSON(), nullable=False),
        sa.Column('status', sa.String(length=20), nullable=False),
        sa.Column('retry_count', sa.Integer(), nullable=False),
        sa.Column('last_error', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('processed_at', sa.DateTime(timezone=True), nullable=True),
        sa.PrimaryKeyConstraint('id', name=op.f('pk_outbox_events'))
    )
    op.create_index(op.f('ix_outbox_events_college_id'), 'outbox_events', ['college_id'], unique=False)
    op.create_index(op.f('ix_outbox_events_status'), 'outbox_events', ['status'], unique=False)
    op.create_index(op.f('ix_outbox_events_topic'), 'outbox_events', ['topic'], unique=False)

    # 6. Create users
    op.create_table('users',
        sa.Column('id', sa.UUID(), nullable=False),
        sa.Column('email', sa.String(length=255), nullable=False),
        sa.Column('full_name', sa.String(length=255), nullable=False),
        sa.Column('hashed_password', sa.String(length=255), nullable=True),
        sa.Column('is_email_verified', sa.Boolean(), nullable=False),
        sa.Column('is_active', sa.Boolean(), nullable=False),
        sa.Column('totp_secret', sa.String(length=64), nullable=True),
        sa.Column('is_mfa_enabled', sa.Boolean(), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('college_id', sa.UUID(), nullable=False),
        sa.PrimaryKeyConstraint('id', name=op.f('pk_users')),
        sa.UniqueConstraint('college_id', 'email', name='uq_users_college_email'),
        sa.UniqueConstraint('college_id', 'id', name='uq_users_college_id')
    )
    op.create_index('ix_users_college_email', 'users', ['college_id', 'email'], unique=False)
    op.create_index(op.f('ix_users_college_id'), 'users', ['college_id'], unique=False)

    # 7. Create verification_tokens
    op.create_table('verification_tokens',
        sa.Column('id', sa.UUID(), nullable=False),
        sa.Column('email', sa.String(length=255), nullable=False),
        sa.Column('code_hash', sa.String(length=64), nullable=False),
        sa.Column('purpose', sa.String(length=50), nullable=False),
        sa.Column('expires_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('used_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('college_id', sa.UUID(), nullable=False),
        sa.PrimaryKeyConstraint('id', name=op.f('pk_verification_tokens')),
        sa.UniqueConstraint('college_id', 'id', name='uq_verification_tokens_college_id')
    )
    op.create_index(op.f('ix_verification_tokens_college_id'), 'verification_tokens', ['college_id'], unique=False)
    op.create_index(op.f('ix_verification_tokens_email'), 'verification_tokens', ['email'], unique=False)

    # 8. Create access_role_grants
    op.create_table('access_role_grants',
        sa.Column('id', sa.UUID(), nullable=False),
        sa.Column('user_id', sa.UUID(), nullable=False),
        sa.Column('role', sa.String(length=50), nullable=False),
        sa.Column('scope', sa.JSON(), nullable=False),
        sa.Column('granted_by', sa.UUID(), nullable=True),
        sa.Column('reason', sa.Text(), nullable=False),
        sa.Column('expires_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('is_revoked', sa.Boolean(), nullable=False),
        sa.Column('revoked_by', sa.UUID(), nullable=True),
        sa.Column('revoked_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('college_id', sa.UUID(), nullable=False),
        sa.ForeignKeyConstraint(['college_id', 'user_id'], ['users.college_id', 'users.id'], name='fk_role_grants_user_composite', ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id', name=op.f('pk_access_role_grants')),
        sa.UniqueConstraint('college_id', 'id', name='uq_access_role_grants_college_id')
    )
    op.create_index(op.f('ix_access_role_grants_college_id'), 'access_role_grants', ['college_id'], unique=False)
    op.create_index(op.f('ix_access_role_grants_role'), 'access_role_grants', ['role'], unique=False)
    op.create_index(op.f('ix_access_role_grants_user_id'), 'access_role_grants', ['user_id'], unique=False)
    op.create_index('ix_role_grants_active', 'access_role_grants', ['college_id', 'user_id', 'role', 'is_revoked'], unique=False)

    # 9. Create directory_courses
    op.create_table('directory_courses',
        sa.Column('id', sa.UUID(), nullable=False),
        sa.Column('department_id', sa.UUID(), nullable=False),
        sa.Column('code', sa.String(length=50), nullable=False),
        sa.Column('title', sa.String(length=255), nullable=False),
        sa.Column('credits', sa.Integer(), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('college_id', sa.UUID(), nullable=False),
        sa.ForeignKeyConstraint(['college_id', 'department_id'], ['directory_departments.college_id', 'directory_departments.id'], name='fk_courses_department_composite', ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id', name=op.f('pk_directory_courses')),
        sa.UniqueConstraint('college_id', 'code', name='uq_courses_college_code'),
        sa.UniqueConstraint('college_id', 'id', name='uq_courses_college_id')
    )
    op.create_index(op.f('ix_directory_courses_college_id'), 'directory_courses', ['college_id'], unique=False)
    op.create_index(op.f('ix_directory_courses_department_id'), 'directory_courses', ['department_id'], unique=False)

    # 10. Create identity_sessions
    op.create_table('identity_sessions',
        sa.Column('id', sa.UUID(), nullable=False),
        sa.Column('user_id', sa.UUID(), nullable=False),
        sa.Column('token_hash', sa.String(length=64), nullable=False),
        sa.Column('expires_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('is_revoked', sa.Boolean(), nullable=False),
        sa.Column('ip_address', sa.String(length=45), nullable=True),
        sa.Column('user_agent', sa.String(length=512), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('college_id', sa.UUID(), nullable=False),
        sa.ForeignKeyConstraint(['college_id', 'user_id'], ['users.college_id', 'users.id'], name='fk_sessions_user_composite', ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id', name=op.f('pk_identity_sessions')),
        sa.UniqueConstraint('college_id', 'id', name='uq_identity_sessions_college_id')
    )
    op.create_index(op.f('ix_identity_sessions_college_id'), 'identity_sessions', ['college_id'], unique=False)
    op.create_index(op.f('ix_identity_sessions_token_hash'), 'identity_sessions', ['token_hash'], unique=True)
    op.create_index(op.f('ix_identity_sessions_user_id'), 'identity_sessions', ['user_id'], unique=False)
    op.create_index('ix_sessions_college_user', 'identity_sessions', ['college_id', 'user_id'], unique=False)

    # 11. Create directory_class_sections
    op.create_table('directory_class_sections',
        sa.Column('id', sa.UUID(), nullable=False),
        sa.Column('course_id', sa.UUID(), nullable=False),
        sa.Column('lecturer_id', sa.UUID(), nullable=True),
        sa.Column('section_name', sa.String(length=50), nullable=False),
        sa.Column('semester', sa.Integer(), nullable=False),
        sa.Column('academic_year', sa.String(length=20), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('college_id', sa.UUID(), nullable=False),
        sa.ForeignKeyConstraint(['college_id', 'course_id'], ['directory_courses.college_id', 'directory_courses.id'], name='fk_class_sections_course_composite', ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['college_id', 'lecturer_id'], ['users.college_id', 'users.id'], name='fk_class_sections_lecturer_composite', ondelete='SET NULL'),
        sa.PrimaryKeyConstraint('id', name=op.f('pk_directory_class_sections')),
        sa.UniqueConstraint('college_id', 'id', name='uq_class_sections_college_id')
    )
    op.create_index(op.f('ix_directory_class_sections_college_id'), 'directory_class_sections', ['college_id'], unique=False)
    op.create_index(op.f('ix_directory_class_sections_course_id'), 'directory_class_sections', ['course_id'], unique=False)
    op.create_index(op.f('ix_directory_class_sections_lecturer_id'), 'directory_class_sections', ['lecturer_id'], unique=False)

    # 12. Create directory_enrollments
    op.create_table('directory_enrollments',
        sa.Column('id', sa.UUID(), nullable=False),
        sa.Column('class_section_id', sa.UUID(), nullable=False),
        sa.Column('student_id', sa.UUID(), nullable=False),
        sa.Column('roll_number', sa.String(length=50), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('college_id', sa.UUID(), nullable=False),
        sa.ForeignKeyConstraint(['college_id', 'class_section_id'], ['directory_class_sections.college_id', 'directory_class_sections.id'], name='fk_enrollments_section_composite', ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['college_id', 'student_id'], ['users.college_id', 'users.id'], name='fk_enrollments_student_composite', ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id', name=op.f('pk_directory_enrollments')),
        sa.UniqueConstraint('college_id', 'class_section_id', 'student_id', name='uq_enrollments_student_section'),
        sa.UniqueConstraint('college_id', 'id', name='uq_enrollments_college_id')
    )
    op.create_index(op.f('ix_directory_enrollments_class_section_id'), 'directory_enrollments', ['class_section_id'], unique=False)
    op.create_index(op.f('ix_directory_enrollments_college_id'), 'directory_enrollments', ['college_id'], unique=False)
    op.create_index(op.f('ix_directory_enrollments_student_id'), 'directory_enrollments', ['student_id'], unique=False)

    # 13. Enable and FORCE PostgreSQL Row-Level Security on all tenant tables (NR-2, TN-3)
    for table in TENANT_TABLES:
        op.execute(f"ALTER TABLE {table} ENABLE ROW LEVEL SECURITY;")
        op.execute(f"ALTER TABLE {table} FORCE ROW LEVEL SECURITY;")
        op.execute(f"""
            CREATE POLICY {table}_tenant_isolation_policy ON {table}
            FOR ALL
            USING (college_id = NULLIF(current_setting('app.current_college_id', true), '')::uuid)
            WITH CHECK (college_id = NULLIF(current_setting('app.current_college_id', true), '')::uuid);
        """)

    # 14. Grant DML permissions to campuscare_app (non-owner role)
    op.execute("GRANT SELECT, INSERT, UPDATE, DELETE ON ALL TABLES IN SCHEMA public TO campuscare_app;")
    op.execute("GRANT USAGE, SELECT ON ALL SEQUENCES IN SCHEMA public TO campuscare_app;")


def downgrade() -> None:
    # 1. Drop RLS policies
    for table in TENANT_TABLES:
        op.execute(f"DROP POLICY IF EXISTS {table}_tenant_isolation_policy ON {table};")
        op.execute(f"ALTER TABLE {table} NO FORCE ROW LEVEL SECURITY;")
        op.execute(f"ALTER TABLE {table} DISABLE ROW LEVEL SECURITY;")

    # 2. Drop tables in reverse order
    op.drop_index(op.f('ix_directory_enrollments_student_id'), table_name='directory_enrollments')
    op.drop_index(op.f('ix_directory_enrollments_college_id'), table_name='directory_enrollments')
    op.drop_index(op.f('ix_directory_enrollments_class_section_id'), table_name='directory_enrollments')
    op.drop_table('directory_enrollments')
    op.drop_index(op.f('ix_directory_class_sections_lecturer_id'), table_name='directory_class_sections')
    op.drop_index(op.f('ix_directory_class_sections_course_id'), table_name='directory_class_sections')
    op.drop_index(op.f('ix_directory_class_sections_college_id'), table_name='directory_class_sections')
    op.drop_table('directory_class_sections')
    op.drop_index('ix_sessions_college_user', table_name='identity_sessions')
    op.drop_index(op.f('ix_identity_sessions_user_id'), table_name='identity_sessions')
    op.drop_index(op.f('ix_identity_sessions_token_hash'), table_name='identity_sessions')
    op.drop_index(op.f('ix_identity_sessions_college_id'), table_name='identity_sessions')
    op.drop_table('identity_sessions')
    op.drop_index(op.f('ix_directory_courses_department_id'), table_name='directory_courses')
    op.drop_index(op.f('ix_directory_courses_college_id'), table_name='directory_courses')
    op.drop_table('directory_courses')
    op.drop_index('ix_role_grants_active', table_name='access_role_grants')
    op.drop_index(op.f('ix_access_role_grants_user_id'), table_name='access_role_grants')
    op.drop_index(op.f('ix_access_role_grants_role'), table_name='access_role_grants')
    op.drop_index(op.f('ix_access_role_grants_college_id'), table_name='access_role_grants')
    op.drop_table('access_role_grants')
    op.drop_index(op.f('ix_verification_tokens_email'), table_name='verification_tokens')
    op.drop_index(op.f('ix_verification_tokens_college_id'), table_name='verification_tokens')
    op.drop_table('verification_tokens')
    op.drop_index(op.f('ix_users_college_id'), table_name='users')
    op.drop_index('ix_users_college_email', table_name='users')
    op.drop_table('users')
    op.drop_index(op.f('ix_outbox_events_topic'), table_name='outbox_events')
    op.drop_index(op.f('ix_outbox_events_status'), table_name='outbox_events')
    op.drop_index(op.f('ix_outbox_events_college_id'), table_name='outbox_events')
    op.drop_table('outbox_events')
    op.drop_index(op.f('ix_directory_departments_college_id'), table_name='directory_departments')
    op.drop_table('directory_departments')
    op.drop_index(op.f('ix_colleges_domain'), table_name='colleges')
    op.drop_index(op.f('ix_colleges_code'), table_name='colleges')
    op.drop_table('colleges')
    op.drop_index('ix_audit_lookup', table_name='audit_log_entries')
    op.drop_index(op.f('ix_audit_log_entries_sequence_number'), table_name='audit_log_entries')
    op.drop_index(op.f('ix_audit_log_entries_college_id'), table_name='audit_log_entries')
    op.drop_index(op.f('ix_audit_log_entries_actor_id'), table_name='audit_log_entries')
    op.drop_index(op.f('ix_audit_log_entries_action'), table_name='audit_log_entries')
    op.drop_table('audit_log_entries')
    op.drop_index(op.f('ix_access_break_glass_sessions_target_college_id'), table_name='access_break_glass_sessions')
    op.drop_table('access_break_glass_sessions')

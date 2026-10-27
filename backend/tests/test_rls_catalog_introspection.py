import uuid
import pytest
from sqlalchemy import text
from src.core.database import migrator_engine, app_engine, SessionApp
from src.core.rls import set_tenant_context, clear_tenant_context


def test_catalog_introspection_enforces_forced_rls():
    """Rule TN-4: CI test introspects the catalog and fails if any table with
    college_id lacks enabled and forced RLS policies.
    """
    with migrator_engine.connect() as conn:
        # 1. Find all tables in public schema with college_id column
        find_tables_sql = text("""
            SELECT table_name 
            FROM information_schema.columns 
            WHERE table_schema = 'public' 
              AND column_name = 'college_id'
            ORDER BY table_name;
        """)
        tenant_tables = [row[0] for row in conn.execute(find_tables_sql).fetchall()]

        assert len(tenant_tables) > 0, "Expected at least one tenant-scoped table"

        # 2. Introspect pg_class and pg_policy
        for table in tenant_tables:
            check_rls_sql = text("""
                SELECT 
                    c.relname,
                    c.relrowsecurity,
                    c.relforcerowsecurity,
                    COUNT(p.polname) as policy_count
                FROM pg_class c
                LEFT JOIN pg_policy p ON p.polrelid = c.oid
                WHERE c.relname = :table_name
                GROUP BY c.relname, c.relrowsecurity, c.relforcerowsecurity;
            """)
            result = conn.execute(check_rls_sql, {"table_name": table}).fetchone()
            assert result is not None, f"Table {table} not found in pg_class"

            relname, row_security, force_row_security, policy_count = result

            assert row_security is True, (
                f"Rule TN-4 Violation: Table '{table}' has college_id but ROW LEVEL SECURITY is NOT enabled."
            )
            assert force_row_security is True, (
                f"Rule TN-4 Violation: Table '{table}' has college_id but FORCE ROW LEVEL SECURITY is NOT enabled."
            )
            assert policy_count > 0, (
                f"Rule TN-4 Violation: Table '{table}' has college_id but lacks active RLS policies in pg_policy."
            )


def test_tenant_isolation_fails_closed_and_isolates_data():
    """Rules NR-2, TN-2, TN-3:
    Verifies that when connected as campuscare_app (NOBYPASSRLS):
    1. Unset college_id returns zero rows (fail-closed).
    2. Setting college_A sees only college_A data and cannot see or mutate college_B data.
    """
    college_a = uuid.uuid4()
    college_b = uuid.uuid4()

    # Step 1: Insert records into colleges and departments using migrator
    with migrator_engine.begin() as conn:
        conn.execute(
            text("INSERT INTO colleges (id, name, code, domain, is_active, settings, created_at, updated_at) "
                 "VALUES (:id, 'College A', :code, :domain, true, '{}', now(), now())"),
            {"id": college_a, "code": f"col-a-{college_a.hex[:6]}", "domain": f"a-{college_a.hex[:6]}.edu"},
        )
        conn.execute(
            text("INSERT INTO colleges (id, name, code, domain, is_active, settings, created_at, updated_at) "
                 "VALUES (:id, 'College B', :code, :domain, true, '{}', now(), now())"),
            {"id": college_b, "code": f"col-b-{college_b.hex[:6]}", "domain": f"b-{college_b.hex[:6]}.edu"},
        )

    # Step 2: Connect as non-owner app user
    session = SessionApp()
    try:
        # Test A: Without setting tenant context, querying tenant table returns 0 rows (Fail-Closed)
        clear_tenant_context(session)
        rows_empty = session.execute(text("SELECT * FROM directory_departments")).fetchall()
        assert len(rows_empty) == 0, "Rule TN-2: Query without tenant context must fail closed (0 rows)"

        # Test B: Set context to College A and insert a department
        set_tenant_context(session, college_a)
        dept_a_id = uuid.uuid4()
        session.execute(
            text("INSERT INTO directory_departments (id, college_id, code, name, created_at) "
                 "VALUES (:id, :college_id, 'CSE', 'Computer Science A', now())"),
            {"id": dept_a_id, "college_id": college_a},
        )
        session.commit()

        # Test C: Set context to College B and insert a department
        set_tenant_context(session, college_b)
        dept_b_id = uuid.uuid4()
        session.execute(
            text("INSERT INTO directory_departments (id, college_id, code, name, created_at) "
                 "VALUES (:id, :college_id, 'MECH', 'Mechanical B', now())"),
            {"id": dept_b_id, "college_id": college_b},
        )
        session.commit()

        # Test D: Verify College B query only sees College B department
        set_tenant_context(session, college_b)
        b_departments = session.execute(text("SELECT id, name FROM directory_departments")).fetchall()
        b_ids = [row[0] for row in b_departments]
        assert dept_b_id in b_ids, "College B should see its own department"
        assert dept_a_id not in b_ids, "Rule NR-2 Violation: College B can see College A department!"

        # Test E: Verify cross-tenant insert is rejected by RLS WITH CHECK
        with pytest.raises(Exception):
            session.execute(
                text("INSERT INTO directory_departments (id, college_id, code, name, created_at) "
                     "VALUES (:id, :college_id, 'ILLEGAL', 'Cross College Dept', now())"),
                {"id": uuid.uuid4(), "college_id": college_a},  # Context is college_b, trying to insert college_a
            )
            session.commit()
        session.rollback()

    finally:
        session.close()

import uuid
from datetime import date, time
import pytest
from sqlalchemy import text
from src.core.database import SessionApp, migrator_engine
from src.modules.attendance.service import (
    AttendanceService,
    SessionCreateRequest,
    AttendanceOpEntry,
)


@pytest.fixture
def setup_attendance_fixture():
    college_id = uuid.uuid4()
    lecturer_id = uuid.uuid4()
    dept_id = uuid.uuid4()
    course_id = uuid.uuid4()
    section_id = uuid.uuid4()
    student_1 = uuid.uuid4()
    student_2 = uuid.uuid4()

    with migrator_engine.begin() as conn:
        conn.execute(
            text("INSERT INTO colleges (id, name, code, domain, is_active, settings, created_at, updated_at) "
                 "VALUES (:id, 'Attendance Test College', :code, :domain, true, '{}', now(), now())"),
            {"id": college_id, "code": f"col-att-{college_id.hex[:6]}", "domain": f"att-{college_id.hex[:6]}.edu"},
        )
        conn.execute(text(f"SET LOCAL app.current_college_id = '{college_id}'"))

        # Users
        conn.execute(
            text("INSERT INTO users (id, college_id, email, full_name, is_email_verified, is_active, is_mfa_enabled, created_at, updated_at) "
                 "VALUES (:id, :cid, 'lecturer@att.edu', 'Prof. Alan Turing', true, true, false, now(), now())"),
            {"id": lecturer_id, "cid": college_id},
        )
        conn.execute(
            text("INSERT INTO users (id, college_id, email, full_name, is_email_verified, is_active, is_mfa_enabled, created_at, updated_at) "
                 "VALUES (:id, :cid, 'student1@att.edu', 'Student One', true, true, false, now(), now())"),
            {"id": student_1, "cid": college_id},
        )
        conn.execute(
            text("INSERT INTO users (id, college_id, email, full_name, is_email_verified, is_active, is_mfa_enabled, created_at, updated_at) "
                 "VALUES (:id, :cid, 'student2@att.edu', 'Student Two', true, true, false, now(), now())"),
            {"id": student_2, "cid": college_id},
        )

        # Department & Course & Section
        conn.execute(
            text("INSERT INTO directory_departments (id, college_id, code, name, created_at) "
                 "VALUES (:id, :cid, 'CS-ATT', 'Computer Science', now())"),
            {"id": dept_id, "cid": college_id},
        )
        conn.execute(
            text("INSERT INTO directory_courses (id, college_id, department_id, code, title, credits, created_at) "
                 "VALUES (:id, :cid, :dept_id, 'CS201', 'Data Structures', 4, now())"),
            {"id": course_id, "cid": college_id, "dept_id": dept_id},
        )
        conn.execute(
            text("INSERT INTO directory_class_sections (id, college_id, course_id, lecturer_id, section_name, semester, academic_year, created_at) "
                 "VALUES (:id, :cid, :course_id, :lecturer_id, 'Section B', 4, '2026-2027', now())"),
            {"id": section_id, "cid": college_id, "course_id": course_id, "lecturer_id": lecturer_id},
        )

    return college_id, lecturer_id, section_id, student_1, student_2


def test_offline_attendance_sync_and_optimistic_concurrency(setup_attendance_fixture):
    """Rule C7 & ADR-005: Offline attendance synchronization with op_id idempotency
    and base_version optimistic concurrency conflict detection.
    """
    college_id, lecturer_id, section_id, student_1, student_2 = setup_attendance_fixture

    with SessionApp() as db:
        # Step 1: Create session (version initialized to 1)
        session_req = SessionCreateRequest(
            class_section_id=section_id,
            session_date=date(2026, 10, 27),
            start_time=time(9, 0),
            end_time=time(10, 0),
            topic="Binary Search Trees",
        )
        session = AttendanceService.create_session(db, college_id, lecturer_id, session_req)
        assert session.version == 1

        # Step 2: Sync batch from offline device with base_version=1
        op1 = AttendanceOpEntry(
            op_id=str(uuid.uuid4()),
            session_id=session.id,
            class_section_id=section_id,
            base_version=1,
            student_records=[
                {"student_id": str(student_1), "status": "PRESENT"},
                {"student_id": str(student_2), "status": "ABSENT"},
            ],
        )
        outcomes1 = AttendanceService.sync_batch_operations(db, college_id, lecturer_id, [op1])

        assert len(outcomes1) == 1
        assert outcomes1[0].op_id == op1.op_id
        assert outcomes1[0].outcome == "applied"
        assert outcomes1[0].server_version == 2

        # Step 3: Verify tamper-evident audit ledger entry recorded (Rule B3)
        audit_entry = db.execute(
            text("SELECT action, resource_id, prev_entry_hash, entry_hash FROM audit_log_entries WHERE college_id = :cid ORDER BY sequence_number DESC LIMIT 1"),
            {"cid": college_id},
        ).fetchone()
        assert audit_entry is not None
        assert audit_entry[0] == "ATTENDANCE_MARKED"
        assert audit_entry[1] == str(session.id)
        assert len(audit_entry[3]) == 64

        # Step 4: Simulate concurrent offline device attempting sync with stale base_version=1 (Rule C7.3)
        stale_op = AttendanceOpEntry(
            op_id=str(uuid.uuid4()),
            session_id=session.id,
            class_section_id=section_id,
            base_version=1,  # Stale: server is now at version 2
            student_records=[
                {"student_id": str(student_1), "status": "ABSENT"},
                {"student_id": str(student_2), "status": "PRESENT"},
            ],
        )
        conflict_outcomes = AttendanceService.sync_batch_operations(db, college_id, lecturer_id, [stale_op])

        assert len(conflict_outcomes) == 1
        assert conflict_outcomes[0].op_id == stale_op.op_id
        assert conflict_outcomes[0].outcome == "conflict"
        assert conflict_outcomes[0].server_version == 2
        assert "Concurrent modification detected" in conflict_outcomes[0].reason
        assert len(conflict_outcomes[0].server_records) == 2

        # Step 5: Offline device resolves conflict by re-syncing against latest base_version=2
        resolved_op = AttendanceOpEntry(
            op_id=str(uuid.uuid4()),
            session_id=session.id,
            class_section_id=section_id,
            base_version=2,
            student_records=[
                {"student_id": str(student_1), "status": "PRESENT"},
                {"student_id": str(student_2), "status": "PRESENT"},  # Resolved to PRESENT
            ],
        )
        resolved_outcomes = AttendanceService.sync_batch_operations(db, college_id, lecturer_id, [resolved_op])

        assert len(resolved_outcomes) == 1
        assert resolved_outcomes[0].outcome == "applied"
        assert resolved_outcomes[0].server_version == 3

import uuid
from datetime import datetime, timezone
import pytest
from src.core.database import SessionApp, migrator_engine
from src.modules.complaints.service import (
    ComplaintsService,
    ComplaintCreate,
    AssignComplaintRequest,
    ResolveComplaintRequest,
    ResolutionConfirmRequest,
)
from src.modules.access.policy import Actor
from sqlalchemy import text


@pytest.fixture
def setup_college_and_users():
    college_id = uuid.uuid4()
    student_id = uuid.uuid4()
    staff_id = uuid.uuid4()

    with migrator_engine.begin() as conn:
        conn.execute(
            text("INSERT INTO colleges (id, name, code, domain, is_active, settings, created_at, updated_at) "
                 "VALUES (:id, 'Test College Complaints', :code, :domain, true, '{}', now(), now())"),
            {"id": college_id, "code": f"col-cmp-{college_id.hex[:6]}", "domain": f"cmp-{college_id.hex[:6]}.edu"},
        )
        conn.execute(text(f"SET LOCAL app.current_college_id = '{college_id}'"))
        conn.execute(
            text("INSERT INTO users (id, college_id, email, full_name, is_email_verified, is_active, is_mfa_enabled, created_at, updated_at) "
                 "VALUES (:id, :cid, 'student@test.edu', 'Test Student', true, true, false, now(), now())"),
            {"id": student_id, "cid": college_id},
        )
        conn.execute(
            text("INSERT INTO users (id, college_id, email, full_name, is_email_verified, is_active, is_mfa_enabled, created_at, updated_at) "
                 "VALUES (:id, :cid, 'staff@test.edu', 'Test Staff', true, true, false, now(), now())"),
            {"id": staff_id, "cid": college_id},
        )

    return college_id, student_id, staff_id


def test_complaints_service_promise_and_closed_loop_lifecycle(setup_college_and_users):
    """Rule B3: Service promise countdown, location-tagged reporting, and closed-loop resolution."""
    college_id, student_id, staff_id = setup_college_and_users

    with SessionApp() as db:
        # Step 1: Create complaint with location tag and committed SLA
        create_data = ComplaintCreate(
            category="FACILITY",
            title="Broken Projector HDMI Cable",
            description="The projector cable in room 302 is damaged.",
            location_tag="QR:LAB-BLOCK-302",
            is_sensitive=False,
            sla_committed_hours=48,
        )
        complaint = ComplaintsService.create_complaint(db, college_id, student_id, create_data)

        assert complaint.ticket_number.startswith("CC-")
        assert complaint.status == "SUBMITTED"
        assert complaint.location_tag == "QR:LAB-BLOCK-302"
        assert complaint.sla_committed_hours == 48
        assert complaint.sla_deadline > datetime.now(timezone.utc)

        # Step 2: Assign complaint to staff
        assigned = ComplaintsService.assign_complaint(
            db,
            college_id,
            complaint.id,
            staff_id,
            AssignComplaintRequest(assigned_to_user_id=staff_id, comment="Investigating cable replacement"),
        )
        assert assigned.status == "ASSIGNED"
        assert assigned.assigned_to_user_id == staff_id

        # Step 3: Staff resolves complaint
        resolved = ComplaintsService.resolve_complaint(
            db,
            college_id,
            complaint.id,
            staff_id,
            ResolveComplaintRequest(resolution_note="Replaced HDMI cable with new braided cable."),
        )
        assert resolved.status == "RESOLVED"
        assert resolved.resolved_at is not None

        # Step 4: Closed-Loop Resolution Confirmation by student (Rule B3)
        confirmed = ComplaintsService.confirm_or_reopen(
            db,
            college_id,
            complaint.id,
            student_id,
            ResolutionConfirmRequest(student_confirmed=True, feedback_rating=5, feedback_comment="Working great!"),
        )
        assert confirmed.status == "CLOSED"
        assert confirmed.student_confirmed is True
        assert confirmed.student_feedback_rating == 5
        assert confirmed.closed_at is not None

        # Step 5: Verify tamper-evident audit ledger entry recorded
        audit_row = db.execute(
            text("SELECT action, prev_entry_hash, entry_hash FROM audit_log_entries WHERE college_id = :cid ORDER BY sequence_number DESC LIMIT 1"),
            {"cid": college_id},
        ).fetchone()

        assert audit_row is not None
        assert audit_row[0] == "COMPLAINT_CONFIRMED_CLOSED"
        assert len(audit_row[2]) == 64  # SHA-256 hash

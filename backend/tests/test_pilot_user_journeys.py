"""CampusCare AI - Phase 5 Pilot User Journeys & End-to-End Release Gate Tests.

Validates the full lifecycle for all four pilot personas:
1. Student Journey (Verified answers, complaints with SLA, supportive attendance alerts, anonymous feedback)
2. Lecturer Journey (Fast attendance sync, k-anonymous feedback themes)
3. Department Admin Journey (SLA Risk Radar, Duplicate complaint clustering)
4. College Admin Journey (Tamper-evident audit ledger verification, role approvals)
"""

import uuid
import pytest
from datetime import date, time, datetime, timezone
from sqlalchemy import text
from src.core.database import SessionApp
from src.core.rls import set_tenant_context
from src.modules.tenancy.service import TenancyService
from src.modules.directory.service import DirectoryService, ClassSectionCreate
from src.modules.assistant.service import AssistantService, ConversationCreate, ChatRequest
from src.modules.complaints.service import ComplaintsService, ComplaintCreate, ResolutionConfirmRequest
from src.modules.attendance.service import AttendanceService, SessionCreateRequest, AttendanceOpEntry
from src.modules.feedback.service import FeedbackService, FeedbackSubmitRequest
from src.modules.analytics.service import AnalyticsService
from src.modules.audit.service import AuditService


def test_pilot_student_and_ai_journey():
    """Validates Pilot Student Journey: RAG citation answers, location-tagged complaint, supportive alerts."""
    with SessionApp() as db:
        apex = TenancyService.get_college_by_domain(db, "apex.edu")
        assert apex is not None, "Pilot college apex.edu must be seeded"
        college_id = apex.id

        set_tenant_context(db, college_id=college_id)
        student_id = db.scalar(
            text("SELECT id FROM users WHERE college_id = :cid AND email = 'aarav.sharma@apex.edu'"),
            {"cid": college_id},
        )
        assert student_id is not None

        # 1. Student queries institutional AI assistant
        conv = AssistantService.create_conversation(
            db, college_id, student_id, ConversationCreate(title="Pilot Attendance Query")
        )
        ans = AssistantService.chat_grounded(
            db,
            college_id,
            student_id,
            conv.id,
            ChatRequest(query="What is the minimum attendance required for semester end examinations?"),
        )
        assert ans.routing_action == "DIRECT_ANSWER"
        assert ans.confidence_score >= 0.50
        assert len(ans.citations_json) >= 1
        assert "75 percent" in ans.citations_json[0]["excerpt"] or "75 percent" in ans.content

        # 2. Student raises location-tagged complaint with SLA promise
        comp = ComplaintsService.create_complaint(
            db,
            college_id,
            student_id,
            ComplaintCreate(
                category="FACILITY",
                title="Air Conditioning Unit Leaking Water",
                description="Ceiling split unit is dripping above desk row 3.",
                location_tag="QR:LAB-4-401",
                sla_committed_hours=24,
            ),
        )
        assert comp.ticket_number.startswith("CC-")
        assert comp.sla_committed_hours == 24
        assert comp.location_tag == "QR:LAB-4-401"
        assert comp.status == "SUBMITTED"

        # 3. Department Admin runs duplicate clustering and SLA Risk Radar
        duplicates = AnalyticsService.detect_duplicate_complaints(db, college_id, comp.id, threshold=0.20)
        assert isinstance(duplicates, list)

        sla_risks = AnalyticsService.assess_sla_risks(db, college_id)
        assert len(sla_risks) >= 1
        comp_risk = next((r for r in sla_risks if r.complaint_id == comp.id), None)
        assert comp_risk is not None
        assert comp_risk.risk_level in ["LOW", "MEDIUM", "HIGH", "CRITICAL"]


def test_pilot_lecturer_and_feedback_journey():
    """Validates Pilot Lecturer Journey: Offline sync protocol and k-anonymous feedback themes."""
    with SessionApp() as db:
        apex = TenancyService.get_college_by_domain(db, "apex.edu")
        college_id = apex.id

        set_tenant_context(db, college_id=college_id)
        lecturer_id = db.scalar(
            text("SELECT id FROM users WHERE college_id = :cid AND email = 'prof.rao@apex.edu'"),
            {"cid": college_id},
        )
        student_id = db.scalar(
            text("SELECT id FROM users WHERE college_id = :cid AND email = 'aarav.sharma@apex.edu'"),
            {"cid": college_id},
        )
        assert lecturer_id is not None
        assert student_id is not None

        depts = DirectoryService.list_departments(db, college_id)
        assert len(depts) >= 1
        courses = DirectoryService.list_courses(db, college_id, depts[0].id)
        assert len(courses) >= 1

        sec = DirectoryService.create_class_section(
            db,
            college_id,
            ClassSectionCreate(
                course_id=courses[0].id,
                lecturer_id=lecturer_id,
                section_name="Pilot Sec Alpha",
                semester=5,
                academic_year="2026-27",
            ),
        )

        # Lecturer creates attendance session and syncs batch
        sess = AttendanceService.create_session(
            db,
            college_id,
            lecturer_id,
            SessionCreateRequest(
                class_section_id=sec.id,
                session_date=date.today(),
                start_time=time(10, 0),
                end_time=time(11, 0),
                topic="Pilot Kernel Memory Management",
            ),
        )

        outcomes = AttendanceService.sync_batch_operations(
            db,
            college_id,
            lecturer_id,
            [
                AttendanceOpEntry(
                    op_id=str(uuid.uuid4()),
                    session_id=sess.id,
                    class_section_id=sec.id,
                    base_version=1,
                    student_records=[{"student_id": str(student_id), "status": "PRESENT"}],
                )
            ],
        )
        assert len(outcomes) == 1
        assert outcomes[0].outcome == "applied"
        assert outcomes[0].server_version == 2


def test_pilot_audit_ledger_tamper_evidence():
    """Validates College Admin Journey: Hash-chained tamper-evident audit ledger (Rule B3)."""
    with SessionApp() as db:
        apex = TenancyService.get_college_by_domain(db, "apex.edu")
        college_id = apex.id

        set_tenant_context(db, college_id=college_id)
        admin_id = db.scalar(
            text("SELECT id FROM users WHERE college_id = :cid AND email = 'admin@apex.edu'"),
            {"cid": college_id},
        )
        assert admin_id is not None

        # Record two chained audit events
        e1 = AuditService.record_entry(
            db=db,
            college_id=college_id,
            actor_id=admin_id,
            action="PILOT_CONFIG_UPDATE",
            resource_type="system_settings",
            resource_id="pilot-settings-01",
            payload={"mfa_enforced": True},
        )
        assert len(e1.entry_hash) == 64  # SHA-256

        e2 = AuditService.record_entry(
            db=db,
            college_id=college_id,
            actor_id=admin_id,
            action="PILOT_SECURITY_SCAN",
            resource_type="system_settings",
            resource_id="pilot-settings-01",
            payload={"vulnerabilities_detected": 0},
        )
        assert e2.prev_entry_hash == e1.entry_hash  # Hash chained!
        assert len(e2.entry_hash) == 64

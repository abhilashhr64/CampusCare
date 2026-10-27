import uuid
from datetime import datetime, timezone, timedelta, date, time
import pytest
from sqlalchemy import text
from src.core.database import SessionApp, migrator_engine
from src.modules.complaints.service import ComplaintsService, ComplaintCreate
from src.modules.feedback.service import (
    FeedbackService,
    FeedbackCycleCreate,
    FeedbackSubmitRequest,
)
from src.modules.directory.service import (
    DirectoryService,
    DepartmentCreate,
    CourseCreate,
    ClassSectionCreate,
)
from src.modules.attendance.service import AttendanceService, SessionCreateRequest, AttendanceOpEntry
from src.modules.analytics.service import AnalyticsService
from src.modules.notifications.service import NotificationService


@pytest.fixture
def setup_intelligence_test_env():
    college_1 = uuid.uuid4()
    college_2 = uuid.uuid4()
    student_c1 = uuid.uuid4()
    student_c2 = uuid.uuid4()
    lecturer_c1 = uuid.uuid4()

    with migrator_engine.begin() as conn:
        # College 1
        conn.execute(
            text("INSERT INTO colleges (id, name, code, domain, is_active, settings, created_at, updated_at) "
                 "VALUES (:id, 'Apex Institute of Tech', :code, :domain, true, '{}', now(), now())"),
            {"id": college_1, "code": f"col-int1-{college_1.hex[:6]}", "domain": f"int1-{college_1.hex[:6]}.edu"},
        )
        conn.execute(text(f"SET LOCAL app.current_college_id = '{college_1}'"))
        conn.execute(
            text("INSERT INTO users (id, college_id, email, full_name, is_email_verified, is_active, is_mfa_enabled, created_at, updated_at) "
                 "VALUES (:id, :cid, 'student@int1.edu', 'Student C1', true, true, false, now(), now())"),
            {"id": student_c1, "cid": college_1},
        )
        conn.execute(
            text("INSERT INTO users (id, college_id, email, full_name, is_email_verified, is_active, is_mfa_enabled, created_at, updated_at) "
                 "VALUES (:id, :cid, 'lecturer@int1.edu', 'Prof Alan Turing', true, true, true, now(), now())"),
            {"id": lecturer_c1, "cid": college_1},
        )

        # College 2
        conn.execute(
            text("INSERT INTO colleges (id, name, code, domain, is_active, settings, created_at, updated_at) "
                 "VALUES (:id, 'Horizon Polytechnic', :code, :domain, true, '{}', now(), now())"),
            {"id": college_2, "code": f"col-int2-{college_2.hex[:6]}", "domain": f"int2-{college_2.hex[:6]}.edu"},
        )
        conn.execute(text(f"SET LOCAL app.current_college_id = '{college_2}'"))
        conn.execute(
            text("INSERT INTO users (id, college_id, email, full_name, is_email_verified, is_active, is_mfa_enabled, created_at, updated_at) "
                 "VALUES (:id, :cid, 'student@int2.edu', 'Student C2', true, true, false, now(), now())"),
            {"id": student_c2, "cid": college_2},
        )

    return college_1, college_2, student_c1, student_c2, lecturer_c1


def test_duplicate_complaint_detection_and_tenant_isolation(setup_intelligence_test_env):
    """Rule B3, TN-6: Duplicate detection clusters overlapping/co-located tickets within tenant.
    Never clusters across tenant boundaries.
    """
    college_1, college_2, student_c1, student_c2, _ = setup_intelligence_test_env

    with SessionApp() as db:
        # College 1: Complaint A
        comp_a = ComplaintsService.create_complaint(
            db,
            college_1,
            student_c1,
            ComplaintCreate(
                category="FACILITY",
                title="Broken Projector HDMI Cable in Lab 302",
                description="The projector cable in Lab 302 has a bent pin and shows no signal.",
                location_tag="QR:LAB-BLOCK-302",
                sla_committed_hours=48,
            ),
        )

        # College 1: Complaint B (Duplicate reported by another student)
        comp_b = ComplaintsService.create_complaint(
            db,
            college_1,
            student_c1,
            ComplaintCreate(
                category="FACILITY",
                title="Lab 302 Projector Display Not Working",
                description="Projector HDMI cable broken in Lab 302, screen is flickering black.",
                location_tag="QR:LAB-BLOCK-302",
                sla_committed_hours=48,
            ),
        )

        # College 2: Identical text but in College 2
        comp_c2 = ComplaintsService.create_complaint(
            db,
            college_2,
            student_c2,
            ComplaintCreate(
                category="FACILITY",
                title="Broken Projector HDMI Cable in Lab 302",
                description="The projector cable in Lab 302 has a bent pin and shows no signal.",
                location_tag="QR:LAB-BLOCK-302",
                sla_committed_hours=48,
            ),
        )

        # Run duplicate detection in College 1 on Complaint A
        clusters_c1 = AnalyticsService.detect_duplicate_complaints(db, college_1, comp_a.id)
        assert len(clusters_c1) > 0
        assert clusters_c1[0].canonical_complaint_id == comp_a.id
        assert clusters_c1[0].duplicate_complaint_id == comp_b.id
        assert clusters_c1[0].similarity_score >= 0.50
        assert clusters_c1[0].detected_reason == "CO_LOCATED_AND_TEXT_OVERLAP"

        # Rule TN-6 Enforcement: Verify College 2's complaint was NOT clustered into College 1
        dup_ids = [c.duplicate_complaint_id for c in clusters_c1]
        assert comp_c2.id not in dup_ids, "Security Violation: Cross-tenant duplicate ticket detected!"


def test_sla_risk_forecasting(setup_intelligence_test_env):
    """Rule B1, B3: Department admin SLA risk radar calculates breach risk and prioritizes urgent tickets."""
    college_1, _, student_c1, _, _ = setup_intelligence_test_env

    with SessionApp() as db:
        # Create an urgent complaint with 4 hours remaining
        urgent_comp = ComplaintsService.create_complaint(
            db,
            college_1,
            student_c1,
            ComplaintCreate(
                category="FACILITY",
                title="Critical Water Leak in Physics Server Room",
                description="Water pipe leaking near main power distribution unit.",
                location_tag="QR:SERVER-RM-101",
                sla_committed_hours=4,
            ),
        )

        # Create a normal complaint with 48 hours remaining
        normal_comp = ComplaintsService.create_complaint(
            db,
            college_1,
            student_c1,
            ComplaintCreate(
                category="FACILITY",
                title="Desk Drawer Jammed in Classroom 204",
                description="Left side drawer handle is loose.",
                location_tag="QR:CLASS-204",
                sla_committed_hours=48,
            ),
        )

        # Run SLA risk assessment
        risks = AnalyticsService.assess_sla_risks(db, college_1)
        assert len(risks) >= 2

        urgent_risk = next(r for r in risks if r.complaint_id == urgent_comp.id)
        assert urgent_risk.risk_level == "CRITICAL"
        assert urgent_risk.hours_remaining <= 4.1
        assert urgent_risk.projected_breach_probability >= 0.90

        normal_risk = next(r for r in risks if r.complaint_id == normal_comp.id)
        assert normal_risk.risk_level in ["LOW", "MEDIUM"]
        assert normal_risk.hours_remaining > 30.0


def test_supportive_attendance_deficit_alerts(setup_intelligence_test_env):
    """Rule B1, B3: Supportive attendance alerts notify students before threshold breach with exact recovery counts."""
    college_1, _, student_c1, _, lecturer_c1 = setup_intelligence_test_env

    with SessionApp() as db:
        dept = DirectoryService.create_department(
            db, college_1, DepartmentCreate(code=f"CSE-{college_1.hex[:4]}", name="Computer Science")
        )
        course = DirectoryService.create_course(
            db, college_1, CourseCreate(department_id=dept.id, code="CS401", title="Distributed Algorithms")
        )
        section = DirectoryService.create_class_section(
            db,
            college_1,
            ClassSectionCreate(
                course_id=course.id,
                lecturer_id=lecturer_c1,
                section_name="Section A",
                semester=7,
                academic_year="2026-27",
            ),
        )

        # Enroll student
        with migrator_engine.begin() as conn:
            conn.execute(text(f"SET LOCAL app.current_college_id = '{college_1}'"))
            conn.execute(
                text("INSERT INTO directory_enrollments (id, college_id, student_id, class_section_id, roll_number, created_at) "
                     "VALUES (gen_random_uuid(), :cid, :sid, :sec_id, '26CS01', now())"),
                {"cid": college_1, "sid": student_c1, "sec_id": section.id},
            )

        # Record 10 sessions: 6 attended (PRESENT), 4 missed (ABSENT) -> 60% (Below 75%)
        for i in range(10):
            sess = AttendanceService.create_session(
                db,
                college_1,
                lecturer_c1,
                SessionCreateRequest(
                    class_section_id=section.id,
                    session_date=date.today(),
                    start_time=time(9, 0),
                    end_time=time(10, 0),
                    topic=f"Lecture {i+1}",
                ),
            )
            status = "PRESENT" if i < 6 else "ABSENT"
            AttendanceService.sync_batch_operations(
                db,
                college_1,
                lecturer_c1,
                [
                    AttendanceOpEntry(
                        op_id=str(uuid.uuid4()),
                        session_id=sess.id,
                        class_section_id=section.id,
                        base_version=1,
                        student_records=[{"student_id": str(student_c1), "status": status}],
                    )
                ],
            )

        # Run attendance risk alerts scan
        alerts = AnalyticsService.generate_supportive_attendance_alerts(db, college_1, target_percentage=75.0)
        assert len(alerts) > 0
        student_alert = next(a for a in alerts if a.student_id == student_c1)
        assert student_alert.current_percentage == 60.0
        assert student_alert.conducted_count == 10
        assert student_alert.attended_count == 6
        # To reach 75% from 6/10: (6 + c) / (10 + c) = 0.75 => 6 + c = 7.5 + 0.75c => 0.25c = 1.5 => c = 6
        assert student_alert.classes_needed_for_safe == 6

        # Check delivered notification
        inbox = NotificationService.list_user_notifications(db, college_1, student_c1)
        assert len(inbox) > 0
        assert "Supportive Attendance Alert" in inbox[0].subject
        assert "6 consecutive classes" in inbox[0].body


def test_feedback_thematic_extraction_under_k_anonymity(setup_intelligence_test_env):
    """Rule NR-10 & ADR-004: Qualitative feedback theme extraction enforces k >= 5 gate."""
    college_1, _, _, _, lecturer_c1 = setup_intelligence_test_env

    with SessionApp() as db:
        dept = DirectoryService.create_department(
            db, college_1, DepartmentCreate(code=f"ECE-{college_1.hex[:4]}", name="Electronics")
        )
        course = DirectoryService.create_course(
            db, college_1, CourseCreate(department_id=dept.id, code="EC301", title="Digital Signal Processing")
        )
        section = DirectoryService.create_class_section(
            db,
            college_1,
            ClassSectionCreate(
                course_id=course.id,
                lecturer_id=lecturer_c1,
                section_name="Section B",
                semester=5,
                academic_year="2026-27",
            ),
        )

        cycle = FeedbackService.create_cycle(
            db,
            college_1,
            FeedbackCycleCreate(title="Fall 2026 Evaluation", academic_term="2026-FALL", k_anonymity_threshold=5),
        )

        # Create 3 voters (< 5 threshold)
        voter_students = [uuid.uuid4() for _ in range(3)]
        with migrator_engine.begin() as conn:
            conn.execute(text(f"SET LOCAL app.current_college_id = '{college_1}'"))
            for s_id in voter_students:
                conn.execute(
                    text("INSERT INTO users (id, college_id, email, full_name, is_email_verified, is_active, is_mfa_enabled, created_at, updated_at) "
                         "VALUES (:id, :cid, :email, 'Voter', true, true, false, now(), now())"),
                    {"id": s_id, "cid": college_1, "email": f"voter-{s_id.hex[:6]}@apex.edu"},
                )

        for s_id in voter_students:
            FeedbackService.submit_anonymous_feedback(
                db,
                college_1,
                s_id,
                FeedbackSubmitRequest(
                    cycle_id=cycle.id,
                    class_section_id=section.id,
                    course_id=course.id,
                    lecturer_id=lecturer_c1,
                    rating_pedagogy=4,
                    rating_clarity=4,
                    rating_engagement=4,
                    rating_punctuality=5,
                    comment="Great lab practical hardware explanations but lecture pace is slightly fast.",
                ),
            )

        # Attempt extraction with k < 5 -> Must raise ValueError (Rule NR-10)
        with pytest.raises(ValueError, match="k-anonymity gate enforced"):
            AnalyticsService.aggregate_feedback_themes(db, college_1, cycle.id, lecturer_c1)

        # Now add 2 more voters to reach k = 5
        more_voters = [uuid.uuid4() for _ in range(2)]
        with migrator_engine.begin() as conn:
            conn.execute(text(f"SET LOCAL app.current_college_id = '{college_1}'"))
            for s_id in more_voters:
                conn.execute(
                    text("INSERT INTO users (id, college_id, email, full_name, is_email_verified, is_active, is_mfa_enabled, created_at, updated_at) "
                         "VALUES (:id, :cid, :email, 'Voter', true, true, false, now(), now())"),
                    {"id": s_id, "cid": college_1, "email": f"voter-{s_id.hex[:6]}@apex.edu"},
                )

        for s_id in more_voters:
            FeedbackService.submit_anonymous_feedback(
                db,
                college_1,
                s_id,
                FeedbackSubmitRequest(
                    cycle_id=cycle.id,
                    class_section_id=section.id,
                    course_id=course.id,
                    lecturer_id=lecturer_c1,
                    rating_pedagogy=5,
                    rating_clarity=5,
                    rating_engagement=5,
                    rating_punctuality=5,
                    comment="Excellent doubt resolution and interactive hardware experiment demonstrations.",
                ),
            )

        # k >= 5 reached! Extraction must succeed
        themes = AnalyticsService.aggregate_feedback_themes(db, college_1, cycle.id, lecturer_c1)
        assert len(themes) > 0
        tags = [t.theme_tag for t in themes]
        assert "LAB_AND_PRACTICALS" in tags or "EXPLANATION_PACING" in tags
        assert themes[0].mention_count >= 1

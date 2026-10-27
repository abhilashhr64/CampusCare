import uuid
from datetime import datetime, timezone
import pytest
from sqlalchemy import text
from src.core.database import SessionApp, migrator_engine
from src.modules.feedback.models import FeedbackAnswer
from src.modules.feedback.service import (
    FeedbackService,
    FeedbackCycleCreate,
    FeedbackSubmitRequest,
)


@pytest.fixture
def setup_feedback_entities():
    college_id = uuid.uuid4()
    lecturer_id = uuid.uuid4()
    dept_id = uuid.uuid4()
    course_id = uuid.uuid4()
    section_id = uuid.uuid4()

    student_ids = [uuid.uuid4() for _ in range(6)]

    with migrator_engine.begin() as conn:
        conn.execute(
            text("INSERT INTO colleges (id, name, code, domain, is_active, settings, created_at, updated_at) "
                 "VALUES (:id, 'Feedback Test University', :code, :domain, true, '{}', now(), now())"),
            {"id": college_id, "code": f"col-fb-{college_id.hex[:6]}", "domain": f"fb-{college_id.hex[:6]}.edu"},
        )
        conn.execute(text(f"SET LOCAL app.current_college_id = '{college_id}'"))

        # Create lecturer user
        conn.execute(
            text("INSERT INTO users (id, college_id, email, full_name, is_email_verified, is_active, is_mfa_enabled, created_at, updated_at) "
                 "VALUES (:id, :cid, 'lecturer@fb.edu', 'Dr. Ada Lovelace', true, true, false, now(), now())"),
            {"id": lecturer_id, "cid": college_id},
        )

        # Create student users
        for i, s_id in enumerate(student_ids):
            conn.execute(
                text("INSERT INTO users (id, college_id, email, full_name, is_email_verified, is_active, is_mfa_enabled, created_at, updated_at) "
                     "VALUES (:id, :cid, :email, :name, true, true, false, now(), now())"),
                {"id": s_id, "cid": college_id, "email": f"student{i}@fb.edu", "name": f"Student {i}"},
            )

        # Create department
        conn.execute(
            text("INSERT INTO directory_departments (id, college_id, code, name, created_at) "
                 "VALUES (:id, :cid, 'CS-FB', 'Computer Science', now())"),
            {"id": dept_id, "cid": college_id},
        )

        # Create course
        conn.execute(
            text("INSERT INTO directory_courses (id, college_id, department_id, code, title, credits, created_at) "
                 "VALUES (:id, :cid, :dept_id, 'CS401', 'Compilers', 4, now())"),
            {"id": course_id, "cid": college_id, "dept_id": dept_id},
        )

        # Create class section
        conn.execute(
            text("INSERT INTO directory_class_sections (id, college_id, course_id, lecturer_id, section_name, semester, academic_year, created_at) "
                 "VALUES (:id, :cid, :course_id, :lecturer_id, 'Section A', 6, '2026-2027', now())"),
            {"id": section_id, "cid": college_id, "course_id": course_id, "lecturer_id": lecturer_id},
        )

    return college_id, lecturer_id, student_ids, course_id, section_id


def test_anonymous_feedback_physical_unlinkability_and_k_anonymity(setup_feedback_entities):
    """Rule NR-10 & ADR-004: Anonymous feedback has zero stored link between respondent identity
    and answers by design. Rule AZ-6: k-anonymity (k>=5) thresholding on aggregates.
    """
    college_id, lecturer_id, student_ids, course_id, section_id = setup_feedback_entities

    with SessionApp() as db:
        # Step 1: Create Feedback Cycle
        cycle = FeedbackService.create_cycle(
            db,
            college_id,
            FeedbackCycleCreate(
                title="Fall 2026 Teaching Evaluations",
                academic_term="Fall 2026",
                k_anonymity_threshold=5,
            ),
        )

        # Verify Schema-level Physical Unlinkability (Rule NR-10, ADR-004)
        answer_columns = [col.name for col in FeedbackAnswer.__table__.columns]
        assert "student_id" not in answer_columns
        assert "user_id" not in answer_columns
        assert "voter_id" not in answer_columns
        assert "participation_id" not in answer_columns
        assert "ip_address" not in answer_columns

        # Step 2: Student 0 submits feedback
        req1 = FeedbackSubmitRequest(
            cycle_id=cycle.id,
            class_section_id=section_id,
            course_id=course_id,
            lecturer_id=lecturer_id,
            rating_pedagogy=5,
            rating_clarity=4,
            rating_engagement=5,
            rating_punctuality=5,
            comment="Excellent explanation of syntax analysis.",
        )
        res1 = FeedbackService.submit_anonymous_feedback(db, college_id, student_ids[0], req1)
        assert res1["status"] == "SUCCESS"

        # Step 3: Prevent duplicate voting (Student 0 tries again)
        with pytest.raises(ValueError, match="already submitted feedback"):
            FeedbackService.submit_anonymous_feedback(db, college_id, student_ids[0], req1)

        # Step 4: Verify k-anonymity gate (< 5 responses -> k_anonymity_met is False)
        aggregates_under_k = FeedbackService.get_lecturer_aggregates(db, college_id, lecturer_id, cycle.id)
        assert aggregates_under_k.response_count == 1
        assert aggregates_under_k.k_anonymity_met is False
        assert aggregates_under_k.avg_pedagogy is None
        assert aggregates_under_k.overall_rating is None
        assert "Insufficient responses" in aggregates_under_k.qualitative_summary

        # Step 5: Submit 4 more responses from different students to reach threshold k=5
        ratings = [
            (4, 5, 4, 4),
            (5, 5, 5, 5),
            (4, 4, 4, 5),
            (3, 4, 4, 4),
        ]
        for i, (p, c, e, pun) in enumerate(ratings, start=1):
            req = FeedbackSubmitRequest(
                cycle_id=cycle.id,
                class_section_id=section_id,
                course_id=course_id,
                lecturer_id=lecturer_id,
                rating_pedagogy=p,
                rating_clarity=c,
                rating_engagement=e,
                rating_punctuality=pun,
                comment=f"Student {i} constructive feedback.",
            )
            FeedbackService.submit_anonymous_feedback(db, college_id, student_ids[i], req)

        # Step 6: Verify k-anonymity gate (>= 5 responses -> metrics safely revealed)
        aggregates_met = FeedbackService.get_lecturer_aggregates(db, college_id, lecturer_id, cycle.id)
        assert aggregates_met.response_count == 5
        assert aggregates_met.k_anonymity_met is True
        assert aggregates_met.avg_pedagogy is not None
        assert aggregates_met.overall_rating is not None
        assert aggregates_met.overall_rating > 4.0

        # Step 7: Verify stored epoch bucket format (prevents timestamp correlation)
        raw_answer = db.execute(
            text("SELECT epoch_bucket, comment_clean FROM feedback_answers WHERE college_id = :cid LIMIT 1"),
            {"cid": college_id},
        ).fetchone()
        assert raw_answer is not None
        assert "-B" in raw_answer[0]

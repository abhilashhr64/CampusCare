import uuid
import math
import re
from datetime import datetime, timezone
from typing import List, Optional
from pydantic import BaseModel, ConfigDict
from sqlalchemy.orm import Session
from src.core.rls import set_tenant_context
from src.modules.complaints.service import ComplaintsService
from src.modules.feedback.service import FeedbackService
from src.modules.attendance.service import AttendanceService
from src.modules.directory.service import DirectoryService
from src.modules.notifications.service import NotificationService
from src.modules.analytics.models import (
    ComplaintDuplicateCluster,
    FeedbackThemeAggregate,
    SlaRiskAssessment,
    AttendanceRiskAlert,
)


class DuplicateClusterOut(BaseModel):
    id: uuid.UUID
    canonical_complaint_id: uuid.UUID
    duplicate_complaint_id: uuid.UUID
    similarity_score: float
    detected_reason: str
    detected_at: datetime

    model_config = ConfigDict(from_attributes=True)


class SlaRiskOut(BaseModel):
    id: uuid.UUID
    complaint_id: uuid.UUID
    ticket_number: str
    title: str
    category: str
    location_tag: str
    risk_level: str
    hours_remaining: float
    projected_breach_probability: float
    assessed_at: datetime


class AttendanceRiskOut(BaseModel):
    id: uuid.UUID
    student_id: uuid.UUID
    class_section_id: uuid.UUID
    conducted_count: int
    attended_count: int
    current_percentage: float
    classes_needed_for_safe: int
    alert_status: str
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class FeedbackThemeOut(BaseModel):
    id: uuid.UUID
    cycle_id: uuid.UUID
    lecturer_id: uuid.UUID
    theme_tag: str
    sentiment_polarity: str
    mention_count: int
    summary_text: str
    computed_at: datetime

    model_config = ConfigDict(from_attributes=True)


STOP_WORDS = {
    "the", "is", "at", "which", "on", "and", "a", "an", "in", "to", "for", "of", "with"
}


def _tokenize(text: str) -> set:
    words = re.findall(r"\w+", text.lower())
    return {w for w in words if len(w) > 2 and w not in STOP_WORDS}


class AnalyticsService:
    @staticmethod
    def detect_duplicate_complaints(
        db: Session,
        college_id: uuid.UUID,
        complaint_id: uuid.UUID,
        threshold: float = 0.35,
    ) -> List[ComplaintDuplicateCluster]:
        """Detects co-located and semantically overlapping complaint tickets within the same tenant (Rule B3, TN-6)."""
        set_tenant_context(db, college_id=college_id)

        target = ComplaintsService.get_complaint_dto(db, college_id, complaint_id)
        if not target:
            raise ValueError("Complaint not found or unauthorized.")

        target_tokens = _tokenize(f"{target.title} {target.description}")

        # Scan open non-closed complaints in the same tenant through service interface (Rule BR-1)
        candidates = ComplaintsService.list_open_complaints_dto(db, college_id)
        detected: List[ComplaintDuplicateCluster] = []

        now = datetime.now(timezone.utc)
        for cand in candidates:
            if cand.id == complaint_id:
                continue

            cand_tokens = _tokenize(f"{cand.title} {cand.description}")
            union_len = len(target_tokens.union(cand_tokens))
            overlap_len = len(target_tokens.intersection(cand_tokens))
            text_sim = (overlap_len / union_len) if union_len > 0 else 0.0

            # Co-location bonus
            same_loc = bool(target.location_tag and cand.location_tag and target.location_tag == cand.location_tag)
            total_score = text_sim + (0.30 if same_loc else 0.0)

            if total_score >= threshold:
                reason = "CO_LOCATED_AND_TEXT_OVERLAP" if same_loc else "TEXT_SIMILARITY_MATCH"
                cluster = ComplaintDuplicateCluster(
                    college_id=college_id,
                    canonical_complaint_id=target.id,
                    duplicate_complaint_id=cand.id,
                    similarity_score=min(1.0, round(total_score, 3)),
                    detected_reason=reason,
                    detected_at=now,
                )
                db.add(cluster)
                detected.append(cluster)

        db.commit()
        for d in detected:
            db.refresh(d)
        return detected

    @staticmethod
    def assess_sla_risks(
        db: Session,
        college_id: uuid.UUID,
    ) -> List[SlaRiskOut]:
        """Evaluates SLA countdowns and projects deadline breach risk for department admins (Rule B1, B3)."""
        set_tenant_context(db, college_id=college_id)

        complaints = ComplaintsService.list_open_complaints_dto(db, college_id)
        now = datetime.now(timezone.utc)
        results: List[SlaRiskOut] = []

        for c in complaints:
            if not c.sla_deadline:
                continue

            diff = (c.sla_deadline - now).total_seconds() / 3600.0
            hours_rem = max(0.0, round(diff, 1))

            if hours_rem <= 6.0:
                risk_level = "CRITICAL"
                prob = 0.92
            elif hours_rem <= 18.0:
                risk_level = "HIGH"
                prob = 0.68
            elif hours_rem <= 30.0:
                risk_level = "MEDIUM"
                prob = 0.35
            else:
                risk_level = "LOW"
                prob = 0.10

            ass_id = uuid.uuid4()
            assessment = SlaRiskAssessment(
                id=ass_id,
                college_id=college_id,
                complaint_id=c.id,
                risk_level=risk_level,
                hours_remaining=hours_rem,
                projected_breach_probability=prob,
                assessed_at=now,
            )
            db.add(assessment)
            results.append(
                SlaRiskOut(
                    id=ass_id,
                    complaint_id=c.id,
                    ticket_number=c.ticket_number,
                    title=c.title,
                    category=c.category,
                    location_tag=c.location_tag or "UNTAGGED",
                    risk_level=risk_level,
                    hours_remaining=hours_rem,
                    projected_breach_probability=prob,
                    assessed_at=now,
                )
            )

        db.commit()
        results.sort(key=lambda x: x.hours_remaining)
        return results

    @staticmethod
    def generate_supportive_attendance_alerts(
        db: Session,
        college_id: uuid.UUID,
        target_percentage: float = 75.0,
    ) -> List[AttendanceRiskAlert]:
        """Proactively identifies students with attendance deficits and dispatches supportive what-if recovery plans (Rule B1, B3)."""
        set_tenant_context(db, college_id=college_id)

        # Query enrollments across sections through directory service interface (Rule BR-1)
        enrollments = DirectoryService.list_enrollments_with_course(db, college_id)
        now = datetime.now(timezone.utc)
        alerts: List[AttendanceRiskAlert] = []

        for student_id, section_id, course_code, course_title in enrollments:
            # Query attendance counts through attendance service interface (Rule BR-1)
            conducted, attended = AttendanceService.get_section_attendance_counts(
                db, college_id, section_id, student_id
            )
            if conducted == 0:
                continue

            current_pct = round((attended / conducted) * 100.0, 1)

            # Check if below target (Rule B3 deterministic what-if recovery)
            if current_pct < target_percentage:
                target_ratio = target_percentage / 100.0
                classes_needed = math.ceil((target_ratio * conducted - attended) / (1.0 - target_ratio))
                classes_needed = max(1, classes_needed)

                alert = AttendanceRiskAlert(
                    college_id=college_id,
                    student_id=student_id,
                    class_section_id=section_id,
                    conducted_count=conducted,
                    attended_count=attended,
                    current_percentage=current_pct,
                    classes_needed_for_safe=classes_needed,
                    alert_status="ACTIVE",
                    created_at=now,
                )
                db.add(alert)
                alerts.append(alert)

                # Send supportive alert notification (Rule B1, B3)
                NotificationService.send_notification(
                    db=db,
                    college_id=college_id,
                    user_id=student_id,
                    subject=f"Supportive Attendance Alert: {course_code} ({current_pct}%)",
                    body=(
                        f"Your current attendance in {course_title} ({course_code}) is {current_pct}%, "
                        f"which is below the {target_percentage:.0f}% institutional requirement. "
                        f"According to the deterministic what-if calculation, you need to attend the next "
                        f"{classes_needed} consecutive classes to return to a safe standing."
                    ),
                    event_type="ATTENDANCE_ALERT",
                    channel="IN_APP",
                )

        db.commit()
        for a in alerts:
            db.refresh(a)
        return alerts

    @staticmethod
    def aggregate_feedback_themes(
        db: Session,
        college_id: uuid.UUID,
        cycle_id: uuid.UUID,
        lecturer_id: uuid.UUID,
    ) -> List[FeedbackThemeAggregate]:
        """Extracts qualitative themes from feedback while strictly enforcing k-anonymity (Rule NR-10 & ADR-004)."""
        set_tenant_context(db, college_id=college_id)

        # Call feedback service interface which validates k-anonymity gate (Rule BR-1, NR-10)
        comments = FeedbackService.get_qualitative_comments_if_threshold_met(
            db, college_id, cycle_id, lecturer_id
        )

        now = datetime.now(timezone.utc)
        aggregates: List[FeedbackThemeAggregate] = []

        # Thematic categorization rules
        themes_def = [
            ("LAB_AND_PRACTICALS", "Lab Guidance & Hands-on Clarity", ["lab", "practical", "hardware", "experiment"]),
            ("EXPLANATION_PACING", "Lecture Pacing & Conceptual Depth", ["pace", "fast", "slow", "slide", "depth", "concept"]),
            ("INTERACTION_AND_DOUBTS", "Student Engagement & Doubt Resolution", ["doubt", "question", "interactive", "friendly", "answer"]),
        ]

        for tag, title, keywords in themes_def:
            matched_count = sum(1 for c in comments if any(k in c.lower() for k in keywords))
            if matched_count > 0:
                agg = FeedbackThemeAggregate(
                    college_id=college_id,
                    cycle_id=cycle_id,
                    lecturer_id=lecturer_id,
                    theme_tag=tag,
                    sentiment_polarity="CONSTRUCTIVE" if "fast" in " ".join(comments).lower() else "POSITIVE",
                    mention_count=matched_count,
                    summary_text=f"{title}: Mentioned in {matched_count} thresholded student responses.",
                    computed_at=now,
                )
                db.add(agg)
                aggregates.append(agg)

        db.commit()
        for a in aggregates:
            db.refresh(a)
        return aggregates

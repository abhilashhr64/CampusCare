import uuid
from datetime import datetime, timezone, timedelta
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, ConfigDict
from sqlalchemy.orm import Session
from sqlalchemy import select, func, desc, update
from src.core.rls import set_tenant_context
from src.core.outbox import publish_event
from src.modules.complaints.models import Complaint, ComplaintEvent
from src.modules.audit.service import AuditService
from src.modules.access.policy import Actor


class ComplaintCreate(BaseModel):
    category: str  # FACILITY, HOSTEL, ACADEMIC, IT, GRIEVANCE_SENSITIVE
    title: str
    description: str
    location_tag: Optional[str] = None  # e.g. "QR:LAB-3-B4"
    is_sensitive: bool = False
    sla_committed_hours: int = 48


class AssignComplaintRequest(BaseModel):
    assigned_to_user_id: Optional[uuid.UUID] = None
    assigned_department_id: Optional[uuid.UUID] = None
    comment: Optional[str] = None


class ResolveComplaintRequest(BaseModel):
    resolution_note: str


class ResolutionConfirmRequest(BaseModel):
    student_confirmed: bool  # True to close, False to reopen
    feedback_rating: Optional[int] = None  # 1-5
    feedback_comment: Optional[str] = None


class ComplaintEventResponse(BaseModel):
    id: uuid.UUID
    event_type: str
    actor_id: Optional[uuid.UUID]
    comment: Optional[str]
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class ComplaintResponse(BaseModel):
    id: uuid.UUID
    college_id: uuid.UUID
    ticket_number: str
    creator_id: uuid.UUID
    category: str
    title: str
    description: str
    location_tag: Optional[str]
    is_sensitive: bool
    status: str
    assigned_to_user_id: Optional[uuid.UUID]
    assigned_department_id: Optional[uuid.UUID]
    sla_committed_hours: int
    sla_deadline: datetime
    resolved_at: Optional[datetime]
    closed_at: Optional[datetime]
    student_confirmed: Optional[bool]
    student_feedback_rating: Optional[int]
    student_feedback_comment: Optional[str]
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class ComplaintsService:
    @staticmethod
    def create_complaint(
        db: Session,
        college_id: uuid.UUID,
        creator_id: uuid.UUID,
        data: ComplaintCreate,
    ) -> Complaint:
        """Raises a complaint with committed SLA response time and location tag (Rule B3)."""
        set_tenant_context(db, college_id=college_id, user_id=creator_id)

        # Generate sequential ticket number for the tenant
        count = db.scalar(
            select(func.count(Complaint.id)).where(Complaint.college_id == college_id)
        ) or 0
        ticket_number = f"CC-{1001 + count}"

        now = datetime.now(timezone.utc)
        deadline = now + timedelta(hours=data.sla_committed_hours)

        complaint = Complaint(
            college_id=college_id,
            ticket_number=ticket_number,
            creator_id=creator_id,
            category=data.category,
            title=data.title,
            description=data.description,
            location_tag=data.location_tag,
            is_sensitive=data.is_sensitive,
            status="SUBMITTED",
            sla_committed_hours=data.sla_committed_hours,
            sla_deadline=deadline,
            created_at=now,
            updated_at=now,
        )
        db.add(complaint)
        db.flush()

        # Record timeline event
        event = ComplaintEvent(
            college_id=college_id,
            complaint_id=complaint.id,
            actor_id=creator_id,
            event_type="CREATED",
            comment="Complaint submitted with committed SLA.",
            created_at=now,
        )
        db.add(event)

        # Enqueue transactional outbox event (Rule EV-1, BR-3)
        publish_event(
            db,
            topic="complaints.created",
            payload={
                "complaint_id": str(complaint.id),
                "ticket_number": complaint.ticket_number,
                "category": complaint.category,
                "is_sensitive": complaint.is_sensitive,
                "college_id": str(college_id),
            },
            college_id=college_id,
        )

        db.commit()
        db.refresh(complaint)
        return complaint

    @staticmethod
    def list_complaints(
        db: Session,
        college_id: uuid.UUID,
        actor: Actor,
    ) -> List[Complaint]:
        """Lists complaints respecting ABAC visibility constraints (Rule AZ-2)."""
        set_tenant_context(db, college_id=college_id, user_id=actor.user_id)

        stmt = select(Complaint).where(Complaint.college_id == college_id)

        # Students see only own complaints
        if "STUDENT" in actor.roles and not ({"COLLEGE_ADMIN", "DEPARTMENT_ADMIN", "GRIEVANCE_COMMITTEE"} & set(actor.roles)):
            stmt = stmt.where(Complaint.creator_id == actor.user_id)
        elif "GRIEVANCE_COMMITTEE" in actor.roles:
            # Grievance committee prioritizes sensitive cases
            stmt = stmt.where(Complaint.is_sensitive == True)
        elif "DEPARTMENT_ADMIN" in actor.roles:
            # Filter non-sensitive cases
            stmt = stmt.where(Complaint.is_sensitive == False)

        stmt = stmt.order_by(Complaint.created_at.desc())
        return list(db.scalars(stmt).all())

    @staticmethod
    def get_complaint(
        db: Session,
        college_id: uuid.UUID,
        complaint_id: uuid.UUID,
    ) -> Optional[Complaint]:
        set_tenant_context(db, college_id=college_id)
        return db.get(Complaint, complaint_id)

    @staticmethod
    def assign_complaint(
        db: Session,
        college_id: uuid.UUID,
        complaint_id: uuid.UUID,
        assigner_id: uuid.UUID,
        data: AssignComplaintRequest,
    ) -> Complaint:
        set_tenant_context(db, college_id=college_id, user_id=assigner_id)

        complaint = db.get(Complaint, complaint_id)
        if not complaint or complaint.college_id != college_id:
            raise ValueError("Complaint not found.")

        complaint.assigned_to_user_id = data.assigned_to_user_id
        complaint.assigned_department_id = data.assigned_department_id
        complaint.status = "ASSIGNED"
        complaint.updated_at = datetime.now(timezone.utc)

        event = ComplaintEvent(
            college_id=college_id,
            complaint_id=complaint.id,
            actor_id=assigner_id,
            event_type="ASSIGNED",
            comment=data.comment or "Assigned to owner for resolution.",
        )
        db.add(event)

        publish_event(
            db,
            topic="complaints.assigned",
            payload={"complaint_id": str(complaint.id), "assigned_to": str(data.assigned_to_user_id)},
            college_id=college_id,
        )

        db.commit()
        db.refresh(complaint)
        return complaint

    @staticmethod
    def resolve_complaint(
        db: Session,
        college_id: uuid.UUID,
        complaint_id: uuid.UUID,
        resolver_id: uuid.UUID,
        data: ResolveComplaintRequest,
    ) -> Complaint:
        """Staff marks complaint as resolved; awaits closed-loop confirmation (Rule B3)."""
        set_tenant_context(db, college_id=college_id, user_id=resolver_id)

        complaint = db.get(Complaint, complaint_id)
        if not complaint or complaint.college_id != college_id:
            raise ValueError("Complaint not found.")

        now = datetime.now(timezone.utc)
        complaint.status = "RESOLVED"
        complaint.resolved_at = now
        complaint.updated_at = now

        event = ComplaintEvent(
            college_id=college_id,
            complaint_id=complaint.id,
            actor_id=resolver_id,
            event_type="RESOLVED",
            comment=data.resolution_note,
        )
        db.add(event)

        publish_event(
            db,
            topic="complaints.resolved",
            payload={"complaint_id": str(complaint.id), "ticket_number": complaint.ticket_number},
            college_id=college_id,
        )

        db.commit()
        db.refresh(complaint)
        return complaint

    @staticmethod
    def confirm_or_reopen(
        db: Session,
        college_id: uuid.UUID,
        complaint_id: uuid.UUID,
        student_id: uuid.UUID,
        data: ResolutionConfirmRequest,
    ) -> Complaint:
        """Closed-loop resolution: student confirms or reopens the issue (Rule B3)."""
        set_tenant_context(db, college_id=college_id, user_id=student_id)

        complaint = db.get(Complaint, complaint_id)
        if not complaint or complaint.college_id != college_id:
            raise ValueError("Complaint not found.")

        if complaint.creator_id != student_id:
            raise ValueError("Only the original student creator can confirm or reopen this complaint.")

        now = datetime.now(timezone.utc)
        complaint.student_confirmed = data.student_confirmed
        complaint.student_feedback_rating = data.feedback_rating
        complaint.student_feedback_comment = data.feedback_comment
        complaint.updated_at = now

        if data.student_confirmed:
            complaint.status = "CLOSED"
            complaint.closed_at = now
            event_type = "CONFIRMED_CLOSED"
            event_comment = "Student confirmed resolution satisfaction."
        else:
            complaint.status = "REOPENED"
            event_type = "REOPENED"
            event_comment = f"Student reopened: {data.feedback_comment or 'Issue not resolved'}"

        event = ComplaintEvent(
            college_id=college_id,
            complaint_id=complaint.id,
            actor_id=student_id,
            event_type=event_type,
            comment=event_comment,
        )
        db.add(event)

        # Tamper-evident hash-chained audit logging (Rule B3)
        AuditService.record_entry(
            db=db,
            college_id=college_id,
            actor_id=student_id,
            action=f"COMPLAINT_{event_type}",
            resource_type="complaint",
            resource_id=str(complaint.id),
            payload={
                "ticket_number": complaint.ticket_number,
                "student_confirmed": data.student_confirmed,
                "rating": data.feedback_rating,
            },
        )

        publish_event(
            db,
            topic=f"complaints.{event_type.lower()}",
            payload={"complaint_id": str(complaint.id), "status": complaint.status},
            college_id=college_id,
        )

        db.commit()
        db.refresh(complaint)
        return complaint

    @staticmethod
    def get_complaint_dto(db: Session, college_id: uuid.UUID, complaint_id: uuid.UUID) -> Optional[ComplaintResponse]:
        set_tenant_context(db, college_id=college_id)
        c = db.get(Complaint, complaint_id)
        if not c or c.college_id != college_id:
            return None
        return ComplaintResponse.model_validate(c)

    @staticmethod
    def list_open_complaints_dto(db: Session, college_id: uuid.UUID) -> List[ComplaintResponse]:
        set_tenant_context(db, college_id=college_id)
        stmt = (
            select(Complaint)
            .where(
                Complaint.college_id == college_id,
                Complaint.status.in_(["SUBMITTED", "ASSIGNED", "IN_PROGRESS"]),
            )
        )
        return [ComplaintResponse.model_validate(c) for c in db.scalars(stmt).all()]

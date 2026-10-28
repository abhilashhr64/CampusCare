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
    category: str  # FACILITY, HOSTEL, TRANSPORT, FEE_ACCOUNTS, ACADEMIC, IT, GRIEVANCE_SENSITIVE
    title: str
    description: str
    location_tag: Optional[str] = None  # e.g. "QR:LAB-3-B4"
    is_sensitive: bool = False
    sla_committed_hours: int = 48


class ComplaintAiRoutingRequest(BaseModel):
    problem_text: str
    location_hint: Optional[str] = None


class ComplaintAiRoutingResponse(BaseModel):
    category: str
    category_label: str
    assigned_department_name: str
    sla_committed_hours: int
    severity: str  # CRITICAL, HIGH, MEDIUM, LOW
    confidence_score: float
    auto_title: str
    key_entities: List[str]
    is_sensitive: bool
    routing_reasoning: str


ROUTING_PROFILES: Dict[str, Dict[str, Any]] = {
    "TRANSPORT": {
        "keywords": [
            "bus", "transport", "driver", "route", "shuttle", "commute", "pickup", "drop",
            "traffic", "transit", "vehicle", "breakdown", "flat tire", "conductor", "bus stop",
            "city junction", "college bus", "bus pass"
        ],
        "label": "Transport & College Bus Fleet",
        "department": "Office of Transportation & Transit Fleet",
        "sla_hours": 24,
        "base_severity": "HIGH",
    },
    "HOSTEL": {
        "keywords": [
            "hostel", "geyser", "hot water", "warden", "mess", "food", "room", "bed", "bathroom",
            "washroom", "plumbing", "tap", "flush", "water leak", "noise", "roommate", "curfew",
            "hostel block", "laundry", "iron box", "mess rebate"
        ],
        "label": "Hostel & Residential Life",
        "department": "Chief Warden & Residential Housing Board",
        "sla_hours": 24,
        "base_severity": "HIGH",
    },
    "FEE_ACCOUNTS": {
        "keywords": [
            "fee", "tuition", "fees", "payment", "receipt", "bursar", "account", "transaction",
            "upi", "net banking", "debit card", "debited", "scholarship", "fine", "dues",
            "installment", "refund", "balance statement", "challan", "unpaid in portal"
        ],
        "label": "Fee, Bursar & Finance Accounts",
        "department": "Finance, Accounts & Bursar Office",
        "sla_hours": 48,
        "base_severity": "HIGH",
    },
    "ACADEMIC": {
        "keywords": [
            "attendance", "attendance percentage", "cutoff", "credit", "professor", "lecturer",
            "marks", "internal", "midsem", "grade", "gpa", "exam", "hall ticket", "revaluation",
            "syllabus", "timetable", "class clash", "section change", "elective", "condonation"
        ],
        "label": "Academic & Examination Affairs",
        "department": "Dean of Academic Affairs & Registrar",
        "sla_hours": 72,
        "base_severity": "MEDIUM",
    },
    "IT": {
        "keywords": [
            "wifi", "wi-fi", "internet", "network", "ethernet", "router", "lan", "login",
            "portal", "password", "gpu", "graphics card", "nvidia", "workstation", "pc",
            "computer", "monitor", "keyboard", "mouse", "server", "linux", "crash"
        ],
        "label": "Campus IT & Computing Infrastructure",
        "department": "Campus IT & Network Operations Center (NOC)",
        "sla_hours": 24,
        "base_severity": "MEDIUM",
    },
    "FACILITY": {
        "keywords": [
            "projector", "hdmi", "screen", "ac", "air conditioner", "fan", "light", "switch",
            "bench", "chair", "desk", "blackboard", "chalkboard", "door", "window", "elevator",
            "lift", "dustbin", "cleanliness", "water cooler", "water filter", "podium", "audio"
        ],
        "label": "Campus Infrastructure & Maintenance",
        "department": "Estate & Physical Maintenance Office",
        "sla_hours": 48,
        "base_severity": "LOW",
    },
    "GRIEVANCE_SENSITIVE": {
        "keywords": [
            "harassment", "ragging", "threat", "discriminate", "abuse", "assault", "mental health",
            "bullying", "stalking", "blackmail", "confidential", "suicide", "depression"
        ],
        "label": "Confidential Grievance Committee",
        "department": "Internal Complaints Committee (ICC) & Ombudsman",
        "sla_hours": 12,
        "base_severity": "CRITICAL",
    },
}


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

    @staticmethod
    def ai_route_complaint(
        problem_text: str,
        location_hint: Optional[str] = None,
    ) -> ComplaintAiRoutingResponse:
        """Intelligently classifies natural language student problem text, extracts entities,
        predicts target campus department, commits SLA hours, and assesses urgency/sensitivity.
        """
        import re

        text_lower = (problem_text or "").lower()
        hint_lower = (location_hint or "").lower()
        combined_text = f"{text_lower} {hint_lower}"

        # 1. Entity Extraction
        entities = []
        bus_match = re.findall(r"(?:bus|route)\s*(?:route|no|bus|number|#)?\s*([0-9]+[a-zA-Z]?)", text_lower)
        if bus_match:
            entities.append(f"Transit Route/Bus: {bus_match[0].upper()}")

        room_match = re.findall(r"(?:room|hostel|block)\s*#?\s*([0-9a-zA-Z]+)", text_lower)
        if room_match:
            entities.append(f"Hostel/Room: {room_match[0].upper()}")

        txn_match = re.findall(r"(?:txn|transaction|ref|upi|utr|challan)\s*[:#]?\s*([0-9a-zA-Z]{6,})", text_lower)
        if txn_match:
            entities.append(f"Transaction Ref: {txn_match[0].upper()}")

        lab_match = re.findall(r"(?:lab|pc|system|station)\s*#?\s*([0-9a-zA-Z]+)", text_lower)
        if lab_match:
            entities.append(f"Lab Resource: {lab_match[0].upper()}")

        if location_hint:
            entities.append(f"Location Tag: {location_hint}")

        # 2. Check for Sensitive Grievance first (harassment, ragging, threat, abuse)
        sensitive_kw = ROUTING_PROFILES["GRIEVANCE_SENSITIVE"]["keywords"]
        matched_sensitive = [kw for kw in sensitive_kw if kw in combined_text]
        if matched_sensitive:
            return ComplaintAiRoutingResponse(
                category="GRIEVANCE_SENSITIVE",
                category_label="Confidential Grievance Committee",
                assigned_department_name="Internal Complaints Committee (ICC) & Ombudsman",
                sla_committed_hours=12,
                severity="CRITICAL",
                confidence_score=0.98,
                auto_title="Confidential Grievance: Urgent ICC Intervention Requested",
                key_entities=entities,
                is_sensitive=True,
                routing_reasoning=(
                    "Natural language analysis identified sensitive grievance indicators "
                    f"({', '.join(matched_sensitive)}). Automatically shielded and rerouted "
                    "directly to the Internal Complaints Committee (ICC) & Ombudsman with 12-hour statutory SLA."
                ),
            )

        # 3. Score against remaining profiles
        category_scores: Dict[str, float] = {}
        matched_words_by_cat: Dict[str, List[str]] = {}
        for cat, prof in ROUTING_PROFILES.items():
            if cat == "GRIEVANCE_SENSITIVE":
                continue
            matches = [kw for kw in prof["keywords"] if kw in combined_text]
            matched_words_by_cat[cat] = matches
            score = 0.0
            for m in matches:
                # Longer keywords give higher discriminatory weight
                score += 1.0 + (len(m.split()) * 0.5)
            # Extra boost if location hint aligns with category
            if cat == "HOSTEL" and any(k in hint_lower for k in ["hostel", "block", "room", "mess"]):
                score += 2.0
            elif cat == "TRANSPORT" and any(k in hint_lower for k in ["bus", "route", "stop", "transit"]):
                score += 2.0
            elif cat == "IT" and any(k in hint_lower for k in ["lab", "noc", "server"]):
                score += 2.0
            category_scores[cat] = score

        # Find best category
        best_cat = max(category_scores, key=lambda k: category_scores[k])
        max_score = category_scores[best_cat]

        if max_score <= 0.0:
            best_cat = "FACILITY"
            confidence = 0.65
        else:
            confidence = min(0.96, 0.70 + (max_score * 0.06))

        profile = ROUTING_PROFILES[best_cat]
        base_severity = profile["base_severity"]
        sla_hours = profile["sla_hours"]

        # 4. Urgency Modifiers
        urgency_markers = [
            "emergency", "urgent", "immediate", "fire", "danger", "spark", "leak", "flood",
            "critical", "stolen", "exam tomorrow", "deadline today", "no power", "blackout"
        ]
        found_urgency = [u for u in urgency_markers if u in text_lower]
        if found_urgency:
            if base_severity == "LOW":
                base_severity = "MEDIUM"
                sla_hours = min(sla_hours, 24)
            elif base_severity == "MEDIUM":
                base_severity = "HIGH"
                sla_hours = min(sla_hours, 24)
            elif base_severity == "HIGH":
                base_severity = "CRITICAL"
                sla_hours = min(sla_hours, 12)

        # 5. Synthesize Auto-Title
        clean_first = (problem_text.strip().split(".")[0] or problem_text.strip())[:65]
        if best_cat == "TRANSPORT":
            route_str = f" ({bus_match[0].upper()})" if bus_match else ""
            auto_title = f"Transport Fleet Delay/Issue{route_str}: {clean_first}"
        elif best_cat == "HOSTEL":
            room_str = f" ({room_match[0].upper()})" if room_match else ""
            auto_title = f"Hostel Residential Disruption{room_str}: {clean_first}"
        elif best_cat == "FEE_ACCOUNTS":
            auto_title = f"Fee & Accounts Reconciliation: {clean_first}"
        elif best_cat == "IT":
            auto_title = f"Campus IT Network Alert: {clean_first}"
        elif best_cat == "ACADEMIC":
            auto_title = f"Academic & Attendance Inquiry: {clean_first}"
        else:
            auto_title = f"Campus Maintenance Request: {clean_first}"

        auto_title = auto_title.strip()
        if len(auto_title) > 100:
            auto_title = auto_title[:97] + "..."

        # 6. Synthesize Reasoning
        matches_found = matched_words_by_cat.get(best_cat, [])
        kw_preview = f"keywords [{', '.join(matches_found[:3])}]" if matches_found else "context analysis"
        urgency_note = f" Escalated to {base_severity} due to urgency signals ({', '.join(found_urgency)})." if found_urgency else ""
        routing_reasoning = (
            f"AI classification identified {profile['label']} based on {kw_preview}. "
            f"Automatically targeted to {profile['department']} with a {sla_hours}-hour turnaround SLA commitment.{urgency_note}"
        )

        return ComplaintAiRoutingResponse(
            category=best_cat,
            category_label=profile["label"],
            assigned_department_name=profile["department"],
            sla_committed_hours=sla_hours,
            severity=base_severity,
            confidence_score=round(confidence, 2),
            auto_title=auto_title,
            key_entities=entities,
            is_sensitive=False,
            routing_reasoning=routing_reasoning,
        )


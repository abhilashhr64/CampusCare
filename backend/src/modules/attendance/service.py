import math
import uuid
from datetime import datetime, timezone, date, time
from typing import Dict, Any, List, Optional
from pydantic import BaseModel, ConfigDict
from sqlalchemy.orm import Session
from sqlalchemy import select, func, and_
from src.core.rls import set_tenant_context
from src.core.outbox import publish_event
from src.modules.attendance.models import AttendanceSession, AttendanceRecord
from src.modules.audit.service import AuditService


class SessionCreateRequest(BaseModel):
    class_section_id: uuid.UUID
    session_date: date
    start_time: time
    end_time: time
    topic: Optional[str] = None


class SessionResponse(BaseModel):
    id: uuid.UUID
    college_id: uuid.UUID
    class_section_id: uuid.UUID
    lecturer_id: uuid.UUID
    session_date: date
    start_time: time
    end_time: time
    topic: Optional[str]
    version: int
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class AttendanceOpEntry(BaseModel):
    op_id: str  # UUID (idempotency key)
    session_id: uuid.UUID
    class_section_id: uuid.UUID
    base_version: int
    student_records: List[Dict[str, Any]]  # [{"student_id": "...", "status": "PRESENT"}]


class SyncOutcome(BaseModel):
    op_id: str
    outcome: str  # applied, duplicate, conflict, rejected
    reason: Optional[str] = None
    server_version: Optional[int] = None
    server_records: Optional[List[Dict[str, Any]]] = None


class AttendanceService:
    @staticmethod
    def calculate_what_if(
        conducted: int,
        attended: int,
        target_percentage: float = 75.0,
    ) -> Dict[str, Any]:
        """Deterministic attendance calculator (Rule B3 Signature Capability)."""
        if conducted < 0 or attended < 0 or attended > conducted:
            raise ValueError("Attended classes cannot exceed conducted classes or be negative.")

        if not (0 < target_percentage < 100):
            raise ValueError("Target threshold must be between 1 and 99 percent.")

        if conducted == 0:
            return {
                "conducted": 0,
                "attended": 0,
                "current_percentage": 100.0,
                "target_threshold": target_percentage,
                "is_safe": True,
                "status": "ON_TARGET",
                "classes_can_miss": 0,
                "classes_must_attend": 0,
            }

        current_pct = (attended / conducted) * 100.0
        rounded_pct = round(current_pct, 1)

        if current_pct >= target_percentage:
            can_miss = math.floor((100.0 * attended - target_percentage * conducted) / target_percentage)
            return {
                "conducted": conducted,
                "attended": attended,
                "current_percentage": rounded_pct,
                "target_threshold": target_percentage,
                "is_safe": True,
                "status": "SURPLUS" if can_miss > 0 else "ON_TARGET",
                "classes_can_miss": max(0, can_miss),
                "classes_must_attend": 0,
            }
        else:
            must_attend = math.ceil(
                (target_percentage * conducted - 100.0 * attended) / (100.0 - target_percentage)
            )
            return {
                "conducted": conducted,
                "attended": attended,
                "current_percentage": rounded_pct,
                "target_threshold": target_percentage,
                "is_safe": False,
                "status": "DEFICIT",
                "classes_can_miss": 0,
                "classes_must_attend": max(0, must_attend),
            }

    @staticmethod
    def create_session(
        db: Session,
        college_id: uuid.UUID,
        lecturer_id: uuid.UUID,
        data: SessionCreateRequest,
    ) -> AttendanceSession:
        set_tenant_context(db, college_id=college_id, user_id=lecturer_id)

        session = AttendanceSession(
            college_id=college_id,
            class_section_id=data.class_section_id,
            lecturer_id=lecturer_id,
            session_date=data.session_date,
            start_time=data.start_time,
            end_time=data.end_time,
            topic=data.topic,
            version=1,
        )
        db.add(session)
        db.commit()
        db.refresh(session)
        return session

    @staticmethod
    def sync_batch_operations(
        db: Session,
        college_id: uuid.UUID,
        lecturer_id: uuid.UUID,
        batch: List[AttendanceOpEntry],
    ) -> List[SyncOutcome]:
        """Processes attendance sync batch according to Rule C7 Offline Protocol."""
        set_tenant_context(db, college_id=college_id, user_id=lecturer_id)
        outcomes = []

        for entry in batch:
            session = db.get(AttendanceSession, entry.session_id)
            if not session or session.college_id != college_id:
                outcomes.append(
                    SyncOutcome(
                        op_id=entry.op_id,
                        outcome="rejected",
                        reason="Attendance session does not exist in tenant.",
                    )
                )
                continue

            # Concurrency check (Rule C7.3: Conflict occurs when server version > base_version)
            if session.version > entry.base_version:
                # Return conflict without silent overwrite
                current_records = list(
                    db.scalars(
                        select(AttendanceRecord).where(
                            AttendanceRecord.college_id == college_id,
                            AttendanceRecord.session_id == entry.session_id,
                        )
                    ).all()
                )
                outcomes.append(
                    SyncOutcome(
                        op_id=entry.op_id,
                        outcome="conflict",
                        reason=f"Concurrent modification detected. Server is at version {session.version}, client sent base_version {entry.base_version}.",
                        server_version=session.version,
                        server_records=[
                            {"student_id": str(r.student_id), "status": r.status}
                            for r in current_records
                        ],
                    )
                )
                continue

            # Apply records
            now = datetime.now(timezone.utc)
            for rec_data in entry.student_records:
                student_id = uuid.UUID(str(rec_data["student_id"]))
                status = rec_data.get("status", "PRESENT")

                existing_rec = db.scalar(
                    select(AttendanceRecord).where(
                        AttendanceRecord.college_id == college_id,
                        AttendanceRecord.session_id == entry.session_id,
                        AttendanceRecord.student_id == student_id,
                    )
                )
                if existing_rec:
                    existing_rec.status = status
                    existing_rec.updated_at = now
                else:
                    new_rec = AttendanceRecord(
                        college_id=college_id,
                        session_id=entry.session_id,
                        student_id=student_id,
                        status=status,
                        created_at=now,
                        updated_at=now,
                    )
                    db.add(new_rec)

            # Increment session concurrency version
            session.version += 1

            # Log to hash-chained tamper-evident audit ledger (Rule B3)
            AuditService.record_entry(
                db=db,
                college_id=college_id,
                actor_id=lecturer_id,
                action="ATTENDANCE_MARKED",
                resource_type="attendance_session",
                resource_id=str(session.id),
                payload={"op_id": entry.op_id, "record_count": len(entry.student_records), "version": session.version},
            )

            # Enqueue outbox event
            publish_event(
                db,
                topic="attendance.marked",
                payload={"session_id": str(session.id), "op_id": entry.op_id, "new_version": session.version},
                college_id=college_id,
            )

            db.commit()
            outcomes.append(
                SyncOutcome(
                    op_id=entry.op_id,
                    outcome="applied",
                    server_version=session.version,
                )
            )

        return outcomes

    @staticmethod
    def get_student_overall_summary(
        db: Session,
        college_id: uuid.UUID,
        student_id: uuid.UUID,
    ) -> Dict[str, Any]:
        """Calculates real-time attendance percentage for a student."""
        set_tenant_context(db, college_id=college_id, user_id=student_id)

        conducted = db.scalar(
            select(func.count(AttendanceRecord.id)).where(
                AttendanceRecord.college_id == college_id,
                AttendanceRecord.student_id == student_id,
            )
        ) or 0

        attended = db.scalar(
            select(func.count(AttendanceRecord.id)).where(
                AttendanceRecord.college_id == college_id,
                AttendanceRecord.student_id == student_id,
                AttendanceRecord.status == "PRESENT",
            )
        ) or 0

        return AttendanceService.calculate_what_if(conducted, attended, 75.0)

    @staticmethod
    def get_section_attendance_counts(
        db: Session,
        college_id: uuid.UUID,
        class_section_id: uuid.UUID,
        student_id: uuid.UUID,
    ) -> tuple[int, int]:
        """Returns (conducted, attended) counts for student in section under tenant RLS."""
        set_tenant_context(db, college_id=college_id)
        conducted = db.scalar(
            select(func.count(AttendanceSession.id)).where(
                AttendanceSession.college_id == college_id,
                AttendanceSession.class_section_id == class_section_id,
            )
        ) or 0
        if conducted == 0:
            return 0, 0

        attended = db.scalar(
            select(func.count(AttendanceRecord.id))
            .join(
                AttendanceSession,
                and_(
                    AttendanceSession.id == AttendanceRecord.session_id,
                    AttendanceSession.college_id == AttendanceRecord.college_id,
                ),
            )
            .where(
                AttendanceRecord.college_id == college_id,
                AttendanceRecord.student_id == student_id,
                AttendanceSession.class_section_id == class_section_id,
                AttendanceRecord.status == "PRESENT",
            )
        ) or 0
        return conducted, attended

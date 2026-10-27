import uuid
from datetime import datetime, timezone
from typing import List, Optional
from pydantic import BaseModel, ConfigDict
from sqlalchemy.orm import Session
from sqlalchemy import select, and_
from src.core.rls import set_tenant_context
from src.modules.notifications.models import NotificationPreference, NotificationDelivery


class PreferenceUpdate(BaseModel):
    event_type: str
    channel: str
    is_enabled: bool


class NotificationOut(BaseModel):
    id: uuid.UUID
    channel: str
    subject: str
    body: str
    status: str
    delivered_at: Optional[datetime] = None
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class NotificationService:
    @staticmethod
    def get_or_create_preference(
        db: Session,
        college_id: uuid.UUID,
        user_id: uuid.UUID,
        event_type: str,
        channel: str = "IN_APP",
    ) -> NotificationPreference:
        set_tenant_context(db, college_id=college_id, user_id=user_id)
        stmt = select(NotificationPreference).where(
            NotificationPreference.college_id == college_id,
            NotificationPreference.user_id == user_id,
            NotificationPreference.event_type == event_type,
            NotificationPreference.channel == channel,
        )
        pref = db.scalar(stmt)
        if not pref:
            pref = NotificationPreference(
                college_id=college_id,
                user_id=user_id,
                event_type=event_type,
                channel=channel,
                is_enabled=True,
            )
            db.add(pref)
            db.commit()
            db.refresh(pref)
        return pref

    @staticmethod
    def update_preference(
        db: Session,
        college_id: uuid.UUID,
        user_id: uuid.UUID,
        data: PreferenceUpdate,
    ) -> NotificationPreference:
        pref = NotificationService.get_or_create_preference(
            db, college_id, user_id, data.event_type, data.channel
        )
        pref.is_enabled = data.is_enabled
        pref.updated_at = datetime.now(timezone.utc)
        db.commit()
        db.refresh(pref)
        return pref

    @staticmethod
    def list_preferences(
        db: Session,
        college_id: uuid.UUID,
        user_id: uuid.UUID,
    ) -> List[NotificationPreference]:
        set_tenant_context(db, college_id=college_id, user_id=user_id)
        stmt = select(NotificationPreference).where(
            NotificationPreference.college_id == college_id,
            NotificationPreference.user_id == user_id,
        )
        return list(db.scalars(stmt).all())

    @staticmethod
    def send_notification(
        db: Session,
        college_id: uuid.UUID,
        user_id: uuid.UUID,
        subject: str,
        body: str,
        event_type: str = "SYSTEM_ALERT",
        channel: str = "IN_APP",
    ) -> Optional[NotificationDelivery]:
        """Delivers a notification respecting user preference under tenant RLS (Rule EV-3)."""
        pref = NotificationService.get_or_create_preference(
            db, college_id, user_id, event_type, channel
        )
        if not pref.is_enabled:
            return None

        delivery = NotificationDelivery(
            college_id=college_id,
            user_id=user_id,
            channel=channel,
            subject=subject,
            body=body,
            status="SENT",
            delivered_at=datetime.now(timezone.utc),
            created_at=datetime.now(timezone.utc),
        )
        db.add(delivery)
        db.commit()
        db.refresh(delivery)
        return delivery

    @staticmethod
    def list_user_notifications(
        db: Session,
        college_id: uuid.UUID,
        user_id: uuid.UUID,
        limit: int = 20,
    ) -> List[NotificationDelivery]:
        set_tenant_context(db, college_id=college_id, user_id=user_id)
        stmt = (
            select(NotificationDelivery)
            .where(
                NotificationDelivery.college_id == college_id,
                NotificationDelivery.user_id == user_id,
            )
            .order_by(NotificationDelivery.created_at.desc())
            .limit(limit)
        )
        return list(db.scalars(stmt).all())

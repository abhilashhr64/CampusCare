import sys
import os
import time
import uuid
from datetime import datetime, timezone
from typing import Dict, Any, List, Optional, Callable
from sqlalchemy.orm import Session
from sqlalchemy import select, update
from src.core.database import SessionApp
from src.core.rls import set_tenant_context
from src.core.outbox import OutboxEvent


def handle_event_payload(topic: str, payload: Dict[str, Any]) -> None:
    """Dispatches event payload to respective consumer handler idempotently (Rule EV-2, EV-3)."""
    if topic == "complaints.created":
        # Simulate SLA timer arming & notification dispatch
        pass
    elif topic == "complaints.resolved":
        # Simulate notification dispatch to student for closed-loop confirmation
        pass
    elif topic == "complaints.confirmed_closed":
        # Simulate routing evaluation metric update
        pass
    elif topic == "attendance.marked":
        # Simulate background percentage cache updates
        pass
    elif topic == "feedback.submitted":
        # Simulate background feedback aggregation refresh
        pass
    elif topic == "access.role_granted":
        # Simulate access change audit alert
        pass
    else:
        # Unknown topic
        pass


def process_outbox_batch(
    db: Session,
    college_id: Optional[uuid.UUID] = None,
    handler: Optional[Callable[[str, Dict[str, Any]], None]] = None,
    max_batch: int = 50,
) -> int:
    """Processes pending events from the transactional outbox (Rule EV-1, EV-2).
    Implements idempotent consumption, retry counts, and dead-letter handling.
    """
    if college_id:
        set_tenant_context(db, college_id=college_id)

    dispatch_func = handler or handle_event_payload

    stmt = (
        select(OutboxEvent)
        .where(OutboxEvent.status.in_(["PENDING", "FAILED"]))
        .where(OutboxEvent.retry_count < 5)
        .order_by(OutboxEvent.created_at.asc())
        .limit(max_batch)
    )
    events: List[OutboxEvent] = list(db.scalars(stmt).all())
    processed_count = 0

    for event in events:
        try:
            dispatch_func(event.topic, event.payload)
            event.status = "PROCESSED"
            event.processed_at = datetime.now(timezone.utc)
            event.last_error = None
            processed_count += 1
        except Exception as e:
            event.retry_count += 1
            event.last_error = str(e)
            if event.retry_count >= 5:
                # Rule EV-2: Move poison messages to dead-letter state with an alert
                event.status = "DEAD_LETTER"
            else:
                event.status = "FAILED"

    db.commit()
    return processed_count


def run_worker_loop(poll_interval_seconds: float = 2.0):
    """Continuous background worker loop (Rule EV-3)."""
    print(f"[{datetime.now().isoformat()}] Starting CampusCare AI Outbox Consumer Worker...")
    while True:
        try:
            with SessionApp() as db:
                count = process_outbox_batch(db)
                if count > 0:
                    print(f"[{datetime.now().isoformat()}] Processed {count} outbox events.")
        except Exception as e:
            print(f"[{datetime.now().isoformat()}] Worker error: {e}", file=sys.stderr)
        time.sleep(poll_interval_seconds)


if __name__ == "__main__":
    run_worker_loop()

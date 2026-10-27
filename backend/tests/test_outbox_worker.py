import uuid
import pytest
from sqlalchemy import text
from src.core.database import SessionApp, migrator_engine
from src.core.outbox import publish_event, OutboxEvent
from src.core.worker import process_outbox_batch


@pytest.fixture
def setup_outbox_tenant():
    college_id = uuid.uuid4()
    with migrator_engine.begin() as conn:
        conn.execute(
            text("INSERT INTO colleges (id, name, code, domain, is_active, settings, created_at, updated_at) "
                 "VALUES (:id, 'Outbox Test College', :code, :domain, true, '{}', now(), now())"),
            {"id": college_id, "code": f"col-ob-{college_id.hex[:6]}", "domain": f"ob-{college_id.hex[:6]}.edu"},
        )
    return college_id


def test_outbox_worker_happy_path(setup_outbox_tenant):
    """Rule EV-1 & EV-2: Transactional outbox events are processed and marked PROCESSED."""
    college_id = setup_outbox_tenant

    with SessionApp() as db:
        # Step 1: Publish events
        event1 = publish_event(
            db,
            topic="complaints.created",
            payload={"complaint_id": str(uuid.uuid4()), "ticket_number": "CC-2001"},
            college_id=college_id,
        )
        event2 = publish_event(
            db,
            topic="attendance.marked",
            payload={"session_id": str(uuid.uuid4()), "version": 2},
            college_id=college_id,
        )
        db.commit()

        # Step 2: Process batch
        processed_count = process_outbox_batch(db, college_id=college_id)
        assert processed_count >= 2

        # Step 3: Verify statuses
        e1 = db.get(OutboxEvent, event1.id)
        e2 = db.get(OutboxEvent, event2.id)

        assert e1.status == "PROCESSED"
        assert e1.processed_at is not None
        assert e1.last_error is None

        assert e2.status == "PROCESSED"
        assert e2.processed_at is not None


def test_outbox_worker_retry_and_dead_letter_queue(setup_outbox_tenant):
    """Rule EV-2: Failed consumer events retry with error logging and move to DEAD_LETTER after 5 attempts."""
    college_id = setup_outbox_tenant

    with SessionApp() as db:
        # Publish poison event
        poison_event = publish_event(
            db,
            topic="complaints.corrupt_payload",
            payload={"data": "corrupt"},
            college_id=college_id,
        )
        db.commit()

        def failing_handler(topic: str, payload: dict) -> None:
            raise RuntimeError("Database connection timeout or downstream consumer crash")

        # Process attempt 1 -> FAILED, retry_count=1
        count = process_outbox_batch(db, college_id=college_id, handler=failing_handler)
        assert count == 0
        evt = db.get(OutboxEvent, poison_event.id)
        assert evt.status == "FAILED"
        assert evt.retry_count == 1
        assert "downstream consumer crash" in evt.last_error

        # Process attempts 2, 3, 4
        for expected_retries in range(2, 5):
            process_outbox_batch(db, college_id=college_id, handler=failing_handler)
            evt = db.get(OutboxEvent, poison_event.id)
            assert evt.status == "FAILED"
            assert evt.retry_count == expected_retries

        # Attempt 5 -> Moves to DEAD_LETTER
        process_outbox_batch(db, college_id=college_id, handler=failing_handler)
        evt = db.get(OutboxEvent, poison_event.id)
        assert evt.status == "DEAD_LETTER"
        assert evt.retry_count == 5

        # Attempt 6 -> Ignored by normal worker (dead-lettered)
        process_outbox_batch(db, college_id=college_id, handler=failing_handler)
        evt = db.get(OutboxEvent, poison_event.id)
        assert evt.status == "DEAD_LETTER"
        assert evt.retry_count == 5

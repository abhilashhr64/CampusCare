import uuid
import pytest
from sqlalchemy import text
from src.core.database import SessionApp, migrator_engine
from src.modules.knowledge.service import (
    KnowledgeService,
    KnowledgeDocCreate,
    ChunkCreate,
)
from src.modules.assistant.service import (
    AssistantService,
    ConversationCreate,
    ChatRequest,
)


@pytest.fixture
def setup_two_colleges_with_users():
    college_1 = uuid.uuid4()
    college_2 = uuid.uuid4()
    student_c1 = uuid.uuid4()
    student_c2 = uuid.uuid4()

    with migrator_engine.begin() as conn:
        # College 1
        conn.execute(
            text("INSERT INTO colleges (id, name, code, domain, is_active, settings, created_at, updated_at) "
                 "VALUES (:id, 'Apex Institute of Tech', :code, :domain, true, '{}', now(), now())"),
            {"id": college_1, "code": f"col-ai1-{college_1.hex[:6]}", "domain": f"ai1-{college_1.hex[:6]}.edu"},
        )
        conn.execute(text(f"SET LOCAL app.current_college_id = '{college_1}'"))
        conn.execute(
            text("INSERT INTO users (id, college_id, email, full_name, is_email_verified, is_active, is_mfa_enabled, created_at, updated_at) "
                 "VALUES (:id, :cid, 'student@ai1.edu', 'Student One', true, true, false, now(), now())"),
            {"id": student_c1, "cid": college_1},
        )

        # College 2
        conn.execute(
            text("INSERT INTO colleges (id, name, code, domain, is_active, settings, created_at, updated_at) "
                 "VALUES (:id, 'Horizon Polytechnic', :code, :domain, true, '{}', now(), now())"),
            {"id": college_2, "code": f"col-ai2-{college_2.hex[:6]}", "domain": f"ai2-{college_2.hex[:6]}.edu"},
        )
        conn.execute(text(f"SET LOCAL app.current_college_id = '{college_2}'"))
        conn.execute(
            text("INSERT INTO users (id, college_id, email, full_name, is_email_verified, is_active, is_mfa_enabled, created_at, updated_at) "
                 "VALUES (:id, :cid, 'student@ai2.edu', 'Student Two', true, true, false, now(), now())"),
            {"id": student_c2, "cid": college_2},
        )

    return college_1, college_2, student_c1, student_c2


def test_knowledge_ingestion_and_cross_tenant_grounding_isolation(setup_two_colleges_with_users):
    """Rule TN-6 & C2: Knowledge retrieval and chunk embeddings are strictly tenant-isolated.
    College 2 must NEVER retrieve institutional chunks belonging to College 1.
    """
    college_1, college_2, student_c1, student_c2 = setup_two_colleges_with_users

    with SessionApp() as db:
        # Ingest Document into College 1
        doc_c1 = KnowledgeService.create_document(
            db,
            college_1,
            KnowledgeDocCreate(
                title="Apex Academic Regulations 2026",
                category="ACADEMIC",
                audience="ALL",
                source_ref="Academic Handbook Section 4.2",
            ),
        )
        KnowledgeService.add_chunks(
            db,
            college_1,
            doc_c1.id,
            [
                ChunkCreate(
                    chunk_index=1,
                    content="A minimum attendance of 75 percent in each registered subject is mandatory to appear for the semester end examinations.",
                    audience="STUDENT",
                )
            ],
        )

        # Ingest Document into College 2
        doc_c2 = KnowledgeService.create_document(
            db,
            college_2,
            KnowledgeDocCreate(
                title="Horizon Polytechnic Workshop Safety Code",
                category="FACILITY",
                audience="ALL",
                source_ref="Safety Manual Rule 12",
            ),
        )
        KnowledgeService.add_chunks(
            db,
            college_2,
            doc_c2.id,
            [
                ChunkCreate(
                    chunk_index=1,
                    content="Protective eyewear and steel-toe boots are mandatory inside the mechanical engineering foundry.",
                    audience="STUDENT",
                )
            ],
        )

        # Query College 1 for attendance
        res_c1 = KnowledgeService.search_chunks(db, college_1, "minimum attendance 75 percent semester end exam", audience="STUDENT")
        assert len(res_c1) > 0
        assert res_c1[0].document_title == "Apex Academic Regulations 2026"
        assert "75 percent" in res_c1[0].content

        # Rule TN-6 Enforcement: Query College 2 for attendance policy -> Must yield 0 results
        res_cross_tenant = KnowledgeService.search_chunks(db, college_2, "minimum attendance 75 percent semester end exam", audience="STUDENT")
        assert len(res_cross_tenant) == 0, "Security Violation: Cross-tenant institutional chunk leaked!"


def test_citation_grounded_assistant_high_confidence(setup_two_colleges_with_users):
    """Rule B2, B3, C1: High-confidence query produces citation-grounded response citing official policy."""
    college_1, college_2, student_c1, student_c2 = setup_two_colleges_with_users

    with SessionApp() as db:
        doc = KnowledgeService.create_document(
            db,
            college_1,
            KnowledgeDocCreate(
                title="Apex Hostel Living Guidelines",
                category="HOSTEL",
                audience="STUDENT",
                source_ref="Hostel Code Annexure C",
            ),
        )
        KnowledgeService.add_chunks(
            db,
            college_1,
            doc.id,
            [
                ChunkCreate(
                    chunk_index=1,
                    content="Night curfew for all undergraduate residential hostels is strictly 10:30 PM. Late entry requires prior written approval from the resident warden.",
                    audience="STUDENT",
                )
            ],
        )

        # Create Assistant Conversation
        conv = AssistantService.create_conversation(
            db,
            college_1,
            student_c1,
            ConversationCreate(title="Hostel Timing Query"),
        )

        # Chat with Assistant
        req = ChatRequest(query="What is the hostel night curfew timing and late entry policy?", audience="STUDENT")
        msg = AssistantService.chat_grounded(db, college_1, student_c1, conv.id, req)

        assert msg.sender_role == "ASSISTANT"
        assert msg.routing_action == "DIRECT_ANSWER"
        assert msg.confidence_score >= 0.50
        assert len(msg.citations_json) > 0
        assert msg.citations_json[0]["source_ref"] == "Hostel Code Annexure C"
        assert "10:30 PM" in msg.content
        assert "Hostel Code Annexure C" in msg.content


def test_citation_grounded_assistant_low_confidence_escalation(setup_two_colleges_with_users):
    """Rule B2, B4: Low-confidence / undocumented query does NOT hallucinate.
    It prepares a Confirmed Draft Action for student review and human department handling.
    """
    college_1, college_2, student_c1, student_c2 = setup_two_colleges_with_users

    with SessionApp() as db:
        conv = AssistantService.create_conversation(
            db,
            college_1,
            student_c1,
            ConversationCreate(title="Unprecedented Situation"),
        )

        # Ask a totally undocumented question
        req = ChatRequest(query="Can I bring my pet python snake into the chemistry laboratory?", audience="STUDENT")
        msg = AssistantService.chat_grounded(db, college_1, student_c1, conv.id, req)

        assert msg.sender_role == "ASSISTANT"
        assert msg.routing_action == "PROPOSED_DRAFT"
        assert msg.confidence_score < 0.35
        assert "could not locate an official policy" in msg.content

        # Verify Confirmed Draft Action structure (Rule B2, B4)
        assert msg.draft_action_json is not None
        assert msg.draft_action_json["action_type"] == "CREATE_COMPLAINT_DRAFT"
        assert msg.draft_action_json["requires_confirmation"] is True
        assert "snake" in msg.draft_action_json["description"]

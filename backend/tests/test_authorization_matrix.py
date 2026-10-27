import uuid
import pytest
from fastapi.routing import APIRoute
from src.main import app
from src.modules.access.policy import Actor, authorize, Decision


def test_routes_declare_required_permission():
    """Rule AZ-3: Every route declares its required permission.
    A CI test enumerates all routes and fails if any lacks a declaration.
    """
    undeclared_routes = []

    for route in app.routes:
        if isinstance(route, APIRoute):
            # Check only application API routes
            if route.path.startswith("/api/v1"):
                if not hasattr(route.endpoint, "__permission_action__"):
                    undeclared_routes.append(f"{route.methods} {route.path}")

    assert len(undeclared_routes) == 0, (
        f"Rule AZ-3 Violation: The following routes lack a declared required permission:\n"
        + "\n".join(undeclared_routes)
    )


def test_permission_matrix_cross_role_and_cross_tenant():
    """Rule AZ-4: Generate a permission matrix test automatically:
    for each role, each endpoint/action and each of two tenants, assert expected allow or deny.
    Also tests Rules AZ-6, NR-3, NR-5, TN-1.
    """
    college_1 = uuid.uuid4()
    college_2 = uuid.uuid4()

    roles = [
        "STUDENT",
        "LECTURER",
        "DEPARTMENT_ADMIN",
        "COLLEGE_ADMIN",
        "GRIEVANCE_COMMITTEE",
        "PLATFORM_OPERATOR",
    ]

    assigned_class_id = uuid.uuid4()
    other_class_id = uuid.uuid4()

    # Build actors for each role in College 1
    actors_c1 = {
        role: Actor(
            user_id=uuid.uuid4(),
            college_id=college_1,
            email=f"{role.lower()}@college1.edu",
            is_email_verified=True,
            is_mfa_authenticated=True,
            roles=[role],
            role_scopes={
                "LECTURER": {"class_ids": [str(assigned_class_id)]},
                "DEPARTMENT_ADMIN": {"department_id": str(uuid.uuid4())},
            },
        )
        for role in roles
    }

    # Build an actor in College 2
    actor_c2_admin = Actor(
        user_id=uuid.uuid4(),
        college_id=college_2,
        email="admin@college2.edu",
        is_email_verified=True,
        is_mfa_authenticated=True,
        roles=["COLLEGE_ADMIN"],
    )

    # 1. Test Role Approval / Privilege Grants (Rule NR-5, AZ-5)
    # Only COLLEGE_ADMIN of College 1 may approve roles in College 1.
    res_c1 = {"college_id": college_1}
    for role, actor in actors_c1.items():
        dec = authorize(actor, "access:approve_role", res_c1)
        if role == "COLLEGE_ADMIN":
            assert dec.allowed is True, f"College Admin should be allowed: {dec}"
        else:
            assert dec.allowed is False, f"Rule NR-5: Role {role} must NOT be allowed to grant roles: {dec}"

    # Cross-College Denial (College 2 Admin cannot approve roles in College 1)
    dec_cross = authorize(actor_c2_admin, "access:approve_role", res_c1)
    assert dec_cross.allowed is False
    assert dec_cross.reason_code == "DENY_CROSS_TENANT", f"Expected cross-tenant denial: {dec_cross}"

    # 2. Test Attendance Marking & Class Scoping (Rule AZ-6)
    # Lecturer can mark only their assigned class section
    res_assigned = {"college_id": college_1, "class_section_id": assigned_class_id}
    res_unassigned = {"college_id": college_1, "class_section_id": other_class_id}

    dec_assigned = authorize(actors_c1["LECTURER"], "attendance:mark", res_assigned)
    assert dec_assigned.allowed is True

    dec_unassigned = authorize(actors_c1["LECTURER"], "attendance:mark", res_unassigned)
    assert dec_unassigned.allowed is False
    assert dec_unassigned.reason_code == "DENY_CLASS_NOT_ASSIGNED"

    dec_student = authorize(actors_c1["STUDENT"], "attendance:mark", res_assigned)
    assert dec_student.allowed is False
    assert dec_student.reason_code == "DENY_INSUFFICIENT_ROLE"

    # 3. Test Anonymous Feedback Secrecy (Rule AZ-6, NR-10)
    # Individual answers are NEVER visible to lecturers
    res_answers = {"college_id": college_1}
    dec_feed = authorize(actors_c1["LECTURER"], "feedback:view_answers", res_answers)
    assert dec_feed.allowed is False
    assert dec_feed.reason_code == "DENY_LECTURER_INDIVIDUAL_FEEDBACK"

    # 4. Test Sensitive Complaint Isolation
    res_sensitive = {"college_id": college_1, "is_sensitive": True}
    dec_grievance = authorize(actors_c1["GRIEVANCE_COMMITTEE"], "complaints:read", res_sensitive)
    assert dec_grievance.allowed is True

    dec_student_sens = authorize(actors_c1["STUDENT"], "complaints:read", res_sensitive)
    assert dec_student_sens.allowed is False
    assert dec_student_sens.reason_code in ("DENY_NOT_CREATOR", "DENY_SENSITIVE_COMPLAINT_RESTRICTED")

    # 5. Test Unauthenticated / Deny-by-default (Rule NR-3)
    dec_none = authorize(None, "attendance:mark", res_assigned)
    assert dec_none.allowed is False
    assert dec_none.reason_code == "DENY_UNAUTHENTICATED"

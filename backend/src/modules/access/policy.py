import uuid
from typing import Optional, List, Dict, Any, Set
from pydantic import BaseModel, Field


class Actor(BaseModel):
    user_id: uuid.UUID
    college_id: uuid.UUID
    email: str
    is_email_verified: bool = False
    is_mfa_authenticated: bool = False
    roles: List[str] = Field(default_factory=list)
    # role -> scope dict, e.g. {"LECTURER": {"class_ids": ["..."]}, "DEPARTMENT_ADMIN": {"department_id": "..."}}
    role_scopes: Dict[str, Dict[str, Any]] = Field(default_factory=dict)
    is_break_glass: bool = False


class Decision(BaseModel):
    allowed: bool
    reason_code: str
    obligations: Dict[str, Any] = Field(default_factory=dict)


# Set of public actions that do not require an authenticated actor
PUBLIC_ACTIONS: Set[str] = {
    "auth:login",
    "auth:verify_email",
    "auth:verify_code",
    "auth:signup_student",
    "system:health",
}

# Staff roles requiring mandatory MFA (Rule C5, ADR-003)
STAFF_ROLES: Set[str] = {
    "LECTURER",
    "DEPARTMENT_ADMIN",
    "COLLEGE_ADMIN",
    "GRIEVANCE_COMMITTEE",
    "PLATFORM_OPERATOR",
}


def authorize(
    actor: Optional[Actor],
    action: str,
    resource: Optional[Dict[str, Any]] = None,
) -> Decision:
    """Central Policy Decision Function (Rule AZ-1, AZ-2, NR-3).
    Evaluates RBAC + ABAC. Deny-by-default.
    """
    resource = resource or {}

    # 1. Public endpoints check
    if action in PUBLIC_ACTIONS:
        return Decision(allowed=True, reason_code="ALLOW_PUBLIC")

    # 2. Deny-by-default if no authenticated actor
    if not actor:
        return Decision(allowed=False, reason_code="DENY_UNAUTHENTICATED")

    # 3. Cross-Tenant Isolation Enforcement (Rule TN-1, NR-2, AZ-1)
    res_college_id = resource.get("college_id")
    if res_college_id:
        target_cid = (
            res_college_id
            if isinstance(res_college_id, uuid.UUID)
            else uuid.UUID(str(res_college_id))
        )
        if actor.college_id != target_cid and not actor.is_break_glass:
            return Decision(
                allowed=False,
                reason_code="DENY_CROSS_TENANT",
                obligations={"alert_security": True},
            )

    # 4. Email verification required for all authenticated actions
    if not actor.is_email_verified:
        return Decision(allowed=False, reason_code="DENY_UNVERIFIED_EMAIL")

    # 5. Break-glass platform operator path (Rule TN-5)
    if actor.is_break_glass and "PLATFORM_OPERATOR" in actor.roles:
        return Decision(
            allowed=True,
            reason_code="ALLOW_BREAK_GLASS",
            obligations={"audit_reason_required": True, "alert_admin": True},
        )

    # 6. Staff MFA Enforcement (Rule C5)
    user_staff_roles = [r for r in actor.roles if r in STAFF_ROLES]
    if user_staff_roles and not actor.is_mfa_authenticated:
        # MFA challenge must be fulfilled
        if action != "auth:mfa_challenge":
            return Decision(
                allowed=False,
                reason_code="DENY_MFA_REQUIRED",
                obligations={"challenge": "totp"},
            )

    # 7. Action-Specific RBAC + ABAC Evaluations
    # --- Profile & Own Account ---
    if action in ("user:get_profile", "user:update_profile"):
        target_user_id = resource.get("user_id")
        if target_user_id and str(target_user_id) != str(actor.user_id):
            if "COLLEGE_ADMIN" not in actor.roles:
                return Decision(allowed=False, reason_code="DENY_NOT_OWNER")
        return Decision(allowed=True, reason_code="ALLOW_AUTHORIZED")

    # --- Directory (Departments & Courses) ---
    if action == "directory:read":
        return Decision(allowed=True, reason_code="ALLOW_AUTHORIZED")

    if action in ("directory:manage_department", "directory:manage_course"):
        if "COLLEGE_ADMIN" in actor.roles:
            return Decision(allowed=True, reason_code="ALLOW_ADMIN")
        if "DEPARTMENT_ADMIN" in actor.roles:
            dept_scope = actor.role_scopes.get("DEPARTMENT_ADMIN", {}).get("department_id")
            res_dept = resource.get("department_id")
            if dept_scope and res_dept and str(dept_scope) == str(res_dept):
                return Decision(allowed=True, reason_code="ALLOW_DEPARTMENT_ADMIN")
            return Decision(allowed=False, reason_code="DENY_DEPARTMENT_SCOPE_MISMATCH")
        return Decision(allowed=False, reason_code="DENY_INSUFFICIENT_ROLE")

    # --- Attendance Workflows (Rule AZ-6, C7) ---
    if action == "attendance:read":
        if "STUDENT" in actor.roles:
            target_student = resource.get("student_id")
            if target_student and str(target_student) != str(actor.user_id):
                return Decision(allowed=False, reason_code="DENY_STUDENT_CROSS_READ")
            return Decision(allowed=True, reason_code="ALLOW_STUDENT_OWN")
        if "LECTURER" in actor.roles:
            class_id = resource.get("class_section_id")
            lecturer_classes = actor.role_scopes.get("LECTURER", {}).get("class_ids", [])
            if class_id and str(class_id) not in [str(c) for c in lecturer_classes]:
                return Decision(allowed=False, reason_code="DENY_CLASS_NOT_ASSIGNED")
            return Decision(allowed=True, reason_code="ALLOW_LECTURER_ASSIGNED")
        if "DEPARTMENT_ADMIN" in actor.roles or "COLLEGE_ADMIN" in actor.roles:
            return Decision(allowed=True, reason_code="ALLOW_ADMIN")
        return Decision(allowed=False, reason_code="DENY_INSUFFICIENT_ROLE")

    if action in ("attendance:mark", "attendance:sync_offline"):
        if "LECTURER" in actor.roles:
            class_id = resource.get("class_section_id")
            lecturer_classes = actor.role_scopes.get("LECTURER", {}).get("class_ids", [])
            if class_id and str(class_id) not in [str(c) for c in lecturer_classes]:
                return Decision(allowed=False, reason_code="DENY_CLASS_NOT_ASSIGNED")
            return Decision(allowed=True, reason_code="ALLOW_LECTURER_MARK")
        if "COLLEGE_ADMIN" in actor.roles:
            return Decision(allowed=True, reason_code="ALLOW_ADMIN_OVERRIDE", obligations={"audit_reason_required": True})
        return Decision(allowed=False, reason_code="DENY_INSUFFICIENT_ROLE")

    # --- Anonymous Feedback (Rule NR-10, AZ-6) ---
    if action == "feedback:submit":
        if "STUDENT" in actor.roles:
            return Decision(allowed=True, reason_code="ALLOW_STUDENT")
        return Decision(allowed=False, reason_code="DENY_NON_STUDENT_FEEDBACK")

    if action == "feedback:view_answers":
        # Individual answers are NEVER visible to lecturers (Rule AZ-6, NR-10)
        if "LECTURER" in actor.roles:
            return Decision(allowed=False, reason_code="DENY_LECTURER_INDIVIDUAL_FEEDBACK")
        return Decision(allowed=False, reason_code="DENY_RAW_FEEDBACK_RESTRICTED")

    if action == "feedback:view_aggregates":
        # Aggregate feedback is visible only if threshold is met
        k_count = resource.get("response_count", 0)
        if k_count < 5:
            return Decision(allowed=False, reason_code="DENY_K_ANONYMITY_THRESHOLD_NOT_MET")
        if "LECTURER" in actor.roles or "DEPARTMENT_ADMIN" in actor.roles or "COLLEGE_ADMIN" in actor.roles:
            return Decision(allowed=True, reason_code="ALLOW_FEEDBACK_AGGREGATES")
        return Decision(allowed=False, reason_code="DENY_INSUFFICIENT_ROLE")

    # --- Complaints Workflows ---
    if action == "complaints:create":
        if "STUDENT" in actor.roles or "LECTURER" in actor.roles:
            return Decision(allowed=True, reason_code="ALLOW_AUTHORIZED")
        return Decision(allowed=False, reason_code="DENY_INSUFFICIENT_ROLE")

    if action == "complaints:read":
        # Sensitive complaints restricted to Grievance Committee and College Admin (or own creator)
        if resource.get("is_sensitive"):
            if "GRIEVANCE_COMMITTEE" in actor.roles or "COLLEGE_ADMIN" in actor.roles:
                return Decision(allowed=True, reason_code="ALLOW_GRIEVANCE_COMMITTEE")
            creator_id = resource.get("creator_id")
            if "STUDENT" in actor.roles and creator_id and str(creator_id) == str(actor.user_id):
                return Decision(allowed=True, reason_code="ALLOW_CREATOR")
            return Decision(allowed=False, reason_code="DENY_SENSITIVE_COMPLAINT_RESTRICTED")

        # Students see only own non-sensitive complaints
        if "STUDENT" in actor.roles:
            creator_id = resource.get("creator_id")
            if not creator_id or str(creator_id) != str(actor.user_id):
                return Decision(allowed=False, reason_code="DENY_NOT_CREATOR")
            return Decision(allowed=True, reason_code="ALLOW_CREATOR")

        if "DEPARTMENT_ADMIN" in actor.roles or "COLLEGE_ADMIN" in actor.roles or "LECTURER" in actor.roles:
            return Decision(allowed=True, reason_code="ALLOW_STAFF")
        return Decision(allowed=False, reason_code="DENY_INSUFFICIENT_ROLE")


    if action in ("complaints:assign", "complaints:resolve", "complaints:close"):
        if resource.get("is_sensitive"):
            if "GRIEVANCE_COMMITTEE" in actor.roles or "COLLEGE_ADMIN" in actor.roles:
                return Decision(allowed=True, reason_code="ALLOW_GRIEVANCE_COMMITTEE")
            return Decision(allowed=False, reason_code="DENY_SENSITIVE_COMPLAINT_RESTRICTED")
        if "DEPARTMENT_ADMIN" in actor.roles or "COLLEGE_ADMIN" in actor.roles:
            return Decision(allowed=True, reason_code="ALLOW_ADMIN")
        return Decision(allowed=False, reason_code="DENY_INSUFFICIENT_ROLE")

    # --- Role Approvals & Admin Management (Rule NR-5, AZ-5) ---
    if action in ("access:approve_role", "access:revoke_role"):
        if "COLLEGE_ADMIN" in actor.roles:
            return Decision(
                allowed=True,
                reason_code="ALLOW_COLLEGE_ADMIN",
                obligations={"audit_reason_required": True, "step_up_mfa": True},
            )
        return Decision(allowed=False, reason_code="DENY_ADMIN_PRIVILEGE_REQUIRED")

    # Catch-all: Deny-by-default (Rule NR-3)
    return Decision(allowed=False, reason_code="DENY_DEFAULT")

"""CampusCare AI - Pilot Hardening & Seed Script (Phase 5, Rule B2).

Provisions an entire pilot college (Apex Institute of Technology):
- 2 Departments (CSE, ECE)
- Real courses and class sections
- Verified users across all personas (Admin, Dept Admin, Lecturer, Students)
- Institutional knowledge documents and vector chunks
- Complaints with committed SLA clocks
- Anonymous feedback cycle with k >= 5 anonymity
- Supportive attendance tracking records
"""

import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))

import uuid
from datetime import datetime, timezone, date, time
from sqlalchemy import text
from src.core.database import SessionApp, migrator_engine
from src.core.rls import set_tenant_context

# Ensure all models are registered in SQLAlchemy metadata
import src.modules.tenancy.models
import src.modules.identity.models
import src.modules.access.models
import src.modules.directory.models
import src.modules.complaints.models
import src.modules.feedback.models
import src.modules.attendance.models
import src.modules.knowledge.models
import src.modules.notifications.models
import src.modules.analytics.models
import src.modules.audit.models
import src.core.outbox
from src.modules.tenancy.service import TenancyService, CollegeCreate
from src.modules.directory.service import (
    DirectoryService,
    DepartmentCreate,
    CourseCreate,
    ClassSectionCreate,
)
from src.modules.knowledge.service import KnowledgeService, KnowledgeDocCreate, ChunkCreate
from src.modules.complaints.service import ComplaintsService, ComplaintCreate
from src.modules.feedback.service import FeedbackService, FeedbackCycleCreate, FeedbackSubmitRequest
from src.modules.attendance.service import AttendanceService, SessionCreateRequest, AttendanceOpEntry
from src.modules.notifications.service import NotificationService
from src.modules.access.service import AccessService, RoleGrantCreate


def seed_pilot_data():
    print(">>> Initializing CampusCare AI Pilot Environment (Phase 5)...")

    # 1. Provision College Tenant under migrator engine
    with SessionApp() as db:
        # Check if Apex already exists
        existing_colleges = TenancyService.get_all_active_colleges(db)
        apex = next((c for c in existing_colleges if c.domain == "apex.edu"), None)

        if not apex:
            apex = TenancyService.create_college(
                db,
                CollegeCreate(
                    name="Apex Institute of Technology",
                    domain="apex.edu",
                    code="APEX",
                ),
            )
            print(f"Created Pilot College: Apex Institute of Technology ({apex.id})")
        else:
            print(f"Found Existing Pilot College: Apex Institute of Technology ({apex.id})")

        college_id = apex.id

    # 2. Provision Pilot Users
    admin_id = uuid.uuid4()
    dept_admin_id = uuid.uuid4()
    lecturer_id = uuid.uuid4()
    student_1_id = uuid.uuid4()
    student_2_id = uuid.uuid4()

    with migrator_engine.begin() as conn:
        conn.execute(text(f"SET LOCAL app.current_college_id = '{college_id}'"))

        # College Director / Management Person
        admin_id = conn.execute(
            text(
                "INSERT INTO users (id, college_id, email, phone_number, full_name, is_email_verified, is_active, is_mfa_enabled, created_at, updated_at) "
                "VALUES (:id, :cid, 'admin@apex.edu', '+919845011001', 'Dr. S. K. Raman (Director & Principal)', true, true, true, now(), now()) "
                "ON CONFLICT (college_id, email) DO UPDATE SET phone_number = '+919845011001', is_active = true RETURNING id"
            ),
            {"id": admin_id, "cid": college_id},
        ).scalar_one()

        # Transport Head (Campus Transit & Bus Fleet In-charge)
        transport_id = uuid.uuid4()
        transport_id = conn.execute(
            text(
                "INSERT INTO users (id, college_id, email, phone_number, full_name, is_email_verified, is_active, is_mfa_enabled, created_at, updated_at) "
                "VALUES (:id, :cid, 'transport.head@apex.edu', '+919845011002', 'Rajesh Gowda (Transport Head)', true, true, true, now(), now()) "
                "ON CONFLICT (college_id, email) DO UPDATE SET phone_number = '+919845011002', is_active = true RETURNING id"
            ),
            {"id": transport_id, "cid": college_id},
        ).scalar_one()

        # Chief Hostel Warden (Residential Blocks A/B/C & Dining Mess)
        warden_id = uuid.uuid4()
        warden_id = conn.execute(
            text(
                "INSERT INTO users (id, college_id, email, phone_number, full_name, is_email_verified, is_active, is_mfa_enabled, created_at, updated_at) "
                "VALUES (:id, :cid, 'hostel.warden@apex.edu', '+919845011003', 'Col. Mahendra Singh (Chief Hostel Warden)', true, true, true, now(), now()) "
                "ON CONFLICT (college_id, email) DO UPDATE SET phone_number = '+919845011003', is_active = true RETURNING id"
            ),
            {"id": warden_id, "cid": college_id},
        ).scalar_one()

        # Finance & Accounts Bursar
        bursar_id = uuid.uuid4()
        bursar_id = conn.execute(
            text(
                "INSERT INTO users (id, college_id, email, phone_number, full_name, is_email_verified, is_active, is_mfa_enabled, created_at, updated_at) "
                "VALUES (:id, :cid, 'bursar@apex.edu', '+919845011004', 'Dr. K. Raghavan (Finance Officer & Bursar)', true, true, true, now(), now()) "
                "ON CONFLICT (college_id, email) DO UPDATE SET phone_number = '+919845011004', is_active = true RETURNING id"
            ),
            {"id": bursar_id, "cid": college_id},
        ).scalar_one()

        # Campus Estate & Facilities Head
        facilities_id = uuid.uuid4()
        facilities_id = conn.execute(
            text(
                "INSERT INTO users (id, college_id, email, phone_number, full_name, is_email_verified, is_active, is_mfa_enabled, created_at, updated_at) "
                "VALUES (:id, :cid, 'estate.officer@apex.edu', '+919845011005', 'Er. Suresh Kumar (Estate & Facilities Head)', true, true, true, now(), now()) "
                "ON CONFLICT (college_id, email) DO UPDATE SET phone_number = '+919845011005', is_active = true RETURNING id"
            ),
            {"id": facilities_id, "cid": college_id},
        ).scalar_one()

        # Department Admin (CSE)
        dept_admin_id = conn.execute(
            text(
                "INSERT INTO users (id, college_id, email, phone_number, full_name, is_email_verified, is_active, is_mfa_enabled, created_at, updated_at) "
                "VALUES (:id, :cid, 'cse.admin@apex.edu', '+919845011006', 'Prof. Sunita Reddy (HOD CSE)', true, true, true, now(), now()) "
                "ON CONFLICT (college_id, email) DO UPDATE SET phone_number = '+919845011006', is_active = true RETURNING id"
            ),
            {"id": dept_admin_id, "cid": college_id},
        ).scalar_one()

        # Lecturer
        lecturer_id = conn.execute(
            text(
                "INSERT INTO users (id, college_id, email, phone_number, full_name, is_email_verified, is_active, is_mfa_enabled, created_at, updated_at) "
                "VALUES (:id, :cid, 'prof.rao@apex.edu', '+919845011007', 'Prof. Raghav Rao', true, true, true, now(), now()) "
                "ON CONFLICT (college_id, email) DO UPDATE SET phone_number = '+919845011007', is_active = true RETURNING id"
            ),
            {"id": lecturer_id, "cid": college_id},
        ).scalar_one()

        # Student 1 (Aarav Sharma)
        student_1_id = conn.execute(
            text(
                "INSERT INTO users (id, college_id, email, phone_number, roll_number, full_name, is_email_verified, is_active, is_mfa_enabled, created_at, updated_at) "
                "VALUES (:id, :cid, 'aarav.sharma@apex.edu', '+919845022001', '26CS01', 'Aarav Sharma', true, true, false, now(), now()) "
                "ON CONFLICT (college_id, email) DO UPDATE SET phone_number = '+919845022001', roll_number = '26CS01', is_active = true RETURNING id"
            ),
            {"id": student_1_id, "cid": college_id},
        ).scalar_one()

        # Student 2 (Dev Patel)
        student_2_id = conn.execute(
            text(
                "INSERT INTO users (id, college_id, email, phone_number, roll_number, full_name, is_email_verified, is_active, is_mfa_enabled, created_at, updated_at) "
                "VALUES (:id, :cid, 'dev.patel@apex.edu', '+919845022002', '26CS03', 'Dev Patel', true, true, false, now(), now()) "
                "ON CONFLICT (college_id, email) DO UPDATE SET phone_number = '+919845022002', roll_number = '26CS03', is_active = true RETURNING id"
            ),
            {"id": student_2_id, "cid": college_id},
        ).scalar_one()

    print("Provisioned Real College Authorities: Director, Transport Head, Hostel Warden, Bursar, Estate Officer, HOD, Faculty, Students")

    # 3. Grant Explicit Roles (Rule AZ-5)
    with SessionApp() as db:
        set_tenant_context(db, college_id=college_id)
        AccessService.grant_role(
            db,
            college_id,
            admin_id,
            RoleGrantCreate(user_id=admin_id, role="COLLEGE_MANAGEMENT", reason="Executive Management Appointment"),
        )
        AccessService.grant_role(
            db,
            college_id,
            admin_id,
            RoleGrantCreate(user_id=admin_id, role="COLLEGE_ADMIN", reason="Pilot College Administrator Onboarding"),
        )
        AccessService.grant_role(
            db,
            college_id,
            admin_id,
            RoleGrantCreate(user_id=transport_id, role="TRANSPORT_HEAD", reason="Campus Transit & Fleet In-charge"),
        )
        AccessService.grant_role(
            db,
            college_id,
            admin_id,
            RoleGrantCreate(user_id=warden_id, role="HOSTEL_WARDEN", reason="Chief Hostel Warden Residential Appointment"),
        )
        AccessService.grant_role(
            db,
            college_id,
            admin_id,
            RoleGrantCreate(user_id=bursar_id, role="BURSAR_ACCOUNTS", reason="Finance & Fee Treasury Officer"),
        )
        AccessService.grant_role(
            db,
            college_id,
            admin_id,
            RoleGrantCreate(user_id=facilities_id, role="FACILITIES_HEAD", reason="Campus Infrastructure & Estate Officer"),
        )
        AccessService.grant_role(
            db,
            college_id,
            admin_id,
            RoleGrantCreate(user_id=dept_admin_id, role="DEPARTMENT_ADMIN", reason="CSE HOD Admin Assignment"),
        )
        AccessService.grant_role(
            db,
            college_id,
            admin_id,
            RoleGrantCreate(user_id=lecturer_id, role="LECTURER", reason="CSE Faculty Appointment"),
        )
        AccessService.grant_role(
            db,
            college_id,
            admin_id,
            RoleGrantCreate(user_id=student_1_id, role="STUDENT", reason="Undergraduate Enrolled Student (26CS01)"),
        )
        AccessService.grant_role(
            db,
            college_id,
            admin_id,
            RoleGrantCreate(user_id=student_2_id, role="STUDENT", reason="Undergraduate Enrolled Student (26CS03)"),
        )
    print("Granted RBAC/ABAC Scoped Roles")

    # 4. Departments & Courses
    with SessionApp() as db:
        existing_depts = DirectoryService.list_departments(db, college_id)
        cse = next((d for d in existing_depts if d.code == "CSE"), None)
        if not cse:
            cse = DirectoryService.create_department(
                db, college_id, DepartmentCreate(code="CSE", name="Computer Science and Engineering")
            )
        ece = next((d for d in existing_depts if d.code == "ECE"), None)
        if not ece:
            ece = DirectoryService.create_department(
                db, college_id, DepartmentCreate(code="ECE", name="Electronics and Communication")
            )

        existing_courses = DirectoryService.list_courses(db, college_id)
        course_os = next((c for c in existing_courses if c.code == "CS301"), None)
        if not course_os:
            course_os = DirectoryService.create_course(
                db, college_id, CourseCreate(department_id=cse.id, code="CS301", title="Operating Systems")
            )
        course_db = next((c for c in existing_courses if c.code == "CS302"), None)
        if not course_db:
            course_db = DirectoryService.create_course(
                db, college_id, CourseCreate(department_id=cse.id, code="CS302", title="Database Systems")
            )
        course_dsp = next((c for c in existing_courses if c.code == "EC301"), None)
        if not course_dsp:
            course_dsp = DirectoryService.create_course(
                db, college_id, CourseCreate(department_id=ece.id, code="EC301", title="Digital Signal Processing")
            )

        sec_os = DirectoryService.create_class_section(
            db,
            college_id,
            ClassSectionCreate(
                course_id=course_os.id,
                lecturer_id=lecturer_id,
                section_name="Section A",
                semester=5,
                academic_year="2026-27",
            ),
        )

        # Enroll Students
        with migrator_engine.begin() as conn:
            conn.execute(text(f"SET LOCAL app.current_college_id = '{college_id}'"))
            conn.execute(
                text(
                    "INSERT INTO directory_enrollments (id, college_id, student_id, class_section_id, roll_number, created_at) "
                    "VALUES (gen_random_uuid(), :cid, :sid, :sec_id, '26CS01', now()) "
                    "ON CONFLICT DO NOTHING"
                ),
                {"cid": college_id, "sid": student_1_id, "sec_id": sec_os.id},
            )
            conn.execute(
                text(
                    "INSERT INTO directory_enrollments (id, college_id, student_id, class_section_id, roll_number, created_at) "
                    "VALUES (gen_random_uuid(), :cid, :sid, :sec_id, '26CS03', now()) "
                    "ON CONFLICT DO NOTHING"
                ),
                {"cid": college_id, "sid": student_2_id, "sec_id": sec_os.id},
            )

    print("Created CSE & ECE Departments, Courses, and Section Enrollments")

    # 5. Institutional Knowledge Base & Document Ingestion (Rule TN-6, B2)
    with SessionApp() as db:
        # Academic & Attendance Regulations
        doc_academic = KnowledgeService.create_document(
            db,
            college_id,
            KnowledgeDocCreate(
                title="Apex Academic Regulations 2026-27",
                category="ACADEMIC",
                source_ref="Section 4.2 - Attendance & Examination Eligibility",
                audience="ALL",
            ),
        )
        KnowledgeService.add_chunks(
            db,
            college_id,
            doc_academic.id,
            [
                ChunkCreate(
                    chunk_index=0,
                    content=(
                        "A minimum attendance of 75 percent in each registered theory and laboratory subject "
                        "is mandatory to appear for the semester end examinations. Students with attendance "
                        "between 65% and 74% may apply for condonation on valid medical grounds with authorized documentation."
                    ),
                    audience="ALL",
                ),
                ChunkCreate(
                    chunk_index=1,
                    content=(
                        "All student grievances regarding facility maintenance, lab equipment, and academic infrastructure "
                        "must be resolved within committed service promise SLAs: 24 hours for lab equipment/power issues, "
                        "and 48 hours for general academic and classroom facility requests."
                    ),
                    audience="ALL",
                ),
            ],
        )

        # Transport & Transit Fleet Regulations
        doc_transport = KnowledgeService.create_document(
            db,
            college_id,
            KnowledgeDocCreate(
                title="Apex Transport & Transit Fleet Manual 2026-27",
                category="TRANSPORT",
                source_ref="Office of Transportation - Fleet Operations Section 2.1",
                audience="ALL",
            ),
        )
        KnowledgeService.add_chunks(
            db,
            college_id,
            doc_transport.id,
            [
                ChunkCreate(
                    chunk_index=0,
                    content=(
                        "College bus fleet operates 18 dedicated routes across the metropolitan region. "
                        "Morning buses arrive at campus by 8:35 AM; evening departures begin strictly at 4:45 PM. "
                        "Bus pass renewal occurs biannually at the Transport Helpdesk or via the student portal. "
                        "In case of route delay or bus breakdown, replacement shuttles are dispatched within 20 minutes."
                    ),
                    audience="ALL",
                ),
                ChunkCreate(
                    chunk_index=1,
                    content=(
                        "Transport complaints regarding driver conduct, rash driving, AC malfunctions, or route delays "
                        "are monitored under a 24-hour turnaround SLA by the Office of Transportation & Transit Fleet. "
                        "Students can track real-time bus locations and report transit disruptions directly through CampusCare."
                    ),
                    audience="ALL",
                ),
            ],
        )

        # Hostel & Residential Regulations
        doc_hostel = KnowledgeService.create_document(
            db,
            college_id,
            KnowledgeDocCreate(
                title="Apex Hostel & Residential Life Handbook 2026-27",
                category="HOSTEL",
                source_ref="Chief Warden Board - Residential Guidelines Chapter 5",
                audience="ALL",
            ),
        )
        KnowledgeService.add_chunks(
            db,
            college_id,
            doc_hostel.id,
            [
                ChunkCreate(
                    chunk_index=0,
                    content=(
                        "Hostel campus curfew is 9:30 PM on weekdays and 10:00 PM on weekends. "
                        "Hot water geysers operate daily during morning hours (5:30 AM to 9:00 AM) and evening hours (5:30 PM to 8:30 PM). "
                        "Mess rebate of 80 rupees per day is granted for absences exceeding 3 consecutive days with 48-hour prior digital intimation."
                    ),
                    audience="ALL",
                ),
                ChunkCreate(
                    chunk_index=1,
                    content=(
                        "Residential maintenance issues including electrical tripping, plumbing leaks, room furniture damage, "
                        "and water cooler filters are assigned a strict 24-hour SLA under the Chief Warden & Residential Housing Board. "
                        "Emergency issues (water stagnation, power outage) are attended to within 2 hours."
                    ),
                    audience="ALL",
                ),
            ],
        )

        # Fee, Accounts & Bursar Charter
        doc_fee = KnowledgeService.create_document(
            db,
            college_id,
            KnowledgeDocCreate(
                title="Apex Bursar, Fee & Financial Accounts Charter 2026-27",
                category="FEE_ACCOUNTS",
                source_ref="Finance & Accounts Division - Tuition Policy Article 3",
                audience="ALL",
            ),
        )
        KnowledgeService.add_chunks(
            db,
            college_id,
            doc_fee.id,
            [
                ChunkCreate(
                    chunk_index=0,
                    content=(
                        "Semester tuition fee payments must be settled by the 15th of the semester commencement month. "
                        "A grace period is provided until the 30th with a late fine of 500 rupees; thereafter, 1000 rupees applies. "
                        "Installment payment plans (up to 3 installments) can be approved upon written request to the Bursar Office."
                    ),
                    audience="ALL",
                ),
                ChunkCreate(
                    chunk_index=1,
                    content=(
                        "For UPI, NEFT, or Net Banking transactions where amounts are debited from student bank accounts "
                        "but the ERP portal reflects unpaid status, students should provide the UTR or Transaction Reference number. "
                        "The Finance & Accounts Bursar Office reconciles bank payment gateway logs within 48 hours and issues official e-receipts."
                    ),
                    audience="ALL",
                ),
            ],
        )

        # IT & NOC Computing Infrastructure
        doc_it = KnowledgeService.create_document(
            db,
            college_id,
            KnowledgeDocCreate(
                title="Apex Campus IT & Computing Infrastructure Policy 2026-27",
                category="IT",
                source_ref="Network Operations Center - User Access Standards",
                audience="ALL",
            ),
        )
        KnowledgeService.add_chunks(
            db,
            college_id,
            doc_it.id,
            [
                ChunkCreate(
                    chunk_index=0,
                    content=(
                        "Campus Wi-Fi (Apex-Secure and eduroam) is available across all academic blocks, hostels, and libraries. "
                        "Students authenticate using their official institutional email ID and portal password. "
                        "Password resets and MAC address registrations are serviced by the NOC Helpdesk located in Computing Block A."
                    ),
                    audience="ALL",
                ),
                ChunkCreate(
                    chunk_index=1,
                    content=(
                        "Advanced AI & High-Performance Computing workstations equipped with NVIDIA GPUs in Lab 3 "
                        "are accessible to all registered CSE and ECE students. "
                        "Network dropouts, portal access bugs, or system hardware faults are resolved within 24 hours by Campus IT & NOC."
                    ),
                    audience="ALL",
                ),
            ],
        )

    print("Ingested Official Knowledge Base with RAG Chunks across Academics, Transport, Hostel, Fee Accounts, and IT")

    # 6. Seed Complaints with Committed SLA & Location Tags
    with SessionApp() as db:
        comp = ComplaintsService.create_complaint(
            db,
            college_id,
            student_1_id,
            ComplaintCreate(
                category="FACILITY",
                title="Lab 4 Compiler Software Licenses Expired",
                description="All terminal workstations in Lab Block A are showing GCC license activation timeout.",
                location_tag="QR:LAB-4-401",
                sla_committed_hours=24,
            ),
        )

    print(f"Dispatched Pilot Complaint with Committed SLA: {comp.ticket_number} (QR:LAB-4-401)")

    # 7. Seed Anonymous Feedback Cycle
    with SessionApp() as db:
        cycle = FeedbackService.create_cycle(
            db,
            college_id,
            FeedbackCycleCreate(
                title="Fall 2026 Mid-Semester Teaching Evaluation",
                academic_term="2026-FALL",
                k_anonymity_threshold=5,
            ),
        )

    print(f"Opened Anonymous Feedback Evaluation Cycle: {cycle.title} (k >= 5 Protected)")

    print("\n=======================================================")
    print(">>> CAMPUSCARE AI PILOT ENVIRONMENT SUCCESSFULLY SEEDED")
    print("=======================================================")
    print(f"Tenant: Apex Institute of Technology ({college_id})")
    print(f"College Admin: admin@apex.edu (MFA Enabled)")
    print(f"Dept Admin (CSE): cse.admin@apex.edu (MFA Enabled)")
    print(f"Lecturer: prof.rao@apex.edu (Assigned CS301 Sec A)")
    print(f"Student: aarav.sharma@apex.edu (Roll 26CS01)")
    print("=======================================================\n")


if __name__ == "__main__":
    seed_pilot_data()

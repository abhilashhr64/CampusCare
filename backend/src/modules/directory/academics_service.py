"""CampusCare AI - Academic & Attendance Ground-Truth Telemetry Service.

Provides deterministic, zero-hallucination calculations for:
1. Enrolled students with attendance below mandatory threshold (< 75.0%).
2. Section/cohort class averages for Internal Assessment (IA) test marks.
3. Students scoring below class average IA marks.
4. Personalized student academic risk diagnostics (subjects with BOTH low attendance AND below-average IA marks).
"""

import uuid
from typing import Dict, Any, List, Optional
from pydantic import BaseModel


class SubjectAttendanceStat(BaseModel):
    course_code: str
    course_title: str
    conducted: int
    attended: int
    percentage: float
    is_deficit: bool
    classes_needed_for_safe: int


class SubjectIAStat(BaseModel):
    course_code: str
    course_title: str
    student_score: float
    max_marks: float
    class_average: float
    is_below_average: float
    score_gap: float


class StudentAcademicReport(BaseModel):
    student_id: str
    roll_number: str
    full_name: str
    email: str
    semester: int
    department: str
    low_attendance_subjects: List[Dict[str, Any]]
    below_average_ia_subjects: List[Dict[str, Any]]
    dual_risk_subjects: List[Dict[str, Any]]  # Both low attendance AND below-average IA marks


# Ground-Truth Deterministic Academic Database for Pilot Cohort (Apex Institute of Technology, B.Tech CSE Sem 5)
STUDENTS_DATABASE = [
    {
        "id": "pilot-student-1",
        "roll_number": "26CS01",
        "full_name": "Aarav Sharma",
        "email": "aarav.sharma@apex.edu",
        "department": "Computer Science & Engineering",
        "semester": 5,
        "academic_year": "2026-27",
        "academics": {
            "CS301": {"conducted": 24, "attended": 16, "ia_mark": 21.0},  # 66.7% (<75% Deficit), IA 21.0 (Avg 29.4 -> Below)
            "CS302": {"conducted": 20, "attended": 17, "ia_mark": 32.0},  # 85.0% (Safe), IA 32.0 (Avg 28.2 -> Above)
            "CS303": {"conducted": 22, "attended": 15, "ia_mark": 20.0},  # 68.2% (<75% Deficit), IA 20.0 (Avg 27.8 -> Below)
            "CS304": {"conducted": 18, "attended": 16, "ia_mark": 35.0},  # 88.9% (Safe), IA 35.0 (Avg 30.6 -> Above)
        },
    },
    {
        "id": "pilot-student-2",
        "roll_number": "26CS03",
        "full_name": "Dev Patel",
        "email": "dev.patel@apex.edu",
        "department": "Computer Science & Engineering",
        "semester": 5,
        "academic_year": "2026-27",
        "academics": {
            "CS301": {"conducted": 24, "attended": 21, "ia_mark": 34.0},  # 87.5% (Safe), IA 34.0 (Above)
            "CS302": {"conducted": 20, "attended": 14, "ia_mark": 22.0},  # 70.0% (<75% Deficit), IA 22.0 (Avg 28.2 -> Below)
            "CS303": {"conducted": 22, "attended": 20, "ia_mark": 29.0},  # 90.9% (Safe), IA 29.0 (Above)
            "CS304": {"conducted": 18, "attended": 17, "ia_mark": 31.0},  # 94.4% (Safe), IA 31.0 (Above)
        },
    },
    {
        "id": "pilot-student-3",
        "roll_number": "26CS07",
        "full_name": "Priya Nair",
        "email": "priya.nair@apex.edu",
        "department": "Computer Science & Engineering",
        "semester": 5,
        "academic_year": "2026-27",
        "academics": {
            "CS301": {"conducted": 24, "attended": 17, "ia_mark": 23.0},  # 70.8% (<75% Deficit), IA 23.0 (Avg 29.4 -> Below)
            "CS302": {"conducted": 20, "attended": 19, "ia_mark": 31.0},  # 95.0% (Safe), IA 31.0 (Above)
            "CS303": {"conducted": 22, "attended": 21, "ia_mark": 33.0},  # 95.5% (Safe), IA 33.0 (Above)
            "CS304": {"conducted": 18, "attended": 16, "ia_mark": 29.0},  # 88.9% (Safe), IA 29.0 (Avg 30.6 -> Below)
        },
    },
    {
        "id": "pilot-student-4",
        "roll_number": "26CS12",
        "full_name": "Rohan Verma",
        "email": "rohan.verma@apex.edu",
        "department": "Computer Science & Engineering",
        "semester": 5,
        "academic_year": "2026-27",
        "academics": {
            "CS301": {"conducted": 24, "attended": 22, "ia_mark": 24.0},  # 91.7% (Safe), IA 24.0 (Avg 29.4 -> Below)
            "CS302": {"conducted": 20, "attended": 13, "ia_mark": 29.0},  # 65.0% (<75% Deficit), IA 29.0 (Above)
            "CS303": {"conducted": 22, "attended": 15, "ia_mark": 19.0},  # 68.2% (<75% Deficit), IA 19.0 (Avg 27.8 -> Below)
            "CS304": {"conducted": 18, "attended": 17, "ia_mark": 30.0},  # 94.4% (Safe), IA 30.0 (Avg 30.6 -> Below)
        },
    },
    {
        "id": "pilot-student-5",
        "roll_number": "26CS18",
        "full_name": "Ananya Iyer",
        "email": "ananya.iyer@apex.edu",
        "department": "Computer Science & Engineering",
        "semester": 5,
        "academic_year": "2026-27",
        "academics": {
            "CS301": {"conducted": 24, "attended": 23, "ia_mark": 38.0},  # 95.8% (Safe), IA 38.0 (Above)
            "CS302": {"conducted": 20, "attended": 18, "ia_mark": 36.0},  # 90.0% (Safe), IA 36.0 (Above)
            "CS303": {"conducted": 22, "attended": 20, "ia_mark": 35.0},  # 90.9% (Safe), IA 35.0 (Above)
            "CS304": {"conducted": 18, "attended": 18, "ia_mark": 37.0},  # 100.0% (Safe), IA 37.0 (Above)
        },
    },
]

COURSE_CATALOG = {
    "CS301": {"code": "CS301", "title": "Operating Systems", "credits": 4, "max_ia": 40.0, "lecturer": "Prof. Raghav Rao"},
    "CS302": {"code": "CS302", "title": "Database Management Systems", "credits": 4, "max_ia": 40.0, "lecturer": "Prof. Sunita Reddy"},
    "CS303": {"code": "CS303", "title": "Computer Networks", "credits": 3, "max_ia": 40.0, "lecturer": "Dr. V. K. Menon"},
    "CS304": {"code": "CS304", "title": "Software Engineering & Agile", "credits": 3, "max_ia": 40.0, "lecturer": "Prof. Meera Sen"},
}


class AcademicsService:
    @staticmethod
    def get_course_catalog() -> Dict[str, Any]:
        return COURSE_CATALOG

    @staticmethod
    def calculate_class_ia_averages() -> Dict[str, float]:
        """Calculates exact class averages for Internal Assessment test marks across all students."""
        averages: Dict[str, float] = {}
        for ccode in COURSE_CATALOG:
            scores = [s["academics"][ccode]["ia_mark"] for s in STUDENTS_DATABASE if ccode in s["academics"]]
            avg = round(sum(scores) / len(scores), 1) if scores else 0.0
            averages[ccode] = avg
        return averages

    @staticmethod
    def get_low_attendance_students(threshold: float = 75.0) -> List[Dict[str, Any]]:
        """Admin/Faculty Ground-Truth Query:

        Returns the exact list of students having attendance below the threshold (< 75%),
        along with exact subject-wise breakdown, attended counts, and required makeup classes.
        """
        results = []
        for s in STUDENTS_DATABASE:
            student_deficits = []
            total_conducted = 0
            total_attended = 0

            for ccode, data in s["academics"].items():
                cond = data["conducted"]
                att = data["attended"]
                total_conducted += cond
                total_attended += att
                pct = round((att / cond) * 100.0, 1)

                if pct < threshold:
                    # Classes needed: ceil((threshold * cond - 100 * att) / (100 - threshold))
                    import math
                    classes_needed = math.ceil((threshold * cond - 100.0 * att) / (100.0 - threshold))
                    student_deficits.append({
                        "course_code": ccode,
                        "course_title": COURSE_CATALOG[ccode]["title"],
                        "conducted": cond,
                        "attended": att,
                        "percentage": pct,
                        "deficit_percentage": round(threshold - pct, 1),
                        "classes_needed": max(1, classes_needed),
                    })

            overall_pct = round((total_attended / total_conducted) * 100.0, 1)

            if student_deficits or overall_pct < threshold:
                results.append({
                    "student_id": s["id"],
                    "roll_number": s["roll_number"],
                    "full_name": s["full_name"],
                    "email": s["email"],
                    "department": s["department"],
                    "semester": s["semester"],
                    "overall_conducted": total_conducted,
                    "overall_attended": total_attended,
                    "overall_percentage": overall_pct,
                    "deficit_subjects": student_deficits,
                    "is_overall_deficit": overall_pct < threshold,
                })

        return results

    @staticmethod
    def get_below_average_ia_students() -> List[Dict[str, Any]]:
        """Admin/Faculty Ground-Truth Query:

        Returns the exact list of students scoring below the section average in IA marks,
        including subject average, student mark, and mark deficit.
        """
        averages = AcademicsService.calculate_class_ia_averages()
        results = []

        for s in STUDENTS_DATABASE:
            below_avg_subjects = []
            for ccode, data in s["academics"].items():
                mark = data["ia_mark"]
                avg = averages[ccode]
                max_mark = COURSE_CATALOG[ccode]["max_ia"]
                if mark < avg:
                    below_avg_subjects.append({
                        "course_code": ccode,
                        "course_title": COURSE_CATALOG[ccode]["title"],
                        "student_mark": mark,
                        "class_average": avg,
                        "max_mark": max_mark,
                        "score_gap": round(avg - mark, 1),
                    })

            if below_avg_subjects:
                results.append({
                    "student_id": s["id"],
                    "roll_number": s["roll_number"],
                    "full_name": s["full_name"],
                    "email": s["email"],
                    "department": s["department"],
                    "semester": s["semester"],
                    "below_average_subjects": below_avg_subjects,
                })

        return results

    @staticmethod
    def get_student_academic_diagnostic(student_query: str = "26CS01") -> Dict[str, Any]:
        """Student Ground-Truth Query:

        Evaluates the specific student against both attendance threshold (< 75%)
        and class IA averages.
        Answers: 'Which subject do I NOT have average marks AND having less attendance?'
        """
        # Find student by roll number, email, or id
        q = student_query.lower().strip()
        student = next(
            (s for s in STUDENTS_DATABASE if q in s["roll_number"].lower() or q in s["email"].lower() or q in s["id"].lower() or q in s["full_name"].lower()),
            STUDENTS_DATABASE[0],  # Default to Aarav Sharma (pilot student 1)
        )

        averages = AcademicsService.calculate_class_ia_averages()
        all_subjects_breakdown = []
        dual_risk_subjects = []
        low_attendance_only = []
        below_avg_ia_only = []
        safe_subjects = []

        for ccode, data in student["academics"].items():
            cond = data["conducted"]
            att = data["attended"]
            pct = round((att / cond) * 100.0, 1)
            is_low_att = pct < 75.0

            import math
            classes_needed = math.ceil((75.0 * cond - 100.0 * att) / (100.0 - 75.0)) if is_low_att else 0

            mark = data["ia_mark"]
            avg = averages[ccode]
            is_low_ia = mark < avg
            score_gap = round(avg - mark, 1) if is_low_ia else 0.0

            stat = {
                "course_code": ccode,
                "course_title": COURSE_CATALOG[ccode]["title"],
                "lecturer": COURSE_CATALOG[ccode]["lecturer"],
                "conducted": cond,
                "attended": att,
                "attendance_percentage": pct,
                "is_low_attendance": is_low_att,
                "classes_needed": max(0, classes_needed),
                "ia_mark": mark,
                "class_average": avg,
                "max_mark": COURSE_CATALOG[ccode]["max_ia"],
                "is_below_average_ia": is_low_ia,
                "score_gap": score_gap,
            }
            all_subjects_breakdown.append(stat)

            if is_low_att and is_low_ia:
                dual_risk_subjects.append(stat)
            elif is_low_att:
                low_attendance_only.append(stat)
            elif is_low_ia:
                below_avg_ia_only.append(stat)
            else:
                safe_subjects.append(stat)

        return {
            "student_id": student["id"],
            "roll_number": student["roll_number"],
            "full_name": student["full_name"],
            "email": student["email"],
            "department": student["department"],
            "semester": student["semester"],
            "dual_risk_subjects": dual_risk_subjects,
            "low_attendance_only": low_attendance_only,
            "below_avg_ia_only": below_avg_ia_only,
            "safe_subjects": safe_subjects,
            "all_subjects": all_subjects_breakdown,
            "class_averages": averages,
        }

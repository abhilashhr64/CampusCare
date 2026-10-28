"""CampusCare AI - Academic & Attendance Telemetry Router."""

from fastapi import APIRouter, Query
from typing import Dict, Any, List
from src.modules.directory.academics_service import AcademicsService

router = APIRouter(prefix="/academics", tags=["Academics & Attendance Ground Truth"])


@router.get("/attendance/deficit-students")
def get_low_attendance_students(threshold: float = Query(75.0, ge=50.0, le=100.0)) -> List[Dict[str, Any]]:
    """Ground-Truth Admin/Faculty Query:

    Returns exact list of enrolled students having attendance below threshold (< 75.0%).
    """
    return AcademicsService.get_low_attendance_students(threshold=threshold)


@router.get("/ia-marks/below-average-students")
def get_below_average_ia_students() -> List[Dict[str, Any]]:
    """Ground-Truth Admin/Faculty Query:

    Returns exact list of enrolled students scoring below the section average in Internal Assessment (IA) marks.
    """
    return AcademicsService.get_below_average_ia_students()


@router.get("/student/diagnostic")
def get_student_academic_diagnostic(student_query: str = Query("26CS01")) -> Dict[str, Any]:
    """Ground-Truth Student Query:

    Answers 'Which subject do I NOT have average marks AND having less attendance?'
    with zero hallucination.
    """
    return AcademicsService.get_student_academic_diagnostic(student_query=student_query)


@router.get("/catalog")
def get_academic_catalog() -> Dict[str, Any]:
    """Returns courses and class IA averages."""
    return {
        "catalog": AcademicsService.get_course_catalog(),
        "class_ia_averages": AcademicsService.calculate_class_ia_averages(),
    }

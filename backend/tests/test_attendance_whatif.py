import pytest
from src.modules.attendance.service import AttendanceService


def test_attendance_what_if_surplus():
    """Rule B3: Attended 18 of 20 classes. Target = 75%.
    Should be safe and able to miss 4 classes.
    """
    res = AttendanceService.calculate_what_if(conducted=20, attended=18, target_percentage=75.0)
    assert res["is_safe"] is True
    assert res["status"] == "SURPLUS"
    assert res["classes_can_miss"] == 4
    assert res["classes_must_attend"] == 0
    # Verification: 18 / 24 = 75%
    pct_after_miss = (18 / (20 + 4)) * 100.0
    assert pct_after_miss >= 75.0


def test_attendance_what_if_deficit():
    """Rule B3: Attended 14 of 20 classes (70%). Target = 75%.
    Must attend 4 consecutive classes to reach 75%.
    """
    res = AttendanceService.calculate_what_if(conducted=20, attended=14, target_percentage=75.0)
    assert res["is_safe"] is False
    assert res["status"] == "DEFICIT"
    assert res["classes_must_attend"] == 4
    assert res["classes_can_miss"] == 0
    # Verification: (14 + 4) / (20 + 4) = 18 / 24 = 75%
    pct_after_attend = ((14 + 4) / (20 + 4)) * 100.0
    assert pct_after_attend >= 75.0


def test_attendance_what_if_exactly_on_target():
    """Rule B3: Exactly 75% attendance (15/20). Cannot miss any classes."""
    res = AttendanceService.calculate_what_if(conducted=20, attended=15, target_percentage=75.0)
    assert res["is_safe"] is True
    assert res["status"] == "ON_TARGET"
    assert res["classes_can_miss"] == 0
    assert res["classes_must_attend"] == 0


def test_attendance_what_if_zero_classes():
    """Rule B3: Zero conducted classes at term start."""
    res = AttendanceService.calculate_what_if(conducted=0, attended=0, target_percentage=75.0)
    assert res["is_safe"] is True
    assert res["current_percentage"] == 100.0


def test_attendance_what_if_invalid_inputs():
    """Rule B3: Attended > Conducted raises ValueError."""
    with pytest.raises(ValueError):
        AttendanceService.calculate_what_if(conducted=10, attended=15, target_percentage=75.0)

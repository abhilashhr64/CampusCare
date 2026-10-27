import math
from typing import Dict, Any


class AttendanceService:
    @staticmethod
    def calculate_what_if(
        conducted: int,
        attended: int,
        target_percentage: float = 75.0,
    ) -> Dict[str, Any]:
        """Deterministic attendance calculator (Rule B3 Signature Capability).
        Calculates the exact classes a student must attend or can miss per subject.
        Tested, deterministic, zero AI dependency.
        """
        if conducted < 0 or attended < 0 or attended > conducted:
            raise ValueError("Attended classes cannot exceed conducted classes or be negative.")

        if not (0 < target_percentage < 100):
            raise ValueError("Target threshold must be between 1 and 99 percent.")

        if conducted == 0:
            return {
                "conducted": 0,
                "attended": 0,
                "current_percentage": 100.0,
                "target_threshold": target_percentage,
                "is_safe": True,
                "status": "ON_TARGET",
                "classes_can_miss": 0,
                "classes_must_attend": 0,
            }

        current_pct = (attended / conducted) * 100.0
        rounded_pct = round(current_pct, 1)

        if current_pct >= target_percentage:
            # Surplus state
            can_miss = math.floor((100.0 * attended - target_percentage * conducted) / target_percentage)
            return {
                "conducted": conducted,
                "attended": attended,
                "current_percentage": rounded_pct,
                "target_threshold": target_percentage,
                "is_safe": True,
                "status": "SURPLUS" if can_miss > 0 else "ON_TARGET",
                "classes_can_miss": max(0, can_miss),
                "classes_must_attend": 0,
            }
        else:
            # Deficit state
            must_attend = math.ceil(
                (target_percentage * conducted - 100.0 * attended) / (100.0 - target_percentage)
            )
            return {
                "conducted": conducted,
                "attended": attended,
                "current_percentage": rounded_pct,
                "target_threshold": target_percentage,
                "is_safe": False,
                "status": "DEFICIT",
                "classes_can_miss": 0,
                "classes_must_attend": max(0, must_attend),
            }

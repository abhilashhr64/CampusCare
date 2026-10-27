export interface AttendanceWhatIfResult {
  currentTotal: number;
  currentAttended: number;
  currentPercentage: number;
  targetThreshold: number;
  isSafe: boolean;
  status: "SURPLUS" | "DEFICIT" | "ON_TARGET";
  classesCanMiss: number;
  classesMustAttend: number;
  explanation: string;
}

export function calculateAttendanceWhatIf(
  conducted: number,
  attended: number,
  targetPercentage: number = 75
): AttendanceWhatIfResult {
  if (conducted < 0 || attended < 0 || attended > conducted) {
    throw new Error("Invalid attendance figures: attended cannot exceed conducted classes.");
  }

  if (targetPercentage <= 0 || targetPercentage >= 100) {
    throw new Error("Target threshold must be between 1 and 99 percent.");
  }

  if (conducted === 0) {
    return {
      currentTotal: 0,
      currentAttended: 0,
      currentPercentage: 100,
      targetThreshold: targetPercentage,
      isSafe: true,
      status: "ON_TARGET",
      classesCanMiss: 0,
      classesMustAttend: 0,
      explanation: "No classes conducted yet. Perfect baseline attendance.",
    };
  }

  const currentPct = (attended / conducted) * 100;
  const roundedPct = Math.round(currentPct * 10) / 10;

  if (currentPct >= targetPercentage) {
    // Student is in SURPLUS
    // Formula: floor((100 * attended - target * conducted) / target)
    const canMiss = Math.floor((100 * attended - targetPercentage * conducted) / targetPercentage);
    return {
      currentTotal: conducted,
      currentAttended: attended,
      currentPercentage: roundedPct,
      targetThreshold: targetPercentage,
      isSafe: true,
      status: canMiss > 0 ? "SURPLUS" : "ON_TARGET",
      classesCanMiss: Math.max(0, canMiss),
      classesMustAttend: 0,
      explanation:
        canMiss > 0
          ? `You are safe! You can miss up to ${canMiss} consecutive upcoming class${canMiss === 1 ? "" : "es"} and still stay above ${targetPercentage}%.`
          : `You are exactly on target at ${roundedPct}%. Missing any class will put you at risk.`,
    };
  } else {
    // Student is in DEFICIT
    // Formula: ceil((target * conducted - 100 * attended) / (100 - target))
    const mustAttend = Math.ceil((targetPercentage * conducted - 100 * attended) / (100 - targetPercentage));
    return {
      currentTotal: conducted,
      currentAttended: attended,
      currentPercentage: roundedPct,
      targetThreshold: targetPercentage,
      isSafe: false,
      status: "DEFICIT",
      classesCanMiss: 0,
      classesMustAttend: Math.max(0, mustAttend),
      explanation: `Attendance deficit! You must attend the next ${mustAttend} consecutive class${mustAttend === 1 ? "" : "es"} without absence to reach ${targetPercentage}%.`,
    };
  }
}

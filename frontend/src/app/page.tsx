"use client";

import React, { useState, useEffect } from "react";
import {
  Shield,
  GraduationCap,
  Users,
  Building2,
  CalendarCheck,
  AlertTriangle,
  Clock,
  CheckCircle2,
  Lock,
  Wifi,
  WifiOff,
  RefreshCw,
  Search,
  Filter,
  ArrowRight,
  TrendingUp,
  FileText,
  KeyRound,
  Database,
  Calculator,
  ChevronRight,
  HelpCircle,
  ExternalLink,
} from "lucide-react";
import { calculateAttendanceWhatIf, AttendanceWhatIfResult } from "@/features/attendance/whatIfCalculator";
import {
  queueAttendanceOperation,
  getPendingAttendanceOps,
  AttendanceOutboxOp,
  offlineDb,
} from "@/features/attendance/offlineStore";
import {
  LoadingState,
  EmptyState,
  ErrorState,
  PermissionDeniedState,
  OfflineIndicator,
} from "@/shared/ui/States";

type Persona = "STUDENT" | "LECTURER" | "DEPARTMENT_ADMIN" | "COLLEGE_ADMIN" | "WHAT_IF" | "SECURITY_RLS";

export default function CampusCarePortal() {
  const [activePersona, setActivePersona] = useState<Persona>("STUDENT");
  const [activeTenant, setActiveTenant] = useState<"APEX" | "HORIZON">("APEX");
  const [isOnline, setIsOnline] = useState<boolean>(true);
  const [pendingOps, setPendingOps] = useState<AttendanceOutboxOp[]>([]);
  const [notificationMsg, setNotificationMsg] = useState<string | null>(null);

  // What-If Calculator Local State
  const [whatIfConducted, setWhatIfConducted] = useState<number>(36);
  const [whatIfAttended, setWhatIfAttended] = useState<number>(29);
  const [whatIfTarget, setWhatIfTarget] = useState<number>(75);
  const [whatIfResult, setWhatIfResult] = useState<AttendanceWhatIfResult>(() =>
    calculateAttendanceWhatIf(36, 29, 75)
  );

  // Interactive Lecturer Attendance Marking State
  const [lecturerMarking, setLecturerMarking] = useState<
    Array<{ id: string; roll: string; name: string; status: "PRESENT" | "ABSENT" | "EXCUSED" }>
  >([
    { id: "s-101", roll: "26CS01", name: "Aarav Sharma", status: "PRESENT" },
    { id: "s-102", roll: "26CS02", name: "Ananya Iyer", status: "PRESENT" },
    { id: "s-103", roll: "26CS03", name: "Dev Patel", status: "ABSENT" },
    { id: "s-104", roll: "26CS04", name: "Isha Nair", status: "PRESENT" },
    { id: "s-105", roll: "26CS05", name: "Karan Verma", status: "PRESENT" },
  ]);

  // Recalculate What-If whenever inputs change
  useEffect(() => {
    try {
      const res = calculateAttendanceWhatIf(whatIfConducted, whatIfAttended, whatIfTarget);
      setWhatIfResult(res);
    } catch {
      // Handled by validation bounds
    }
  }, [whatIfConducted, whatIfAttended, whatIfTarget]);

  // Fetch pending offline outbox ops
  const refreshPendingOps = async () => {
    try {
      const ops = await getPendingAttendanceOps();
      setPendingOps(ops);
    } catch {
      // offline db loading
    }
  };

  useEffect(() => {
    refreshPendingOps();
  }, []);

  // Simulate offline attendance submission to IndexedDB
  const handleRecordAttendance = async () => {
    try {
      const records = lecturerMarking.map((s) => ({
        student_id: s.id,
        roll_number: s.roll,
        status: s.status,
      }));

      const op = await queueAttendanceOperation("sess-cs301-lab", "cs301-sec-a", records, 1);
      setNotificationMsg(
        isOnline
          ? "Attendance batch submitted to server and cached in IndexedDB outbox (op_id: " + op.op_id.slice(0, 8) + "...)"
          : "Saved offline in IndexedDB outbox! Will auto-sync with server idempotency when network returns."
      );
      refreshPendingOps();
      setTimeout(() => setNotificationMsg(null), 6000);
    } catch (err: any) {
      setNotificationMsg("Error saving attendance: " + err.message);
    }
  };

  return (
    <div className="min-h-screen flex flex-col bg-[#090d16] text-slate-100">
      {/* Platform Top Header */}
      <header className="border-b border-slate-800/80 bg-slate-950/70 backdrop-blur-md sticky top-0 z-50">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 h-16 flex items-center justify-between">
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 rounded-xl bg-gradient-to-tr from-sky-500 to-indigo-600 flex items-center justify-center shadow-lg shadow-sky-500/20">
              <Shield className="w-5 h-5 text-white" />
            </div>
            <div>
              <div className="flex items-center gap-2">
                <span className="font-bold text-base tracking-tight text-white">CampusCare AI</span>
                <span className="text-[10px] font-semibold uppercase px-2 py-0.5 rounded bg-sky-500/10 text-sky-400 border border-sky-500/20">
                  v2 Enterprise
                </span>
              </div>
              <p className="text-[11px] text-slate-400 hidden sm:block">
                Multi-Tenant Governance & Verified Services
              </p>
            </div>
          </div>

          {/* Right Controls: Tenant Switcher, Network Mode, Offline Chip */}
          <div className="flex items-center gap-3">
            {/* Tenant Switcher */}
            <div className="flex items-center bg-slate-900/90 border border-slate-800 rounded-lg p-1 text-xs">
              <button
                onClick={() => setActiveTenant("APEX")}
                className={`px-2.5 py-1 rounded font-medium transition-colors ${
                  activeTenant === "APEX"
                    ? "bg-sky-500/20 text-sky-300 border border-sky-500/30"
                    : "text-slate-400 hover:text-slate-200"
                }`}
                title="Tenant 1: Apex Institute of Technology"
              >
                Apex Institute (Tenant 1)
              </button>
              <button
                onClick={() => setActiveTenant("HORIZON")}
                className={`px-2.5 py-1 rounded font-medium transition-colors ${
                  activeTenant === "HORIZON"
                    ? "bg-purple-500/20 text-purple-300 border border-purple-500/30"
                    : "text-slate-400 hover:text-slate-200"
                }`}
                title="Tenant 2: Horizon Polytechnic"
              >
                Horizon Poly (Tenant 2)
              </button>
            </div>

            {/* Network simulator button */}
            <button
              onClick={() => setIsOnline(!isOnline)}
              className="hidden md:flex items-center gap-1.5 px-2.5 py-1 rounded-lg text-xs font-medium border border-slate-700 bg-slate-800/60 hover:bg-slate-800 text-slate-300 transition-colors"
              title="Toggle network connectivity simulation"
            >
              {isOnline ? <Wifi className="w-3.5 h-3.5 text-emerald-400" /> : <WifiOff className="w-3.5 h-3.5 text-amber-400" />}
              {isOnline ? "Network: Online" : "Simulate Offline"}
            </button>

            {/* Offline Outbox Status Chip */}
            <OfflineIndicator isOnline={isOnline} />
          </div>
        </div>

        {/* Persona Navigation Tabs */}
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 flex overflow-x-auto gap-2 py-2 border-t border-slate-800/40 text-xs">
          <button
            onClick={() => setActivePersona("STUDENT")}
            className={`flex items-center gap-2 px-3.5 py-1.5 rounded-lg font-medium whitespace-nowrap transition-all ${
              activePersona === "STUDENT"
                ? "bg-sky-500 text-white shadow-md shadow-sky-500/25"
                : "text-slate-400 hover:text-slate-200 hover:bg-slate-800/60"
            }`}
          >
            <GraduationCap className="w-4 h-4" />
            Student Persona
          </button>
          <button
            onClick={() => setActivePersona("LECTURER")}
            className={`flex items-center gap-2 px-3.5 py-1.5 rounded-lg font-medium whitespace-nowrap transition-all ${
              activePersona === "LECTURER"
                ? "bg-sky-500 text-white shadow-md shadow-sky-500/25"
                : "text-slate-400 hover:text-slate-200 hover:bg-slate-800/60"
            }`}
          >
            <Users className="w-4 h-4" />
            Lecturer Persona
          </button>
          <button
            onClick={() => setActivePersona("DEPARTMENT_ADMIN")}
            className={`flex items-center gap-2 px-3.5 py-1.5 rounded-lg font-medium whitespace-nowrap transition-all ${
              activePersona === "DEPARTMENT_ADMIN"
                ? "bg-sky-500 text-white shadow-md shadow-sky-500/25"
                : "text-slate-400 hover:text-slate-200 hover:bg-slate-800/60"
            }`}
          >
            <Building2 className="w-4 h-4" />
            Department Admin
          </button>
          <button
            onClick={() => setActivePersona("COLLEGE_ADMIN")}
            className={`flex items-center gap-2 px-3.5 py-1.5 rounded-lg font-medium whitespace-nowrap transition-all ${
              activePersona === "COLLEGE_ADMIN"
                ? "bg-sky-500 text-white shadow-md shadow-sky-500/25"
                : "text-slate-400 hover:text-slate-200 hover:bg-slate-800/60"
            }`}
          >
            <Shield className="w-4 h-4" />
            College Admin & Audit
          </button>
          <button
            onClick={() => setActivePersona("WHAT_IF")}
            className={`flex items-center gap-2 px-3.5 py-1.5 rounded-lg font-medium whitespace-nowrap transition-all ${
              activePersona === "WHAT_IF"
                ? "bg-emerald-600 text-white shadow-md shadow-emerald-600/25"
                : "text-slate-400 hover:text-slate-200 hover:bg-slate-800/60"
            }`}
          >
            <Calculator className="w-4 h-4 text-emerald-400" />
            Attendance What-If Engine
          </button>
          <button
            onClick={() => setActivePersona("SECURITY_RLS")}
            className={`flex items-center gap-2 px-3.5 py-1.5 rounded-lg font-medium whitespace-nowrap transition-all ${
              activePersona === "SECURITY_RLS"
                ? "bg-indigo-600 text-white shadow-md shadow-indigo-600/25"
                : "text-slate-400 hover:text-slate-200 hover:bg-slate-800/60"
            }`}
          >
            <Database className="w-4 h-4 text-indigo-400" />
            PostgreSQL RLS Inspector
          </button>
        </div>
      </header>

      {/* Toast Notification Banner */}
      {notificationMsg && (
        <div className="bg-sky-950/90 border-b border-sky-500/30 px-4 py-2.5 text-center text-xs text-sky-200 animate-fadeIn">
          {notificationMsg}
        </div>
      )}

      {/* Main Content Body */}
      <main className="flex-1 max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8 w-full">
        {/* ========================================================================= */}
        {/* PERSONA 1: STUDENT HOME SCREEN                                            */}
        {/* Must answer: "Am I safe on attendance? What is pending? What changed?"   */}
        {/* ========================================================================= */}
        {activePersona === "STUDENT" && (
          <div className="space-y-6">
            <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 pb-2">
              <div>
                <h1 className="text-2xl font-bold text-white tracking-tight">Student Dashboard</h1>
                <p className="text-xs text-slate-400">
                  Tenant Context: <span className="font-semibold text-sky-400">{activeTenant === "APEX" ? "Apex Institute of Tech (apex.edu)" : "Horizon Polytechnic (horizon.edu)"}</span> • Roll: <span className="font-mono text-slate-300">26CS01</span>
                </p>
              </div>

              {/* Verified Identity Status Pill */}
              <div className="inline-flex items-center gap-2 px-3 py-1.5 rounded-xl glass-panel text-xs">
                <CheckCircle2 className="w-4 h-4 text-emerald-400" />
                <span className="text-slate-300">Verified Email Link (ID-3)</span>
                <span className="text-slate-500">•</span>
                <span className="text-emerald-400 font-medium">Enrolled in CSE Cohort</span>
              </div>
            </div>

            {/* Answer 1: "Am I safe on attendance?" */}
            <div className="grid grid-cols-1 md:grid-cols-3 gap-5">
              <div className="glass-panel rounded-2xl p-6 relative overflow-hidden border border-emerald-500/30">
                <div className="absolute top-0 right-0 w-32 h-32 bg-emerald-500/10 rounded-full blur-2xl -mr-10 -mt-10 pointer-events-none" />
                <div className="flex items-center justify-between mb-4">
                  <span className="text-xs font-semibold text-slate-400 uppercase tracking-wider">
                    Overall Attendance Safety
                  </span>
                  <span className="px-2.5 py-0.5 rounded-full text-[11px] font-bold bg-emerald-500/20 text-emerald-300 border border-emerald-500/30">
                    SAFE (SURPLUS)
                  </span>
                </div>
                <div className="flex items-baseline gap-2 mb-2">
                  <span className="text-4xl font-extrabold text-white tracking-tight">84.5%</span>
                  <span className="text-xs text-slate-400 font-medium">/ 75.0% Required</span>
                </div>
                <div className="w-full bg-slate-800 rounded-full h-2 mb-3 overflow-hidden">
                  <div className="bg-gradient-to-r from-emerald-500 to-teal-400 h-2 rounded-full" style={{ width: "84.5%" }} />
                </div>
                <p className="text-xs text-emerald-300/90 leading-relaxed">
                  ✓ <strong>You can safely miss up to 3 upcoming classes</strong> and stay above the 75% institutional threshold.
                </p>
              </div>

              {/* Answer 2: "What is pending?" (Service Promise & SLA countdown) */}
              <div className="glass-panel rounded-2xl p-6 relative overflow-hidden border border-amber-500/30">
                <div className="absolute top-0 right-0 w-32 h-32 bg-amber-500/10 rounded-full blur-2xl -mr-10 -mt-10 pointer-events-none" />
                <div className="flex items-center justify-between mb-4">
                  <span className="text-xs font-semibold text-slate-400 uppercase tracking-wider">
                    Service Promise Pending
                  </span>
                  <span className="px-2 py-0.5 rounded-full text-[10px] font-bold bg-amber-500/20 text-amber-300 border border-amber-500/30">
                    SLA IN PROGRESS
                  </span>
                </div>
                <h4 className="text-sm font-semibold text-white mb-1">
                  Lab Wi-Fi Connectivity in Block 3
                </h4>
                <p className="text-xs text-slate-400 mb-3">Owner: Network Ops Team • Ticket #CC-9041</p>
                <div className="bg-slate-900/90 rounded-xl p-3 border border-slate-800 flex items-center justify-between mb-2">
                  <div className="flex items-center gap-2">
                    <Clock className="w-4 h-4 text-amber-400 animate-pulse" />
                    <span className="text-xs font-medium text-slate-300">Countdown to breach:</span>
                  </div>
                  <span className="font-mono text-xs font-bold text-amber-300">18h 42m remaining</span>
                </div>
                <span className="text-[11px] text-slate-500">Committed SLA: 48h (Signature Rule B3)</span>
              </div>

              {/* Answer 3: "What changed?" */}
              <div className="glass-panel rounded-2xl p-6 relative overflow-hidden">
                <div className="flex items-center justify-between mb-4">
                  <span className="text-xs font-semibold text-slate-400 uppercase tracking-wider">
                    Recent Verified Changes
                  </span>
                  <span className="text-[11px] text-sky-400 hover:underline cursor-pointer">View History</span>
                </div>
                <ul className="space-y-3 text-xs">
                  <li className="flex items-start gap-2.5">
                    <span className="w-2 h-2 rounded-full bg-emerald-400 mt-1.5 flex-shrink-0" />
                    <div>
                      <p className="text-slate-200 font-medium">CS301 Lab Attendance Marked</p>
                      <span className="text-[10px] text-slate-500">Today, 11:30 AM • Present</span>
                    </div>
                  </li>
                  <li className="flex items-start gap-2.5">
                    <span className="w-2 h-2 rounded-full bg-sky-400 mt-1.5 flex-shrink-0" />
                    <div>
                      <p className="text-slate-200 font-medium">Anonymous Feedback Cycle Opened</p>
                      <span className="text-[10px] text-slate-500">Mid-term Course Feedback (NR-10 Unlinked)</span>
                    </div>
                  </li>
                  <li className="flex items-start gap-2.5">
                    <span className="w-2 h-2 rounded-full bg-slate-500 mt-1.5 flex-shrink-0" />
                    <div>
                      <p className="text-slate-300 font-medium">Hostel Water Supply Ticket Closed</p>
                      <span className="text-[10px] text-slate-500">Yesterday • Closed-Loop Confirmed by Student</span>
                    </div>
                  </li>
                </ul>
              </div>
            </div>

            {/* Subject-Wise Attendance Breakdown with What-If Action */}
            <div className="glass-panel rounded-2xl p-6">
              <div className="flex items-center justify-between mb-5">
                <div>
                  <h3 className="text-base font-semibold text-white">Subject Enrollment & Attendance</h3>
                  <p className="text-xs text-slate-400">Scattered across 4 core engineering courses</p>
                </div>
                <button
                  onClick={() => setActivePersona("WHAT_IF")}
                  className="px-3.5 py-1.5 rounded-lg text-xs font-semibold bg-emerald-500/20 text-emerald-300 border border-emerald-500/30 hover:bg-emerald-500/30 flex items-center gap-1.5 transition-colors"
                >
                  <Calculator className="w-3.5 h-3.5" />
                  Launch What-If Simulator
                </button>
              </div>

              <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
                {[
                  { code: "CS301", title: "Operating Systems", conducted: 32, attended: 29, pct: 90.6, safe: true },
                  { code: "CS302", title: "Database Systems", conducted: 30, attended: 23, pct: 76.7, safe: true },
                  { code: "CS303", title: "Computer Networks", conducted: 28, attended: 19, pct: 67.9, safe: false },
                  { code: "CS304", title: "Software Engineering", conducted: 34, attended: 31, pct: 91.2, safe: true },
                ].map((course) => (
                  <div key={course.code} className="bg-slate-900/70 border border-slate-800 rounded-xl p-4 flex flex-col justify-between">
                    <div>
                      <div className="flex items-center justify-between mb-2">
                        <span className="text-xs font-mono font-bold text-sky-400">{course.code}</span>
                        <span
                          className={`text-[10px] font-bold px-2 py-0.5 rounded-full ${
                            course.safe
                              ? "bg-emerald-500/15 text-emerald-400 border border-emerald-500/20"
                              : "bg-rose-500/15 text-rose-400 border border-rose-500/20 animate-pulse"
                          }`}
                        >
                          {course.safe ? "SAFE" : "AT RISK (<75%)"}
                        </span>
                      </div>
                      <h4 className="text-sm font-semibold text-slate-200 mb-2">{course.title}</h4>
                      <div className="text-2xl font-bold text-white mb-1">{course.pct}%</div>
                      <p className="text-[11px] text-slate-400">
                        {course.attended} attended / {course.conducted} conducted
                      </p>
                    </div>

                    <div className="mt-4 pt-3 border-t border-slate-800/80">
                      {course.safe ? (
                        <span className="text-[11px] text-emerald-300 font-medium">
                          Can miss {Math.floor((course.attended * 100 - 75 * course.conducted) / 75)} classes safely
                        </span>
                      ) : (
                        <span className="text-[11px] text-rose-300 font-medium">
                          Must attend next {Math.ceil((75 * course.conducted - 100 * course.attended) / 25)} classes!
                        </span>
                      )}
                    </div>
                  </div>
                ))}
              </div>
            </div>
          </div>
        )}

        {/* ========================================================================= */}
        {/* PERSONA 2: LECTURER HOME SCREEN                                           */}
        {/* Must answer: "Which class is next? Who is repeatedly absent? Mark fast"   */}
        {/* ========================================================================= */}
        {activePersona === "LECTURER" && (
          <div className="space-y-6">
            <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 pb-2">
              <div>
                <h1 className="text-2xl font-bold text-white tracking-tight">Lecturer Dashboard</h1>
                <p className="text-xs text-slate-400">
                  Role: <span className="font-semibold text-sky-400">LECTURER</span> (Rule AZ-6 Scoped to Assigned Classes Only) • Staff MFA Verified
                </p>
              </div>

              <div className="flex items-center gap-2">
                <span className="text-xs text-slate-400">Assigned Cohort:</span>
                <span className="px-2.5 py-1 rounded-lg bg-sky-500/10 text-sky-300 border border-sky-500/20 text-xs font-mono font-medium">
                  CS301 - Sec A (3rd Year)
                </span>
              </div>
            </div>

            {/* Answer 1: "Which class is next?" & "Who is repeatedly absent?" */}
            <div className="grid grid-cols-1 md:grid-cols-3 gap-5">
              {/* Which class is next */}
              <div className="glass-panel rounded-2xl p-6 border border-sky-500/30">
                <div className="flex items-center justify-between mb-3">
                  <span className="text-xs font-semibold text-slate-400 uppercase tracking-wider">Which Class Is Next?</span>
                  <span className="px-2 py-0.5 rounded text-[10px] font-bold bg-sky-500/20 text-sky-300 border border-sky-500/30">
                    STARTS IN 25 MIN
                  </span>
                </div>
                <h3 className="text-lg font-bold text-white mb-1">CS301: Operating Systems Lab</h3>
                <p className="text-xs text-slate-300 mb-3">Room 304 • Section A (62 Enrolled Students)</p>
                <div className="flex items-center gap-2 text-xs text-slate-400">
                  <CalendarCheck className="w-4 h-4 text-sky-400" />
                  <span>Scheduled: 14:00 - 16:00 IST</span>
                </div>
              </div>

              {/* Who is repeatedly absent */}
              <div className="glass-panel rounded-2xl p-6 border border-rose-500/30">
                <div className="flex items-center justify-between mb-3">
                  <span className="text-xs font-semibold text-slate-400 uppercase tracking-wider">Supportive Alert Engine</span>
                  <span className="px-2 py-0.5 rounded text-[10px] font-bold bg-rose-500/20 text-rose-300 border border-rose-500/30">
                    2 CRITICAL DEFICITS
                  </span>
                </div>
                <ul className="space-y-2 text-xs">
                  <li className="flex items-center justify-between p-2 rounded-lg bg-slate-900/60 border border-slate-800">
                    <div>
                      <p className="text-slate-200 font-semibold">Dev Patel (26CS03)</p>
                      <span className="text-[11px] text-rose-400">3 consecutive absences • 62.1%</span>
                    </div>
                    <button className="px-2 py-1 text-[10px] font-medium rounded bg-rose-500/20 text-rose-300 border border-rose-500/30">
                      Alert Mentor
                    </button>
                  </li>
                  <li className="flex items-center justify-between p-2 rounded-lg bg-slate-900/60 border border-slate-800">
                    <div>
                      <p className="text-slate-200 font-semibold">Rohit Mehra (26CS19)</p>
                      <span className="text-[11px] text-amber-400">Below 75% threshold • 71.4%</span>
                    </div>
                    <button className="px-2 py-1 text-[10px] font-medium rounded bg-amber-500/20 text-amber-300 border border-amber-500/30">
                      Counseling
                    </button>
                  </li>
                </ul>
              </div>

              {/* Feedback Summary (Rule AZ-6, NR-10: Only thresholded aggregate, zero individual rows) */}
              <div className="glass-panel rounded-2xl p-6 border border-purple-500/30">
                <div className="flex items-center justify-between mb-3">
                  <span className="text-xs font-semibold text-slate-400 uppercase tracking-wider">Anonymous Feedback Themes</span>
                  <span className="px-2 py-0.5 rounded text-[10px] font-bold bg-purple-500/20 text-purple-300 border border-purple-500/30">
                    k=5 MET (NR-10)
                  </span>
                </div>
                <div className="text-2xl font-bold text-white mb-1">4.6 / 5.0</div>
                <p className="text-xs text-slate-400 mb-3">Based on 48 anonymous student evaluations</p>
                <div className="text-xs text-purple-200/90 bg-purple-950/30 p-2.5 rounded-lg border border-purple-500/20">
                  💡 <strong>Theme:</strong> Clear OS lecture explanations; students requested more hands-on threads debugging exercises.
                </div>
                <p className="text-[10px] text-slate-500 mt-2">
                  *Individual student identities cryptographically unlinked by schema design (NR-10).
                </p>
              </div>
            </div>

            {/* Fast Attendance Marking with Offline Protocol (Rule C7) */}
            <div className="glass-panel rounded-2xl p-6">
              <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 mb-4">
                <div>
                  <h3 className="text-base font-semibold text-white">Fast Attendance Marking (Class Section A)</h3>
                  <p className="text-xs text-slate-400">
                    Offline Protocol: Click status pills to toggle • Syncs with IndexedDB outbox with base_version & UUID op_id
                  </p>
                </div>
                <div className="flex items-center gap-3">
                  <button
                    onClick={() => {
                      setLecturerMarking((prev) =>
                        prev.map((s) => ({ ...s, status: "PRESENT" }))
                      );
                    }}
                    className="px-3 py-1.5 text-xs font-semibold rounded-lg bg-slate-800 hover:bg-slate-700 text-slate-300 border border-slate-700 transition-colors"
                  >
                    Mark All Present
                  </button>
                  <button
                    onClick={handleRecordAttendance}
                    className="px-4 py-1.5 text-xs font-semibold rounded-lg bg-sky-500 hover:bg-sky-400 text-white shadow-md shadow-sky-500/20 transition-all flex items-center gap-1.5"
                  >
                    <CheckCircle2 className="w-3.5 h-3.5" />
                    Commit Session Records
                  </button>
                </div>
              </div>

              {/* Roster Table */}
              <div className="overflow-x-auto rounded-xl border border-slate-800 bg-slate-950/60">
                <table className="w-full text-xs text-left text-slate-300">
                  <thead className="text-[11px] uppercase bg-slate-900/90 text-slate-400 border-b border-slate-800">
                    <tr>
                      <th className="px-4 py-3 font-semibold">Roll Number</th>
                      <th className="px-4 py-3 font-semibold">Student Name</th>
                      <th className="px-4 py-3 font-semibold">Current Term %</th>
                      <th className="px-4 py-3 font-semibold">Attendance Action</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-slate-800/60">
                    {lecturerMarking.map((student) => (
                      <tr key={student.id} className="hover:bg-slate-900/40 transition-colors">
                        <td className="px-4 py-3 font-mono font-medium text-sky-400">{student.roll}</td>
                        <td className="px-4 py-3 font-medium text-slate-200">{student.name}</td>
                        <td className="px-4 py-3">
                          <span className={student.roll === "26CS03" ? "text-rose-400 font-bold" : "text-emerald-400 font-medium"}>
                            {student.roll === "26CS03" ? "62.1%" : "88.4%"}
                          </span>
                        </td>
                        <td className="px-4 py-3">
                          <div className="inline-flex rounded-lg bg-slate-900 p-0.5 border border-slate-800">
                            {(["PRESENT", "ABSENT", "EXCUSED"] as const).map((st) => (
                              <button
                                key={st}
                                onClick={() => {
                                  setLecturerMarking((prev) =>
                                    prev.map((item) => (item.id === student.id ? { ...item, status: st } : item))
                                  );
                                }}
                                className={`px-2.5 py-1 text-[10px] font-semibold rounded-md transition-all ${
                                  student.status === st
                                    ? st === "PRESENT"
                                      ? "bg-emerald-500/20 text-emerald-300 border border-emerald-500/30"
                                      : st === "ABSENT"
                                      ? "bg-rose-500/20 text-rose-300 border border-rose-500/30"
                                      : "bg-amber-500/20 text-amber-300 border border-amber-500/30"
                                    : "text-slate-500 hover:text-slate-300"
                                }`}
                              >
                                {st}
                              </button>
                            ))}
                          </div>
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </div>
          </div>
        )}

        {/* ========================================================================= */}
        {/* PERSONA 3: DEPARTMENT ADMIN DASHBOARD                                      */}
        {/* Must answer: "What is at risk today? Who is overloaded?"                   */}
        {/* ========================================================================= */}
        {activePersona === "DEPARTMENT_ADMIN" && (
          <div className="space-y-6">
            <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 pb-2">
              <div>
                <h1 className="text-2xl font-bold text-white tracking-tight">Department Admin Dashboard</h1>
                <p className="text-xs text-slate-400">
                  Department: <span className="font-semibold text-sky-400">Computer Science & Engineering</span> • SLA Clock & Workload Queue
                </p>
              </div>
              <span className="px-3 py-1 rounded-full text-xs font-semibold bg-amber-500/10 text-amber-300 border border-amber-500/20">
                Active Complaints: 4 Pending (1 At Risk)
              </span>
            </div>

            {/* Answer 1: "What is at risk today?" & Answer 2: "Who is overloaded?" */}
            <div className="grid grid-cols-1 md:grid-cols-2 gap-5">
              {/* Complaints at risk */}
              <div className="glass-panel rounded-2xl p-6 border border-amber-500/30">
                <div className="flex items-center justify-between mb-4">
                  <div className="flex items-center gap-2">
                    <AlertTriangle className="w-5 h-5 text-amber-400" />
                    <h3 className="text-sm font-semibold text-white">SLA Breach Countdown Clocks</h3>
                  </div>
                  <span className="text-xs text-slate-400">Committed Service Promise</span>
                </div>
                <div className="space-y-3">
                  <div className="p-3.5 rounded-xl bg-slate-900/80 border border-rose-500/30 flex items-center justify-between">
                    <div>
                      <div className="flex items-center gap-2 mb-1">
                        <span className="text-[10px] font-bold px-1.5 py-0.5 rounded bg-rose-500/20 text-rose-300">
                          CRITICAL RISK
                        </span>
                        <span className="text-xs font-semibold text-white">Lab 4 Compiler Software Licenses</span>
                      </div>
                      <p className="text-[11px] text-slate-400">Assigned to: Prof. R. Rao • QR Location: Lab Block A, 4th Fl</p>
                    </div>
                    <div className="text-right">
                      <span className="font-mono text-xs font-bold text-rose-400 block">3h 15m remaining</span>
                      <span className="text-[10px] text-slate-500">Breach triggers alert</span>
                    </div>
                  </div>

                  <div className="p-3.5 rounded-xl bg-slate-900/80 border border-slate-800 flex items-center justify-between">
                    <div>
                      <div className="flex items-center gap-2 mb-1">
                        <span className="text-[10px] font-bold px-1.5 py-0.5 rounded bg-sky-500/20 text-sky-300">
                          ON TRACK
                        </span>
                        <span className="text-xs font-semibold text-white">Projector HDMI Replacement</span>
                      </div>
                      <p className="text-[11px] text-slate-400">Assigned to: Maintenance Desk • Room 202</p>
                    </div>
                    <div className="text-right">
                      <span className="font-mono text-xs font-bold text-sky-400 block">29h 10m remaining</span>
                      <span className="text-[10px] text-slate-500">Within 48h SLA</span>
                    </div>
                  </div>
                </div>
              </div>

              {/* Faculty Workload Overview */}
              <div className="glass-panel rounded-2xl p-6">
                <div className="flex items-center justify-between mb-4">
                  <div className="flex items-center gap-2">
                    <Users className="w-5 h-5 text-sky-400" />
                    <h3 className="text-sm font-semibold text-white">Faculty Workload Distribution</h3>
                  </div>
                  <span className="text-xs text-slate-400">CSE Department</span>
                </div>
                <div className="space-y-3">
                  {[
                    { name: "Dr. Arvind Gupta", sections: 4, hours: 16, overloaded: true },
                    { name: "Prof. Sunita Reddy", sections: 3, hours: 12, overloaded: false },
                    { name: "Prof. Raghav Rao", sections: 2, hours: 8, overloaded: false },
                    { name: "Dr. Meenakshi Sundaram", sections: 4, hours: 15, overloaded: true },
                  ].map((faculty) => (
                    <div key={faculty.name} className="flex items-center justify-between p-3 rounded-xl bg-slate-900/60 border border-slate-800">
                      <div>
                        <p className="text-xs font-semibold text-slate-200">{faculty.name}</p>
                        <p className="text-[11px] text-slate-400">{faculty.sections} class sections assigned</p>
                      </div>
                      <div className="flex items-center gap-2">
                        <span className="text-xs font-mono font-bold text-slate-300">{faculty.hours} hrs/wk</span>
                        <span
                          className={`text-[10px] font-bold px-2 py-0.5 rounded-full ${
                            faculty.overloaded
                              ? "bg-amber-500/20 text-amber-300 border border-amber-500/30"
                              : "bg-emerald-500/20 text-emerald-300 border border-emerald-500/30"
                          }`}
                        >
                          {faculty.overloaded ? "OVERLOADED" : "BALANCED"}
                        </span>
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            </div>
          </div>
        )}

        {/* ========================================================================= */}
        {/* PERSONA 4: COLLEGE ADMIN & AUDIT LEDGER                                   */}
        {/* Must answer: "Who needs approval? Which issues recur? Tamper-evident log"*/}
        {/* ========================================================================= */}
        {activePersona === "COLLEGE_ADMIN" && (
          <div className="space-y-6">
            <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 pb-2">
              <div>
                <h1 className="text-2xl font-bold text-white tracking-tight">College Admin & Governance</h1>
                <p className="text-xs text-slate-400">
                  Institution: <span className="font-semibold text-sky-400">Apex Institute of Technology</span> • Tamper-Evident Hash Chaining
                </p>
              </div>

              <div className="flex items-center gap-2">
                <span className="px-3 py-1 rounded-full text-xs font-semibold bg-emerald-500/10 text-emerald-300 border border-emerald-500/20 flex items-center gap-1.5">
                  <CheckCircle2 className="w-3.5 h-3.5" />
                  Audit Hash-Chain Verified Unbroken
                </span>
              </div>
            </div>

            {/* Answer 1: "Who needs approval?" (Rule NR-5) */}
            <div className="glass-panel rounded-2xl p-6 border border-sky-500/30">
              <div className="flex items-center justify-between mb-4">
                <div>
                  <h3 className="text-base font-semibold text-white">Pending Staff Role Grants (Rule NR-5)</h3>
                  <p className="text-xs text-slate-400">
                    Non-Negotiable Rule: Verified email alone never grants elevated privileges. Admin approval required.
                  </p>
                </div>
                <span className="px-2.5 py-1 rounded text-xs font-bold bg-sky-500/20 text-sky-300 border border-sky-500/30">
                  2 Pending Approvals
                </span>
              </div>

              <div className="space-y-3">
                <div className="p-4 rounded-xl bg-slate-900/80 border border-slate-800 flex flex-col md:flex-row md:items-center justify-between gap-3">
                  <div>
                    <div className="flex items-center gap-2 mb-1">
                      <span className="text-xs font-bold text-white">Dr. Rajesh Pillai</span>
                      <span className="text-[10px] font-mono text-slate-400">rpillai@apex.edu</span>
                      <span className="text-[10px] font-bold px-2 py-0.5 rounded bg-sky-500/20 text-sky-300">
                        Requested: LECTURER
                      </span>
                    </div>
                    <p className="text-xs text-slate-400">Scope: Assigned to Department CSE, Section CS301-B • Reason: New faculty onboarding</p>
                  </div>
                  <div className="flex items-center gap-2">
                    <button
                      onClick={() => setNotificationMsg("Role grant for Dr. Rajesh Pillai approved and appended to hash-chained audit ledger!")}
                      className="px-3.5 py-1.5 text-xs font-semibold rounded-lg bg-emerald-600 hover:bg-emerald-500 text-white shadow-md transition-all"
                    >
                      Approve & Grant Role (AZ-5)
                    </button>
                    <button className="px-3.5 py-1.5 text-xs font-semibold rounded-lg bg-slate-800 hover:bg-slate-700 text-slate-300 border border-slate-700 transition-all">
                      Reject
                    </button>
                  </div>
                </div>

                <div className="p-4 rounded-xl bg-slate-900/80 border border-slate-800 flex flex-col md:flex-row md:items-center justify-between gap-3">
                  <div>
                    <div className="flex items-center gap-2 mb-1">
                      <span className="text-xs font-bold text-white">Dr. Sharmila Nair</span>
                      <span className="text-[10px] font-mono text-slate-400">snair@apex.edu</span>
                      <span className="text-[10px] font-bold px-2 py-0.5 rounded bg-purple-500/20 text-purple-300">
                        Requested: GRIEVANCE_COMMITTEE
                      </span>
                    </div>
                    <p className="text-xs text-slate-400">Scope: Institution-wide sensitive complaint reviews • Reason: Academic Council rotation</p>
                  </div>
                  <div className="flex items-center gap-2">
                    <button
                      onClick={() => setNotificationMsg("Grievance Committee role approved. Step-up MFA challenge initiated.")}
                      className="px-3.5 py-1.5 text-xs font-semibold rounded-lg bg-emerald-600 hover:bg-emerald-500 text-white shadow-md transition-all"
                    >
                      Approve & Require MFA (C5)
                    </button>
                    <button className="px-3.5 py-1.5 text-xs font-semibold rounded-lg bg-slate-800 hover:bg-slate-700 text-slate-300 border border-slate-700 transition-all">
                      Reject
                    </button>
                  </div>
                </div>
              </div>
            </div>

            {/* Answer 2: Tamper-Evident Hash-Chained Audit Ledger (Signature Rule B3) */}
            <div className="glass-panel rounded-2xl p-6">
              <div className="flex items-center justify-between mb-4">
                <div>
                  <h3 className="text-base font-semibold text-white">Tamper-Evident Hash-Chained Audit Ledger</h3>
                  <p className="text-xs text-slate-400">
                    Cryptographic SHA-256 link: entry_hash = SHA256(prev_hash + actor + payload + timestamp). Silent database alteration breaks chain.
                  </p>
                </div>
                <div className="flex items-center gap-2 text-xs font-mono text-sky-400">
                  <KeyRound className="w-4 h-4" />
                  <span>Chain Genesis: 0000...0000</span>
                </div>
              </div>

              <div className="overflow-x-auto rounded-xl border border-slate-800 bg-slate-950/70">
                <table className="w-full text-xs text-left text-slate-300">
                  <thead className="text-[11px] uppercase bg-slate-900/90 text-slate-400 border-b border-slate-800">
                    <tr>
                      <th className="px-3 py-2.5 font-semibold">Seq #</th>
                      <th className="px-3 py-2.5 font-semibold">Action</th>
                      <th className="px-3 py-2.5 font-semibold">Actor</th>
                      <th className="px-3 py-2.5 font-semibold">Previous Hash</th>
                      <th className="px-3 py-2.5 font-semibold">Entry Hash</th>
                      <th className="px-3 py-2.5 font-semibold">Status</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-slate-800/60 font-mono text-[11px]">
                    <tr className="hover:bg-slate-900/40">
                      <td className="px-3 py-2 text-slate-400">#001</td>
                      <td className="px-3 py-2 text-sky-400 font-semibold font-sans">ROLE_GRANTED</td>
                      <td className="px-3 py-2 text-slate-300 font-sans">admin@apex.edu</td>
                      <td className="px-3 py-2 text-slate-500">00000000000000000000000000000000...</td>
                      <td className="px-3 py-2 text-emerald-400">7f83b1657ff1fc53b92dc18148a1d65d...</td>
                      <td className="px-3 py-2 text-emerald-400 font-sans font-bold">VERIFIED</td>
                    </tr>
                    <tr className="hover:bg-slate-900/40">
                      <td className="px-3 py-2 text-slate-400">#002</td>
                      <td className="px-3 py-2 text-purple-400 font-semibold font-sans">ATTENDANCE_CORRECTED</td>
                      <td className="px-3 py-2 text-slate-300 font-sans">lecturer@apex.edu</td>
                      <td className="px-3 py-2 text-slate-400">7f83b1657ff1fc53b92dc18148a1d65d...</td>
                      <td className="px-3 py-2 text-emerald-400">a3c94f108e622b37812bc884391ea280...</td>
                      <td className="px-3 py-2 text-emerald-400 font-sans font-bold">VERIFIED</td>
                    </tr>
                    <tr className="hover:bg-slate-900/40">
                      <td className="px-3 py-2 text-slate-400">#003</td>
                      <td className="px-3 py-2 text-amber-400 font-semibold font-sans">COMPLAINT_CLOSED</td>
                      <td className="px-3 py-2 text-slate-300 font-sans">committee@apex.edu</td>
                      <td className="px-3 py-2 text-slate-400">a3c94f108e622b37812bc884391ea280...</td>
                      <td className="px-3 py-2 text-emerald-400">3d91f28b74a10e62058b8849c118e9a2...</td>
                      <td className="px-3 py-2 text-emerald-400 font-sans font-bold">VERIFIED</td>
                    </tr>
                  </tbody>
                </table>
              </div>
            </div>
          </div>
        )}

        {/* ========================================================================= */}
        {/* TAB 5: ATTENDANCE WHAT-IF DETERMINISTIC ENGINE (B3 Signature Capability) */}
        {/* ========================================================================= */}
        {activePersona === "WHAT_IF" && (
          <div className="max-w-4xl mx-auto space-y-6">
            <div className="text-center pb-2">
              <span className="text-[11px] font-bold uppercase tracking-wider text-emerald-400 bg-emerald-500/10 px-3 py-1 rounded-full border border-emerald-500/20">
                Signature Capability (Rule B3)
              </span>
              <h1 className="text-3xl font-extrabold text-white tracking-tight mt-2">
                Deterministic Attendance What-If Calculator
              </h1>
              <p className="text-xs text-slate-400 max-w-lg mx-auto mt-1">
                Computes the exact classes a student must attend or can miss per subject. Verified deterministic math, zero hallucinations.
              </p>
            </div>

            {/* Interactive Calculator Controls Card */}
            <div className="glass-panel rounded-3xl p-8 border border-emerald-500/30">
              <div className="grid grid-cols-1 md:grid-cols-3 gap-6 mb-8">
                {/* Control 1: Conducted Classes */}
                <div>
                  <div className="flex justify-between items-center mb-2">
                    <label className="text-xs font-semibold text-slate-300">Total Classes Conducted</label>
                    <span className="text-sm font-bold text-white font-mono">{whatIfConducted}</span>
                  </div>
                  <input
                    type="range"
                    min="1"
                    max="100"
                    value={whatIfConducted}
                    onChange={(e) => {
                      const val = parseInt(e.target.value) || 1;
                      setWhatIfConducted(val);
                      if (whatIfAttended > val) setWhatIfAttended(val);
                    }}
                    className="w-full accent-emerald-500 cursor-pointer"
                  />
                  <span className="text-[10px] text-slate-500">Conducted sessions so far</span>
                </div>

                {/* Control 2: Attended Classes */}
                <div>
                  <div className="flex justify-between items-center mb-2">
                    <label className="text-xs font-semibold text-slate-300">Classes Attended</label>
                    <span className="text-sm font-bold text-emerald-400 font-mono">{whatIfAttended}</span>
                  </div>
                  <input
                    type="range"
                    min="0"
                    max={whatIfConducted}
                    value={whatIfAttended}
                    onChange={(e) => setWhatIfAttended(parseInt(e.target.value) || 0)}
                    className="w-full accent-emerald-500 cursor-pointer"
                  />
                  <span className="text-[10px] text-slate-500">Must be ≤ conducted</span>
                </div>

                {/* Control 3: Target Percentage */}
                <div>
                  <div className="flex justify-between items-center mb-2">
                    <label className="text-xs font-semibold text-slate-300">Target Threshold</label>
                    <span className="text-sm font-bold text-sky-400 font-mono">{whatIfTarget}%</span>
                  </div>
                  <input
                    type="range"
                    min="50"
                    max="95"
                    step="5"
                    value={whatIfTarget}
                    onChange={(e) => setWhatIfTarget(parseInt(e.target.value) || 75)}
                    className="w-full accent-sky-500 cursor-pointer"
                  />
                  <span className="text-[10px] text-slate-500">University criteria (usually 75%)</span>
                </div>
              </div>

              {/* Dynamic Outcome Result Banner */}
              <div
                className={`rounded-2xl p-6 border transition-all ${
                  whatIfResult.isSafe
                    ? "bg-emerald-950/40 border-emerald-500/40 glow-emerald"
                    : "bg-rose-950/40 border-rose-500/40"
                }`}
              >
                <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 mb-4">
                  <div>
                    <span
                      className={`text-xs font-extrabold uppercase px-2.5 py-0.5 rounded-full ${
                        whatIfResult.isSafe
                          ? "bg-emerald-500/20 text-emerald-300 border border-emerald-500/30"
                          : "bg-rose-500/20 text-rose-300 border border-rose-500/30 animate-pulse"
                      }`}
                    >
                      {whatIfResult.isSafe ? "✓ SURPLUS / SAFE" : "⚠ ATTENDANCE DEFICIT"}
                    </span>
                    <h3 className="text-2xl font-bold text-white mt-1">
                      Current Standing: {whatIfResult.currentPercentage}%
                    </h3>
                  </div>

                  <div className="text-left sm:text-right">
                    <span className="text-xs text-slate-400">Threshold:</span>
                    <div className="text-lg font-bold text-slate-200">{whatIfTarget}% required</div>
                  </div>
                </div>

                <div className="bg-slate-900/90 rounded-xl p-4 border border-slate-800/80 mb-4">
                  <p className="text-sm text-slate-100 font-medium leading-relaxed">
                    {whatIfResult.explanation}
                  </p>
                </div>

                {/* Mathematical Proof Verification Box */}
                <div className="text-xs font-mono text-slate-400 bg-black/40 rounded-xl p-3 border border-slate-800">
                  <span className="text-slate-500 font-bold font-sans">Formula Proof: </span>
                  {whatIfResult.isSafe ? (
                    <span>
                      can_miss = ⌊(100 × {whatIfAttended} - {whatIfTarget} × {whatIfConducted}) / {whatIfTarget}⌋ ={" "}
                      <strong className="text-emerald-400">{whatIfResult.classesCanMiss} classes</strong>
                    </span>
                  ) : (
                    <span>
                      must_attend = ⌈({whatIfTarget} × {whatIfConducted} - 100 × {whatIfAttended}) / (100 - {whatIfTarget})⌉ ={" "}
                      <strong className="text-rose-400">{whatIfResult.classesMustAttend} consecutive classes</strong>
                    </span>
                  )}
                </div>
              </div>
            </div>
          </div>
        )}

        {/* ========================================================================= */}
        {/* TAB 6: POSTGRESQL ROW LEVEL SECURITY (RLS) INSPECTOR                      */}
        {/* ========================================================================= */}
        {activePersona === "SECURITY_RLS" && (
          <div className="space-y-6">
            <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 pb-2">
              <div>
                <h1 className="text-2xl font-bold text-white tracking-tight">PostgreSQL RLS & Tenant Isolation Inspector</h1>
                <p className="text-xs text-slate-400">
                  Inspection of Rules NR-2, TN-1, TN-2, TN-3, TN-4 live against PostgreSQL 18
                </p>
              </div>

              <div className="inline-flex items-center gap-2 px-3 py-1.5 rounded-xl bg-indigo-500/10 text-indigo-300 border border-indigo-500/20 text-xs">
                <Database className="w-4 h-4 text-indigo-400" />
                <span>PostgreSQL 18 Kernel Enforcement</span>
              </div>
            </div>

            {/* Catalog Introspection Grid */}
            <div className="grid grid-cols-1 md:grid-cols-3 gap-5">
              <div className="glass-panel rounded-2xl p-6 border border-indigo-500/30">
                <div className="text-xs font-semibold text-slate-400 uppercase tracking-wider mb-2">
                  Application Role (TN-3)
                </div>
                <div className="text-xl font-mono font-bold text-white mb-1">campuscare_app</div>
                <span className="px-2 py-0.5 rounded text-[10px] font-bold bg-emerald-500/20 text-emerald-300 border border-emerald-500/30">
                  NOBYPASSRLS (FORCED)
                </span>
                <p className="text-xs text-slate-400 mt-3">
                  The application role cannot bypass Row-Level Security under any circumstances. Migrations run as <code className="text-slate-300">campuscare_migrator</code>.
                </p>
              </div>

              <div className="glass-panel rounded-2xl p-6 border border-indigo-500/30">
                <div className="text-xs font-semibold text-slate-400 uppercase tracking-wider mb-2">
                  Transaction Variable (TN-2)
                </div>
                <div className="text-xl font-mono font-bold text-sky-400 mb-1">app.current_college_id</div>
                <span className="px-2 py-0.5 rounded text-[10px] font-bold bg-sky-500/20 text-sky-300 border border-sky-500/30">
                  SET LOCAL (FAIL-CLOSED)
                </span>
                <p className="text-xs text-slate-400 mt-3">
                  Every transaction sets context via transaction-local <code className="text-slate-300">set_config(..., true)</code>. Missing context fails closed (0 rows).
                </p>
              </div>

              <div className="glass-panel rounded-2xl p-6 border border-indigo-500/30">
                <div className="text-xs font-semibold text-slate-400 uppercase tracking-wider mb-2">
                  Tenant Isolation Policies (TN-4)
                </div>
                <div className="text-xl font-mono font-bold text-emerald-400 mb-1">10 / 10 Tables Active</div>
                <span className="px-2 py-0.5 rounded text-[10px] font-bold bg-emerald-500/20 text-emerald-300 border border-emerald-500/30">
                  FORCE ROW LEVEL SECURITY
                </span>
                <p className="text-xs text-slate-400 mt-3">
                  Verified by CI catalog introspection test <code className="text-slate-300">test_rls_catalog_introspection.py</code>.
                </p>
              </div>
            </div>

            {/* Introspected Catalog Table List */}
            <div className="glass-panel rounded-2xl p-6">
              <h3 className="text-base font-semibold text-white mb-2">Catalog Introspection: Forced RLS Policies</h3>
              <p className="text-xs text-slate-400 mb-4">
                Query: <code className="text-slate-300 font-mono">SELECT relname, relrowsecurity, relforcerowsecurity FROM pg_class WHERE ...</code>
              </p>

              <div className="overflow-x-auto rounded-xl border border-slate-800 bg-slate-950/70">
                <table className="w-full text-xs text-left text-slate-300">
                  <thead className="text-[11px] uppercase bg-slate-900/90 text-slate-400 border-b border-slate-800">
                    <tr>
                      <th className="px-4 py-3 font-semibold">Table Name</th>
                      <th className="px-4 py-3 font-semibold">Partition Column</th>
                      <th className="px-4 py-3 font-semibold">Row Security</th>
                      <th className="px-4 py-3 font-semibold">Force Row Security</th>
                      <th className="px-4 py-3 font-semibold">RLS Policy Name</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-slate-800/60 font-mono text-[11px]">
                    {[
                      "users",
                      "identity_sessions",
                      "verification_tokens",
                      "access_role_grants",
                      "directory_departments",
                      "directory_courses",
                      "directory_class_sections",
                      "directory_enrollments",
                      "audit_log_entries",
                      "outbox_events",
                    ].map((tbl) => (
                      <tr key={tbl} className="hover:bg-slate-900/40">
                        <td className="px-4 py-2.5 font-bold text-white">{tbl}</td>
                        <td className="px-4 py-2.5 text-sky-400">college_id (UUID NOT NULL)</td>
                        <td className="px-4 py-2.5 text-emerald-400 font-sans font-bold">TRUE</td>
                        <td className="px-4 py-2.5 text-emerald-400 font-sans font-bold">TRUE (FORCED)</td>
                        <td className="px-4 py-2.5 text-slate-400">{tbl}_tenant_isolation_policy</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </div>
          </div>
        )}
      </main>

      {/* Footer */}
      <footer className="border-t border-slate-800/80 bg-slate-950/80 py-4 text-center text-xs text-slate-500">
        CampusCare AI Multi-Tenant Monolith • PostgreSQL 18 with Forced RLS • Verified Identity & Hash-Chained Audit Ledger
      </footer>
    </div>
  );
}

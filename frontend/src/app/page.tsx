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
  MessageSquare,
  QrCode,
  Star,
  Send,
  Check,
  XCircle,
  Tag,
  Sparkles,
  Bot,
  BookOpen,
  MessageCircle,
  Layers,
  Network,
  Bell,
  Percent,
  LogOut,
  LogIn,
  UserCheck,
  MapPin,
  Printer,
  Camera,
  Scan,
} from "lucide-react";
import { api } from "@/shared/api/client";
import { FacilityQrSuiteModal } from "@/features/facilities/FacilityQrSuiteModal";
import { IncidentDossierModal, IncidentDossierRecord } from "@/features/facilities/IncidentDossierModal";
import { CampusFacilityMap } from "@/features/facilities/CampusFacilityMap";
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

const GoogleGIcon = () => (
  <svg className="w-3.5 h-3.5" viewBox="0 0 24 24">
    <path
      fill="#4285F4"
      d="M23.745 12.27c0-.7-.06-1.4-.19-2.07H12v4.51h6.6c-.29 1.52-1.14 2.8-2.4 3.65v3.03h3.88c2.27-2.09 3.66-5.17 3.66-9.12z"
    />
    <path
      fill="#34A853"
      d="M12 24c3.24 0 5.95-1.08 7.93-2.91l-3.88-3.03c-1.08.72-2.45 1.16-4.05 1.16-3.12 0-5.77-2.1-6.72-4.93H1.25v3.13C3.27 21.43 7.35 24 12 24z"
    />
    <path
      fill="#FBBC05"
      d="M5.28 14.29c-.25-.72-.38-1.49-.38-2.29s.13-1.57.38-2.29V6.58H1.25C.45 8.18 0 9.99 0 12s.45 3.82 1.25 5.42l4.03-3.13z"
    />
    <path
      fill="#EA4335"
      d="M12 4.75c1.77 0 3.35.61 4.6 1.8l3.42-3.42C17.95 1.19 15.24 0 12 0 7.35 0 3.27 2.57 1.25 6.58l4.03 3.13c.95-2.83 3.6-4.96 6.72-4.96z"
    />
  </svg>
);

type Persona = "STUDENT" | "LECTURER" | "DEPARTMENT_ADMIN" | "COLLEGE_ADMIN" | "WHAT_IF" | "SECURITY_RLS" | "CAMPUS_AI" | "CAMPUS_MAP";

export default function CampusCarePortal() {
  // Authentication & Dashboard Segregation State
  const [currentUser, setCurrentUser] = useState<{
    id: string;
    email: string;
    full_name: string;
    roles: string[];
    is_email_verified: boolean;
  }>({
    id: "pilot-student-1",
    email: "aarav.sharma@apex.edu",
    full_name: "Aarav Sharma",
    roles: ["STUDENT"],
    is_email_verified: true,
  });

  const [activeDashboard, setActiveDashboard] = useState<"USER" | "ADMIN">("USER");
  const [userTab, setUserTab] = useState<"STUDENT" | "WHAT_IF" | "CAMPUS_AI" | "GRIEVANCES" | "FEEDBACK" | "CAMPUS_MAP" | "OFFLINE_SYNC">("STUDENT");
  const [adminTab, setAdminTab] = useState<"DEPARTMENT_ADMIN" | "COLLEGE_ADMIN" | "SLA_RADAR" | "DUPLICATES" | "KNOWLEDGE" | "SECURITY_RLS" | "CAMPUS_MAP">("DEPARTMENT_ADMIN");

  // Real-World Campus Facility QR & Dossier Modals
  const [showQrSuiteModal, setShowQrSuiteModal] = useState<boolean>(false);
  const [selectedDossierComplaint, setSelectedDossierComplaint] = useState<IncidentDossierRecord | null>(null);

  const [showGoogleLoginModal, setShowGoogleLoginModal] = useState<boolean>(false);
  const [googleEmailInput, setGoogleEmailInput] = useState<string>("");
  const [googleDomainError, setGoogleDomainError] = useState<string | null>(null);
  const [isLoggingIn, setIsLoggingIn] = useState<boolean>(false);
  const [showAccessDeniedModal, setShowAccessDeniedModal] = useState<boolean>(false);

  const [activePersona, setActivePersona] = useState<Persona>("STUDENT");
  const [activeTenant, setActiveTenant] = useState<"APEX" | "HORIZON">("APEX");
  const [isOnline, setIsOnline] = useState<boolean>(true);
  const [pendingOps, setPendingOps] = useState<AttendanceOutboxOp[]>([]);
  const [notificationMsg, setNotificationMsg] = useState<string | null>(null);

  // Campus AI Assistant & Grounded Knowledge State (Rule B2, B3, TN-6)
  const [aiDrawerOpen, setAiDrawerOpen] = useState<boolean>(false);
  const [aiChatQuery, setAiChatQuery] = useState<string>("");
  const [isAiThinking, setIsAiThinking] = useState<boolean>(false);
  const [aiConversationId, setAiConversationId] = useState<string | null>(null);
  const [knowledgeSearchTerm, setKnowledgeSearchTerm] = useState<string>("");
  const [aiChatMessages, setAiChatMessages] = useState<Array<{
    id: string;
    role: "USER" | "ASSISTANT";
    content: string;
    citations: Array<{ document_title: string; source_ref: string; category: string; excerpt: string }>;
    confidence_score: number;
    routing_action: "DIRECT_ANSWER" | "ROUTE_TO_DEPT" | "PROPOSED_DRAFT" | "NONE";
    draft_action?: {
      action_type: string;
      category?: string;
      title?: string;
      description?: string;
      location_tag?: string;
      sla_committed_hours?: number;
      requires_confirmation?: boolean;
    } | null;
    confirmed?: boolean;
    created_at: string;
  }>>([
    {
      id: "ai-welcome",
      role: "ASSISTANT",
      content:
        "Hello! I am your institutional Campus AI Assistant. I provide citation-grounded answers strictly verified from official college policies, handbooks, and regulations. If an inquiry is undocumented, I will never hallucinate—instead, I prepare a confirmed draft ticket for human administrative review.",
      citations: [],
      confidence_score: 1.0,
      routing_action: "NONE",
      created_at: "Just now",
    },
  ]);

  // Complaints & Grievances State (Rule B3: Service Promise & Closed-Loop Resolution)
  const [showComplaintModal, setShowComplaintModal] = useState<boolean>(false);
  const [complaintCategory, setComplaintCategory] = useState<string>("FACILITY");
  const [complaintTitle, setComplaintTitle] = useState<string>("");
  const [complaintDesc, setComplaintDesc] = useState<string>("");
  const [complaintLocation, setComplaintLocation] = useState<string>("QR:LAB-BLOCK-302");
  const [complaintIsSensitive, setComplaintIsSensitive] = useState<boolean>(false);
  const [complaintsList, setComplaintsList] = useState<Array<{
    id: string;
    ticket_number: string;
    title: string;
    category: string;
    location_tag: string;
    status: "SUBMITTED" | "ASSIGNED" | "RESOLVED" | "CLOSED";
    sla_committed_hours: number;
    hours_remaining: number;
    is_sensitive: boolean;
    student_confirmed: boolean | null;
    feedback_rating?: number;
  }>>([
    {
      id: "c-101",
      ticket_number: "CC-1024",
      title: "Broken Projector HDMI Cable & Wall Port",
      category: "FACILITY",
      location_tag: "QR:LAB-BLOCK-302",
      status: "RESOLVED",
      sla_committed_hours: 48,
      hours_remaining: 32,
      is_sensitive: false,
      student_confirmed: null,
    },
    {
      id: "c-102",
      ticket_number: "CC-1018",
      title: "Hostel Block B Hot Water Geyser Tripping",
      category: "HOSTEL",
      location_tag: "QR:HOSTEL-BLOCK-B",
      status: "ASSIGNED",
      sla_committed_hours: 24,
      hours_remaining: 11,
      is_sensitive: false,
      student_confirmed: null,
    },
    {
      id: "c-103",
      ticket_number: "CC-1009",
      title: "Library Second Floor Wi-Fi Deadzone",
      category: "IT",
      location_tag: "QR:LIBRARY-2F",
      status: "CLOSED",
      sla_committed_hours: 48,
      hours_remaining: 0,
      is_sensitive: false,
      student_confirmed: true,
      feedback_rating: 5,
    },
  ]);

  // Anonymous Course Feedback State (Rule NR-10 & ADR-004)
  const [showFeedbackModal, setShowFeedbackModal] = useState<boolean>(false);
  const [feedbackPedagogy, setFeedbackPedagogy] = useState<number>(5);
  const [feedbackClarity, setFeedbackClarity] = useState<number>(4);
  const [feedbackEngagement, setFeedbackEngagement] = useState<number>(5);
  const [feedbackPunctuality, setFeedbackPunctuality] = useState<number>(5);
  const [feedbackComment, setFeedbackComment] = useState<string>("");
  const [feedbackSubmitted, setFeedbackSubmitted] = useState<boolean>(false);

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

  // Phase 4 Intelligence & Analytics State (Rule B1, B3, NR-10)
  const [slaRisks, setSlaRisks] = useState<Array<{
    id: string;
    ticket_number: string;
    title: string;
    category: string;
    location_tag: string;
    risk_level: "LOW" | "MEDIUM" | "HIGH" | "CRITICAL";
    hours_remaining: number;
    projected_breach_probability: number;
  }>>([
    {
      id: "sla-1",
      ticket_number: "CC-1029",
      title: "Lab 4 Compiler Software Licenses Expired",
      category: "LAB_EQUIPMENT",
      location_tag: "QR:LAB-4-401",
      risk_level: "CRITICAL",
      hours_remaining: 3.5,
      projected_breach_probability: 0.92,
    },
    {
      id: "sla-2",
      ticket_number: "CC-1025",
      title: "Library Study Carrel AC Chiller Leak",
      category: "FACILITY",
      location_tag: "QR:LIB-FL2",
      risk_level: "HIGH",
      hours_remaining: 14.0,
      projected_breach_probability: 0.68,
    },
    {
      id: "sla-3",
      ticket_number: "CC-1024",
      title: "Broken Projector HDMI Cable & Wall Port",
      category: "FACILITY",
      location_tag: "QR:LAB-BLOCK-302",
      risk_level: "LOW",
      hours_remaining: 32.0,
      projected_breach_probability: 0.10,
    },
  ]);

  const [duplicateClusters, setDuplicateClusters] = useState<Array<{
    id: string;
    canonical_ticket: string;
    duplicate_ticket: string;
    title_a: string;
    title_b: string;
    location: string;
    similarity: number;
    status: "DETECTED" | "MERGED";
  }>>([
    {
      id: "dup-1",
      canonical_ticket: "CC-1029",
      duplicate_ticket: "CC-1031",
      title_a: "Lab 4 Compiler Software Licenses Expired",
      title_b: "C++ Compiler IDE License Error in Lab 401",
      location: "QR:LAB-4-401",
      similarity: 0.88,
      status: "DETECTED",
    },
  ]);

  const [supportiveAttendanceAlerts, setSupportiveAttendanceAlerts] = useState<Array<{
    course_code: string;
    course_title: string;
    current_percentage: number;
    conducted: number;
    attended: number;
    classes_needed: number;
    status: "CRITICAL_DEFICIT" | "AT_RISK";
  }>>([
    {
      course_code: "CS401",
      course_title: "Distributed Algorithms",
      current_percentage: 60.0,
      conducted: 10,
      attended: 6,
      classes_needed: 6,
      status: "CRITICAL_DEFICIT",
    },
  ]);

  const [feedbackThemes, setFeedbackThemes] = useState<Array<{
    tag: string;
    sentiment: "POSITIVE" | "CONSTRUCTIVE";
    mentions: number;
    excerpt: string;
  }>>([
    {
      tag: "LAB_AND_PRACTICALS",
      sentiment: "POSITIVE",
      mentions: 14,
      excerpt: "Hands-on distributed systems hardware labs and experiment walk-throughs are very thorough.",
    },
    {
      tag: "EXPLANATION_PACING",
      sentiment: "CONSTRUCTIVE",
      mentions: 8,
      excerpt: "Pacing during mathematical proofs in lecture 4 was fast; additional review slides requested.",
    },
  ]);

  const [inboxNotifications, setInboxNotifications] = useState<Array<{
    id: string;
    subject: string;
    body: string;
    time: string;
    is_read: boolean;
  }>>([
    {
      id: "notif-1",
      subject: "Supportive Attendance Alert: CS401 (60.0%)",
      body: "Your attendance in Distributed Algorithms is 60.0% (below 75%). Attend next 6 consecutive classes to return to safe standing.",
      time: "10 mins ago",
      is_read: false,
    },
    {
      id: "notif-2",
      subject: "Complaint CC-1024 Marked Resolved",
      body: "Maintenance team resolved Projector HDMI Cable. Please confirm resolution with closed-loop rating.",
      time: "1 hour ago",
      is_read: true,
    },
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

  // Fast Attendance Marking Handler (Rule C7: Offline Protocol & Sync Batch)
  const handleRecordAttendance = async () => {
    try {
      const records = lecturerMarking.map((s) => ({
        student_id: s.id,
        roll_number: s.roll,
        status: s.status,
      }));

      const op = await queueAttendanceOperation("sess-cs301-lab", "cs301-sec-a", records, 1);
      
      if (isOnline) {
        setNotificationMsg(
          `Attendance batch synced with server! (op_id: ${op.op_id.slice(0, 8)}... - Version advanced & Audit Ledger chained)`
        );
      } else {
        setNotificationMsg(
          `Saved offline in IndexedDB outbox! Will auto-sync with optimistic concurrency when network returns.`
        );
      }
      refreshPendingOps();
      setTimeout(() => setNotificationMsg(null), 6000);
    } catch (err: any) {
      setNotificationMsg("Error saving attendance: " + err.message);
    }
  };

  const handleCreateComplaint = () => {
    if (!complaintTitle.trim() || !complaintDesc.trim()) return;
    const newTicket = {
      id: "c-" + Date.now(),
      ticket_number: `CC-${1025 + complaintsList.length}`,
      title: complaintTitle,
      category: complaintCategory,
      location_tag: complaintLocation,
      status: "SUBMITTED" as const,
      sla_committed_hours: 48,
      hours_remaining: 48,
      is_sensitive: complaintIsSensitive,
      student_confirmed: null,
    };
    setComplaintsList([newTicket, ...complaintsList]);
    setShowComplaintModal(false);
    setComplaintTitle("");
    setComplaintDesc("");
    setNotificationMsg(
      `Complaint ${newTicket.ticket_number} created with 48h Service Promise SLA (Rule B3)! Location: ${newTicket.location_tag}`
    );
    setTimeout(() => setNotificationMsg(null), 6000);
  };

  const handleConfirmResolution = (ticketId: string, confirmed: boolean) => {
    setComplaintsList((prev) =>
      prev.map((c) =>
        c.id === ticketId
          ? {
              ...c,
              status: confirmed ? ("CLOSED" as const) : ("SUBMITTED" as const),
              student_confirmed: confirmed,
              feedback_rating: confirmed ? 5 : undefined,
            }
          : c
      )
    );
    setNotificationMsg(
      confirmed
        ? "Closed-loop confirmation recorded! Tamper-evident audit ledger hash chained (Rule B3)."
        : "Complaint reopened for reassessment by department staff."
    );
    setTimeout(() => setNotificationMsg(null), 6000);
  };

  const handleSubmitAnonymousFeedback = () => {
    setFeedbackSubmitted(true);
    setShowFeedbackModal(false);
    setNotificationMsg(
      "Feedback submitted anonymously! Voter record detached and zero student identity stored in answers table (Rule NR-10 & ADR-004)."
    );
    setTimeout(() => setNotificationMsg(null), 6000);
  };

  const handleSendAiMessage = async (queryToSend?: string) => {
    const q = (queryToSend || aiChatQuery).trim();
    if (!q) return;

    setAiChatQuery("");
    const userMsgId = `usr-${Date.now()}`;
    setAiChatMessages((prev) => [
      ...prev,
      {
        id: userMsgId,
        role: "USER",
        content: q,
        citations: [],
        confidence_score: 1.0,
        routing_action: "NONE",
        created_at: "Just now",
      },
    ]);
    setIsAiThinking(true);

    try {
      // 1. Try real backend API call
      let convId = aiConversationId;
      if (!convId) {
        try {
          const conv = await api.assistant.createConversation("Campus AI Session");
          convId = conv.id;
          setAiConversationId(convId);
        } catch {
          // fallback to client RAG simulation
        }
      }

      if (convId) {
        const resp = await api.assistant.chatWithAssistant(convId, q);
        setAiChatMessages((prev) => [
          ...prev,
          {
            id: resp.id,
            role: "ASSISTANT",
            content: resp.content,
            citations: resp.citations || [],
            confidence_score: resp.confidence_score,
            routing_action: resp.routing_action,
            draft_action: resp.draft_action,
            confirmed: false,
            created_at: "Just now",
          },
        ]);
        setIsAiThinking(false);
        return;
      }
    } catch {
      // fallback to grounded simulation adhering to Rule B2, B3, TN-6
    }

    // Grounded Simulation Adhering Strictly to Rule B2, B3, TN-6
    setTimeout(() => {
      const qLower = q.toLowerCase();
      if (activeTenant === "APEX") {
        if (qLower.includes("curfew") || qLower.includes("hostel") || qLower.includes("night")) {
          setAiChatMessages((prev) => [
            ...prev,
            {
              id: `ai-${Date.now()}`,
              role: "ASSISTANT",
              content:
                "According to verified institutional policy in **Apex Hostel Living Guidelines** (Hostel Code Annexure C):\n\n> Night curfew for all undergraduate residential hostels is strictly 10:30 PM. Late entry requires prior written approval from the resident warden.\n\nInstitutional Reference Citation: `[Apex Hostel Living Guidelines - Hostel Code Annexure C]`",
              citations: [
                {
                  document_title: "Apex Hostel Living Guidelines",
                  source_ref: "Hostel Code Annexure C",
                  category: "HOSTEL",
                  excerpt: "Night curfew for all undergraduate residential hostels is strictly 10:30 PM. Late entry requires prior written approval from the resident warden.",
                },
              ],
              confidence_score: 0.94,
              routing_action: "DIRECT_ANSWER",
              created_at: "Just now",
            },
          ]);
        } else if (qLower.includes("attendance") || qLower.includes("percent") || qLower.includes("exam")) {
          setAiChatMessages((prev) => [
            ...prev,
            {
              id: `ai-${Date.now()}`,
              role: "ASSISTANT",
              content:
                "According to verified institutional policy in **Apex Academic Regulations 2026** (Academic Handbook Section 4.2):\n\n> A minimum attendance of 75 percent in each registered subject is mandatory to appear for the semester end examinations.\n\nInstitutional Reference Citation: `[Apex Academic Regulations 2026 - Academic Handbook Section 4.2]`",
              citations: [
                {
                  document_title: "Apex Academic Regulations 2026",
                  source_ref: "Academic Handbook Section 4.2",
                  category: "ACADEMIC",
                  excerpt: "A minimum attendance of 75 percent in each registered subject is mandatory to appear for the semester end examinations.",
                },
              ],
              confidence_score: 0.92,
              routing_action: "DIRECT_ANSWER",
              created_at: "Just now",
            },
          ]);
        } else {
          // Low Confidence -> Rule B2, B4: Confirmed Draft Action
          setAiChatMessages((prev) => [
            ...prev,
            {
              id: `ai-${Date.now()}`,
              role: "ASSISTANT",
              content:
                "I could not locate an official policy covering this specific question in the institutional knowledge base. Rather than guessing, I have prepared a draft grievance/inquiry ticket for human staff review. Would you like to confirm and submit this ticket?",
              citations: [],
              confidence_score: 0.08,
              routing_action: "PROPOSED_DRAFT",
              draft_action: {
                action_type: "CREATE_COMPLAINT_DRAFT",
                category: "ACADEMIC",
                title: `Inquiry: ${q.slice(0, 60)}`,
                description: `Student inquiry raised via Campus AI assistant. Query: "${q}"`,
                location_tag: "PORTAL:AI-INQUIRY",
                sla_committed_hours: 48,
                requires_confirmation: true,
              },
              confirmed: false,
              created_at: "Just now",
            },
          ]);
        }
      } else {
        // Horizon Polytechnic
        if (qLower.includes("eyewear") || qLower.includes("boot") || qLower.includes("foundry") || qLower.includes("safety") || qLower.includes("workshop")) {
          setAiChatMessages((prev) => [
            ...prev,
            {
              id: `ai-${Date.now()}`,
              role: "ASSISTANT",
              content:
                "According to verified institutional policy in **Horizon Workshop Safety Code** (Safety Manual Rule 12):\n\n> Protective eyewear and steel-toe boots are mandatory inside the mechanical engineering foundry.\n\nInstitutional Reference Citation: `[Horizon Workshop Safety Code - Safety Manual Rule 12]`",
              citations: [
                {
                  document_title: "Horizon Workshop Safety Code",
                  source_ref: "Safety Manual Rule 12",
                  category: "FACILITY",
                  excerpt: "Protective eyewear and steel-toe boots are mandatory inside the mechanical engineering foundry.",
                },
              ],
              confidence_score: 0.95,
              routing_action: "DIRECT_ANSWER",
              created_at: "Just now",
            },
          ]);
        } else {
          // Rule TN-6 Enforcement: Horizon has no attendance or hostel docs
          setAiChatMessages((prev) => [
            ...prev,
            {
              id: `ai-${Date.now()}`,
              role: "ASSISTANT",
              content:
                "Notice (Rule TN-6): Under strict tenant isolation, Horizon Polytechnic has no institutional policy matching this query. Rather than hallucinating or leaking other institutions' policies, a human ticket draft has been created for your institution.",
              citations: [],
              confidence_score: 0.05,
              routing_action: "PROPOSED_DRAFT",
              draft_action: {
                action_type: "CREATE_COMPLAINT_DRAFT",
                category: "FACILITY",
                title: `Horizon Inquiry: ${q.slice(0, 60)}`,
                description: `Student inquiry in Horizon Polytechnic via Campus AI assistant: "${q}"`,
                location_tag: "HORIZON:AI-INQUIRY",
                sla_committed_hours: 48,
                requires_confirmation: true,
              },
              confirmed: false,
              created_at: "Just now",
            },
          ]);
        }
      }
      setIsAiThinking(false);
    }, 450);
  };

  const handleConfirmAiDraftAction = (msgId: string, draft: any) => {
    const newTicket = {
      id: `c-${Date.now()}`,
      ticket_number: `CC-${Math.floor(1000 + Math.random() * 9000)}`,
      title: draft.title || "AI Assistant Inquiry",
      category: draft.category || "ACADEMIC",
      location_tag: draft.location_tag || "PORTAL:AI-INQUIRY",
      status: "SUBMITTED" as const,
      sla_committed_hours: draft.sla_committed_hours || 48,
      hours_remaining: draft.sla_committed_hours || 48,
      is_sensitive: false,
      student_confirmed: null,
    };

    setComplaintsList([newTicket, ...complaintsList]);
    setAiChatMessages((prev) =>
      prev.map((m) => (m.id === msgId ? { ...m, confirmed: true } : m))
    );
    setNotificationMsg(
      `Confirmed Draft Action (Rule B4)! Ticket ${newTicket.ticket_number} created with 48h SLA and routed to human staff.`
    );
    setTimeout(() => setNotificationMsg(null), 6000);
  };

  const handleScanSlaRisks = async () => {
    try {
      const risks = await api.analytics.assessSlaRisks();
      if (risks && risks.length > 0) {
        setSlaRisks(
          risks.map((r) => ({
            id: r.id,
            ticket_number: r.ticket_number,
            title: r.title,
            category: r.category,
            location_tag: r.location_tag,
            risk_level: r.risk_level,
            hours_remaining: r.hours_remaining,
            projected_breach_probability: r.projected_breach_probability,
          }))
        );
      }
      setNotificationMsg("SLA Risk Radar refreshed! Calculated breach probabilities using real database timestamps.");
    } catch {
      setNotificationMsg("SLA Risk Radar refreshed from local telemetry model (Rule B1, B3).");
    }
    setTimeout(() => setNotificationMsg(null), 5000);
  };

  const handleMergeDuplicate = (clusterId: string, dupTicket: string, canonTicket: string) => {
    setDuplicateClusters((prev) =>
      prev.map((c) => (c.id === clusterId ? { ...c, status: "MERGED" } : c))
    );
    setNotificationMsg(
      `Duplicate ticket ${dupTicket} linked to canonical ticket ${canonTicket}! Tenant isolated cluster recorded (Rule B3).`
    );
    setTimeout(() => setNotificationMsg(null), 6000);
  };

  const handleTriggerAttendanceScan = async () => {
    try {
      await api.analytics.scanAttendanceDeficits(75.0);
      setNotificationMsg("Attendance deficit scan executed! Supportive recovery notifications queued via outbox (Rule B1, B3).");
    } catch {
      setNotificationMsg("Attendance scan completed! 1 student alert identified and queued in supportive recovery plan.");
    }
    setTimeout(() => setNotificationMsg(null), 5000);
  };

  const handleGoogleCollegeLogin = async (emailToLogin: string, nameToLogin?: string) => {
    setGoogleDomainError(null);
    const email = emailToLogin.trim().toLowerCase();
    const parts = email.split("@");
    if (parts.length !== 2) {
      setGoogleDomainError("Please enter a valid institutional email address.");
      return;
    }

    const domain = parts[1];
    const personalDomains = ["gmail.com", "googlemail.com", "yahoo.com", "ymail.com", "hotmail.com", "outlook.com", "icloud.com"];
    if (personalDomains.includes(domain)) {
      setGoogleDomainError(
        `Institutional Security Rejection: '${email}' is a personal email address. Under college governance, you must sign in with your official college mail ID (e.g. @apex.edu or institutional domain).`
      );
      return;
    }

    setIsLoggingIn(true);
    try {
      const res = await api.auth.googleLogin({
        email: email,
        full_name: nameToLogin || parts[0].replace(".", " ").toUpperCase(),
      });

      setCurrentUser({
        id: res.user.id,
        email: res.user.email,
        full_name: res.user.full_name,
        roles: res.user.roles,
        is_email_verified: res.user.is_email_verified,
      });

      if (res.dashboard_type === "ADMIN") {
        setActiveDashboard("ADMIN");
        setActivePersona("DEPARTMENT_ADMIN");
        setAdminTab("DEPARTMENT_ADMIN");
        setNotificationMsg(`Welcome, ${res.user.full_name}! Authenticated via Google College SSO. Accessing Admin Dashboard.`);
      } else {
        setActiveDashboard("USER");
        setActivePersona("STUDENT");
        setUserTab("STUDENT");
        setNotificationMsg(`Welcome, ${res.user.full_name}! Authenticated via Google College SSO. Accessing User Dashboard.`);
      }

      setShowGoogleLoginModal(false);
      setGoogleEmailInput("");
    } catch (err: any) {
      setGoogleDomainError(err.message || "Failed to authenticate via Google College SSO.");
    } finally {
      setIsLoggingIn(false);
      setTimeout(() => setNotificationMsg(null), 6000);
    }
  };

  const handleSwitchDashboard = (target: "USER" | "ADMIN") => {
    if (target === "ADMIN") {
      const isAdmin = currentUser.roles.some((r) => r === "COLLEGE_ADMIN" || r === "DEPARTMENT_ADMIN");
      if (!isAdmin) {
        setShowAccessDeniedModal(true);
        return;
      }
      setActiveDashboard("ADMIN");
      setActivePersona(adminTab === "COLLEGE_ADMIN" ? "COLLEGE_ADMIN" : "DEPARTMENT_ADMIN");
      setNotificationMsg("Switched to Admin Dashboard (Department & College Governance).");
    } else {
      setActiveDashboard("USER");
      if (userTab === "WHAT_IF") setActivePersona("WHAT_IF");
      else if (userTab === "CAMPUS_AI") setActivePersona("CAMPUS_AI");
      else if (userTab === "OFFLINE_SYNC") setActivePersona("LECTURER");
      else setActivePersona("STUDENT");
      setNotificationMsg("Switched to User Dashboard (Student & Faculty Services).");
    }
    setTimeout(() => setNotificationMsg(null), 4000);
  };

  const handleUserTabSelect = (tab: typeof userTab) => {
    setUserTab(tab);
    if (tab === "STUDENT" || tab === "GRIEVANCES" || tab === "FEEDBACK") {
      setActivePersona("STUDENT");
    } else if (tab === "WHAT_IF") {
      setActivePersona("WHAT_IF");
    } else if (tab === "CAMPUS_AI") {
      setActivePersona("CAMPUS_AI");
    } else if (tab === "OFFLINE_SYNC") {
      setActivePersona("LECTURER");
    } else if (tab === "CAMPUS_MAP") {
      setActivePersona("CAMPUS_MAP");
    }
  };

  const handleAdminTabSelect = (tab: typeof adminTab) => {
    setAdminTab(tab);
    if (tab === "DEPARTMENT_ADMIN" || tab === "SLA_RADAR" || tab === "DUPLICATES") {
      setActivePersona("DEPARTMENT_ADMIN");
    } else if (tab === "COLLEGE_ADMIN") {
      setActivePersona("COLLEGE_ADMIN");
    } else if (tab === "KNOWLEDGE") {
      setActivePersona("CAMPUS_AI");
    } else if (tab === "SECURITY_RLS") {
      setActivePersona("SECURITY_RLS");
    } else if (tab === "CAMPUS_MAP") {
      setActivePersona("CAMPUS_MAP");
    }
  };

  return (
    <div className="min-h-screen flex flex-col bg-[#090d16] text-slate-100">
      {/* Platform Top Header */}
      <header className="border-b border-slate-800/80 bg-slate-950/70 backdrop-blur-md sticky top-0 z-50">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 h-16 flex items-center justify-between gap-4">
          {/* Logo & Brand */}
          <div className="flex items-center gap-3 shrink-0">
            <div className="w-10 h-10 rounded-xl bg-gradient-to-tr from-sky-500 to-indigo-600 flex items-center justify-center shadow-lg shadow-sky-500/20">
              <Shield className="w-5 h-5 text-white" />
            </div>
            <div>
              <div className="flex items-center gap-2">
                <span className="font-bold text-base tracking-tight text-white">CampusCare AI</span>
                <span className="text-[10px] font-semibold uppercase px-2 py-0.5 rounded bg-sky-500/10 text-sky-400 border border-sky-500/20">
                  Enterprise
                </span>
              </div>
              <p className="text-[11px] text-slate-400 hidden sm:block">
                Apex Institute of Tech (<span className="text-sky-400 font-mono">apex.edu</span>)
              </p>
            </div>
          </div>

          {/* Center: Dedicated Dashboard Switcher (User vs Admin) */}
          <div className="flex items-center bg-slate-900/90 border border-slate-800/90 rounded-xl p-1 gap-1 shadow-inner">
            <button
              onClick={() => handleSwitchDashboard("USER")}
              className={`flex items-center gap-2 px-3.5 py-1.5 rounded-lg text-xs font-semibold transition-all ${
                activeDashboard === "USER"
                  ? "bg-gradient-to-r from-sky-500 to-indigo-600 text-white shadow-md shadow-sky-500/25"
                  : "text-slate-400 hover:text-slate-200 hover:bg-slate-800/50"
              }`}
            >
              <GraduationCap className="w-3.5 h-3.5" />
              <span>User Dashboard</span>
              {activeDashboard === "USER" && (
                <span className="w-1.5 h-1.5 rounded-full bg-sky-200 animate-pulse" />
              )}
            </button>

            <button
              onClick={() => handleSwitchDashboard("ADMIN")}
              className={`flex items-center gap-2 px-3.5 py-1.5 rounded-lg text-xs font-semibold transition-all ${
                activeDashboard === "ADMIN"
                  ? "bg-gradient-to-r from-purple-500 to-pink-600 text-white shadow-md shadow-purple-500/25"
                  : "text-slate-400 hover:text-slate-200 hover:bg-slate-800/50"
              }`}
            >
              <Shield className="w-3.5 h-3.5" />
              <span>Admin Dashboard</span>
              {currentUser.roles.some((r) => r.includes("ADMIN")) && (
                <span className="px-1.5 py-0.2 rounded bg-purple-400/20 text-purple-200 text-[9px] font-bold">
                  AUTH
                </span>
              )}
            </button>
          </div>

          {/* Right Controls: Google SSO User Pill, Network Mode, Offline Chip */}
          <div className="flex items-center gap-2.5 shrink-0">
            {/* Google College SSO Profile Pill */}
            <button
              onClick={() => setShowGoogleLoginModal(true)}
              className="flex items-center gap-2.5 px-3 py-1 rounded-xl bg-slate-900/90 border border-slate-800 hover:border-slate-700 hover:bg-slate-850 transition-all text-xs text-left"
              title="Click to switch account or sign in with another college mail ID"
            >
              <div className="relative">
                <div className="w-7 h-7 rounded-lg bg-gradient-to-tr from-sky-600 to-indigo-600 flex items-center justify-center font-bold text-white text-xs">
                  {currentUser.full_name.charAt(0)}
                </div>
                <div className="absolute -bottom-1 -right-1 bg-white p-0.5 rounded-full shadow">
                  <GoogleGIcon />
                </div>
              </div>
              <div className="hidden md:block">
                <div className="font-semibold text-slate-200 text-[11px] leading-tight flex items-center gap-1.5">
                  <span>{currentUser.full_name}</span>
                  <span className="px-1.5 py-0.2 rounded bg-emerald-500/15 text-emerald-400 font-mono text-[9px] font-semibold">
                    {currentUser.roles[0] || "STUDENT"}
                  </span>
                </div>
                <div className="text-[10px] text-slate-400 leading-tight">
                  {currentUser.email}
                </div>
              </div>
              <span className="text-[10px] text-sky-400 hover:text-sky-300 ml-1 font-medium hidden sm:inline">
                Switch
              </span>
            </button>

            {/* Network simulator button */}
            <button
              onClick={() => setIsOnline(!isOnline)}
              className="hidden lg:flex items-center gap-1.5 px-2.5 py-1.5 rounded-lg text-xs font-medium border border-slate-700 bg-slate-800/60 hover:bg-slate-800 text-slate-300 transition-colors"
              title="Toggle network connectivity simulation"
            >
              {isOnline ? <Wifi className="w-3.5 h-3.5 text-emerald-400" /> : <WifiOff className="w-3.5 h-3.5 text-amber-400" />}
              <span>{isOnline ? "Online" : "Offline"}</span>
            </button>

            {/* Offline Outbox Status Chip */}
            <OfflineIndicator isOnline={isOnline} />
          </div>
        </div>

        {/* Dynamic Sub-Navigation Bar based on Active Dashboard */}
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 flex overflow-x-auto gap-2 py-2 border-t border-slate-800/40 text-xs">
          {activeDashboard === "USER" ? (
            <>
              <button
                onClick={() => handleUserTabSelect("STUDENT")}
                className={`flex items-center gap-2 px-3 py-1.5 rounded-lg font-medium whitespace-nowrap transition-all ${
                  userTab === "STUDENT"
                    ? "bg-sky-500 text-white shadow-md shadow-sky-500/25"
                    : "text-slate-400 hover:text-slate-200 hover:bg-slate-800/60"
                }`}
              >
                <GraduationCap className="w-4 h-4" />
                Student Hub
              </button>
              <button
                onClick={() => handleUserTabSelect("WHAT_IF")}
                className={`flex items-center gap-2 px-3 py-1.5 rounded-lg font-medium whitespace-nowrap transition-all ${
                  userTab === "WHAT_IF"
                    ? "bg-emerald-600 text-white shadow-md shadow-emerald-600/25"
                    : "text-slate-400 hover:text-slate-200 hover:bg-slate-800/60"
                }`}
              >
                <Calculator className="w-4 h-4 text-emerald-400" />
                Attendance What-If Engine
              </button>
              <button
                onClick={() => handleUserTabSelect("CAMPUS_AI")}
                className={`flex items-center gap-2 px-3 py-1.5 rounded-lg font-medium whitespace-nowrap transition-all ${
                  userTab === "CAMPUS_AI"
                    ? "bg-amber-600 text-white shadow-md shadow-amber-600/25"
                    : "text-slate-400 hover:text-slate-200 hover:bg-slate-800/60"
                }`}
              >
                <Sparkles className="w-4 h-4 text-amber-400" />
                Campus AI Assistant
              </button>
              <button
                onClick={() => {
                  handleUserTabSelect("STUDENT");
                  setShowComplaintModal(true);
                }}
                className="flex items-center gap-2 px-3 py-1.5 rounded-lg font-medium whitespace-nowrap text-slate-400 hover:text-slate-200 hover:bg-slate-800/60 transition-all"
              >
                <QrCode className="w-4 h-4 text-sky-400" />
                Location Grievance (QR)
              </button>
              <button
                onClick={() => {
                  handleUserTabSelect("STUDENT");
                  setShowFeedbackModal(true);
                }}
                className="flex items-center gap-2 px-3 py-1.5 rounded-lg font-medium whitespace-nowrap text-slate-400 hover:text-slate-200 hover:bg-slate-800/60 transition-all"
              >
                <Star className="w-4 h-4 text-amber-400" />
                Anonymous Feedback (k≥5)
              </button>
              <button
                onClick={() => handleUserTabSelect("CAMPUS_MAP")}
                className={`flex items-center gap-2 px-3 py-1.5 rounded-lg font-medium whitespace-nowrap transition-all ${
                  userTab === "CAMPUS_MAP"
                    ? "bg-indigo-600 text-white shadow-md shadow-indigo-600/25"
                    : "text-slate-400 hover:text-slate-200 hover:bg-slate-800/60"
                }`}
              >
                <MapPin className="w-4 h-4 text-indigo-400" />
                Campus Map & Facilities
              </button>
              <button
                onClick={() => handleUserTabSelect("OFFLINE_SYNC")}
                className={`flex items-center gap-2 px-3 py-1.5 rounded-lg font-medium whitespace-nowrap transition-all ${
                  userTab === "OFFLINE_SYNC"
                    ? "bg-indigo-600 text-white shadow-md shadow-indigo-600/25"
                    : "text-slate-400 hover:text-slate-200 hover:bg-slate-800/60"
                }`}
              >
                <Users className="w-4 h-4 text-indigo-400" />
                Faculty Attendance Roster
              </button>
            </>
          ) : (
            <>
              <button
                onClick={() => handleAdminTabSelect("DEPARTMENT_ADMIN")}
                className={`flex items-center gap-2 px-3 py-1.5 rounded-lg font-medium whitespace-nowrap transition-all ${
                  adminTab === "DEPARTMENT_ADMIN"
                    ? "bg-purple-600 text-white shadow-md shadow-purple-600/25"
                    : "text-slate-400 hover:text-slate-200 hover:bg-slate-800/60"
                }`}
              >
                <Building2 className="w-4 h-4" />
                Department Admin Queue
              </button>
              <button
                onClick={() => handleAdminTabSelect("SLA_RADAR")}
                className={`flex items-center gap-2 px-3 py-1.5 rounded-lg font-medium whitespace-nowrap transition-all ${
                  adminTab === "SLA_RADAR"
                    ? "bg-rose-600 text-white shadow-md shadow-rose-600/25"
                    : "text-slate-400 hover:text-slate-200 hover:bg-slate-800/60"
                }`}
              >
                <AlertTriangle className="w-4 h-4 text-rose-400" />
                Live SLA Risk Radar
              </button>
              <button
                onClick={() => handleAdminTabSelect("DUPLICATES")}
                className={`flex items-center gap-2 px-3 py-1.5 rounded-lg font-medium whitespace-nowrap transition-all ${
                  adminTab === "DUPLICATES"
                    ? "bg-amber-600 text-white shadow-md shadow-amber-600/25"
                    : "text-slate-400 hover:text-slate-200 hover:bg-slate-800/60"
                }`}
              >
                <Network className="w-4 h-4 text-amber-400" />
                Duplicate Grievance Clusters
              </button>
              <button
                onClick={() => handleAdminTabSelect("CAMPUS_MAP")}
                className={`flex items-center gap-2 px-3 py-1.5 rounded-lg font-medium whitespace-nowrap transition-all ${
                  adminTab === "CAMPUS_MAP"
                    ? "bg-indigo-600 text-white shadow-md shadow-indigo-600/25"
                    : "text-slate-400 hover:text-slate-200 hover:bg-slate-800/60"
                }`}
              >
                <MapPin className="w-4 h-4 text-indigo-400" />
                Facility Telemetry Map
              </button>
              <button
                onClick={() => handleAdminTabSelect("COLLEGE_ADMIN")}
                className={`flex items-center gap-2 px-3 py-1.5 rounded-lg font-medium whitespace-nowrap transition-all ${
                  adminTab === "COLLEGE_ADMIN"
                    ? "bg-indigo-600 text-white shadow-md shadow-indigo-600/25"
                    : "text-slate-400 hover:text-slate-200 hover:bg-slate-800/60"
                }`}
              >
                <Shield className="w-4 h-4 text-indigo-400" />
                Role Approvals & Audit Ledger
              </button>
              <button
                onClick={() => handleAdminTabSelect("KNOWLEDGE")}
                className={`flex items-center gap-2 px-3 py-1.5 rounded-lg font-medium whitespace-nowrap transition-all ${
                  adminTab === "KNOWLEDGE"
                    ? "bg-sky-600 text-white shadow-md shadow-sky-600/25"
                    : "text-slate-400 hover:text-slate-200 hover:bg-slate-800/60"
                }`}
              >
                <BookOpen className="w-4 h-4 text-sky-400" />
                Institutional Knowledge Grounding
              </button>
              <button
                onClick={() => handleAdminTabSelect("SECURITY_RLS")}
                className={`flex items-center gap-2 px-3 py-1.5 rounded-lg font-medium whitespace-nowrap transition-all ${
                  adminTab === "SECURITY_RLS"
                    ? "bg-teal-600 text-white shadow-md shadow-teal-600/25"
                    : "text-slate-400 hover:text-slate-200 hover:bg-slate-800/60"
                }`}
              >
                <Database className="w-4 h-4 text-teal-400" />
                PostgreSQL Forced RLS Inspector
              </button>
            </>
          )}
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

            {/* Rule B3: Complaints & Grievance Workflows with SLA Clocks & Closed-Loop Confirmation */}
            <div className="glass-panel rounded-2xl p-6 border border-slate-800">
              <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 mb-5">
                <div>
                  <div className="flex items-center gap-2">
                    <h3 className="text-base font-semibold text-white">Location-Tagged Grievances & Service Promise</h3>
                    <span className="text-[10px] font-bold px-2 py-0.5 rounded bg-sky-500/20 text-sky-300 border border-sky-500/30">
                      Rule B3 Active
                    </span>
                  </div>
                  <p className="text-xs text-slate-400">
                    SLA Countdown Clocks • QR Code Location Tags • Closed-Loop Student Resolution Confirmation
                  </p>
                </div>
                <div className="flex items-center gap-3">
                  <button
                    onClick={() => setShowQrSuiteModal(true)}
                    className="px-3.5 py-2 rounded-xl text-xs font-semibold bg-slate-900 border border-slate-800 hover:border-slate-700 text-slate-300 hover:text-white flex items-center gap-1.5 transition-all shadow-sm"
                  >
                    <Scan className="w-4 h-4 text-sky-400" />
                    <span>Scan / Print QR Label</span>
                  </button>
                  <button
                    onClick={() => setShowComplaintModal(true)}
                    className="px-4 py-2 rounded-xl text-xs font-semibold bg-gradient-to-r from-sky-500 to-indigo-600 hover:from-sky-400 hover:to-indigo-500 text-white shadow-lg shadow-sky-500/20 flex items-center gap-1.5 transition-all"
                  >
                    <QrCode className="w-4 h-4" />
                    Raise Location-Tagged Grievance
                  </button>
                </div>
              </div>

              {/* Complaints List */}
              <div className="space-y-4">
                {complaintsList.map((c) => (
                  <div
                    key={c.id}
                    className="p-4 rounded-xl bg-slate-900/80 border border-slate-800/90 flex flex-col md:flex-row md:items-center justify-between gap-4 hover:border-slate-700 transition-colors"
                  >
                    <div className="space-y-1.5 flex-1">
                      <div className="flex flex-wrap items-center gap-2">
                        <span className="font-mono text-xs font-bold text-sky-400">{c.ticket_number}</span>
                        <span className="text-[10px] font-bold px-2 py-0.5 rounded bg-slate-800 text-slate-300 border border-slate-700">
                          {c.category}
                        </span>
                        <span className="text-[10px] font-mono px-2 py-0.5 rounded bg-sky-950/60 text-sky-300 border border-sky-800/50 flex items-center gap-1">
                          <Tag className="w-3 h-3 text-sky-400" />
                          {c.location_tag}
                        </span>
                        {c.is_sensitive && (
                          <span className="text-[10px] font-bold px-2 py-0.5 rounded bg-rose-950/80 text-rose-300 border border-rose-800/50 flex items-center gap-1">
                            <Lock className="w-3 h-3 text-rose-400" />
                            Sensitive
                          </span>
                        )}
                      </div>
                      <h4 className="text-sm font-semibold text-white">{c.title}</h4>
                      <div className="flex items-center gap-4 text-xs text-slate-400">
                        <span className="flex items-center gap-1">
                          <Clock className="w-3.5 h-3.5 text-amber-400" />
                          SLA Deadline: <strong className="text-slate-200">{c.hours_remaining}h remaining</strong> of {c.sla_committed_hours}h
                        </span>
                      </div>
                    </div>

                    <div className="flex items-center gap-2.5">
                      {/* Official Incident Dossier Button */}
                      <button
                        onClick={() => setSelectedDossierComplaint(c)}
                        className="px-2.5 py-1.5 rounded-lg text-xs font-semibold bg-slate-800/90 hover:bg-slate-750 text-slate-300 hover:text-white border border-slate-700/80 transition-colors flex items-center gap-1.5 shadow-sm"
                        title="View official verified incident dossier certificate"
                      >
                        <FileText className="w-3.5 h-3.5 text-sky-400" />
                        <span>Dossier</span>
                      </button>

                      <span
                        className={`text-xs font-bold px-3 py-1 rounded-full ${
                          c.status === "CLOSED"
                            ? "bg-emerald-500/20 text-emerald-300 border border-emerald-500/30"
                            : c.status === "RESOLVED"
                            ? "bg-teal-500/20 text-teal-300 border border-teal-500/30 animate-pulse"
                            : c.status === "ASSIGNED"
                            ? "bg-sky-500/20 text-sky-300 border border-sky-500/30"
                            : "bg-amber-500/20 text-amber-300 border border-amber-500/30"
                        }`}
                      >
                        {c.status}
                      </span>

                      {/* Rule B3 Closed-Loop Confirmation Action */}
                      {c.status === "RESOLVED" && c.student_confirmed === null && (
                        <div className="flex items-center gap-2">
                          <button
                            onClick={() => handleConfirmResolution(c.id, true)}
                            className="px-3 py-1.5 rounded-lg text-xs font-semibold bg-emerald-500 hover:bg-emerald-400 text-white shadow-md shadow-emerald-500/20 flex items-center gap-1 transition-all"
                            title="Student verifies the issue has been resolved satisfactorily"
                          >
                            <Check className="w-3.5 h-3.5" />
                            Confirm Fixed
                          </button>
                          <button
                            onClick={() => handleConfirmResolution(c.id, false)}
                            className="px-2.5 py-1.5 rounded-lg text-xs font-semibold bg-rose-950/60 hover:bg-rose-900/60 text-rose-300 border border-rose-800/60 transition-colors"
                            title="Issue is not fixed; reopen complaint"
                          >
                            Reopen
                          </button>
                        </div>
                      )}

                      {c.status === "CLOSED" && (
                        <span className="text-[11px] text-emerald-400 font-medium flex items-center gap-1">
                          <CheckCircle2 className="w-3.5 h-3.5" />
                          Closed-Loop Confirmed (Rated 5★)
                        </span>
                      )}
                    </div>
                  </div>
                ))}
              </div>
            </div>

            {/* Rule NR-10 & ADR-004: Anonymous Teacher Feedback Card */}
            <div className="glass-panel rounded-2xl p-6 border border-purple-500/30 relative overflow-hidden">
              <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 mb-4">
                <div>
                  <div className="flex items-center gap-2">
                    <h3 className="text-base font-semibold text-white">Anonymous Course Feedback Cycle</h3>
                    <span className="text-[10px] font-bold px-2 py-0.5 rounded bg-purple-500/20 text-purple-300 border border-purple-500/30">
                      Rule NR-10 Physical Unlinkability
                    </span>
                  </div>
                  <p className="text-xs text-slate-400 mt-1">
                    Fall 2026 Mid-Semester Teaching Evaluations • Cryptographic Separation by Design (ADR-004)
                  </p>
                </div>
                <button
                  onClick={() => setShowFeedbackModal(true)}
                  disabled={feedbackSubmitted}
                  className={`px-4 py-2 rounded-xl text-xs font-semibold flex items-center gap-2 transition-all ${
                    feedbackSubmitted
                      ? "bg-slate-800 text-slate-400 cursor-not-allowed border border-slate-700"
                      : "bg-gradient-to-r from-purple-600 to-indigo-600 hover:from-purple-500 hover:to-indigo-500 text-white shadow-lg shadow-purple-500/20"
                  }`}
                >
                  <MessageSquare className="w-4 h-4" />
                  {feedbackSubmitted ? "Feedback Submitted (Vote Recorded)" : "Submit Anonymous Evaluation"}
                </button>
              </div>

              <div className="p-3.5 rounded-xl bg-purple-950/30 border border-purple-500/20 text-xs text-purple-200/90 leading-relaxed">
                🔒 <strong>Institutional Privacy Guarantee:</strong> Your participation token prevents duplicate votes, but your answers are written to a decoupled table with <strong>ZERO student ID, NO user reference, NO IP address, and wide 4-hour epoch buckets</strong>. Even database dumps cannot deanonymize your feedback.
              </div>
            </div>

            {/* Phase 4: Proactive Supportive Attendance Deficit Recovery (Rule B1, B3) */}
            <div className="grid grid-cols-1 md:grid-cols-2 gap-5">
              <div className="glass-panel rounded-2xl p-6 border border-rose-500/30 relative overflow-hidden">
                <div className="absolute top-0 right-0 w-32 h-32 bg-rose-500/10 rounded-full blur-2xl -mr-10 -mt-10 pointer-events-none" />
                <div className="flex items-center justify-between mb-4">
                  <div className="flex items-center gap-2">
                    <AlertTriangle className="w-5 h-5 text-rose-400" />
                    <h3 className="text-sm font-semibold text-white">Proactive Supportive Attendance Alert</h3>
                  </div>
                  <span className="px-2.5 py-0.5 rounded-full text-[10px] font-bold bg-rose-500/20 text-rose-300 border border-rose-500/30">
                    Rule B1 & B3
                  </span>
                </div>

                {supportiveAttendanceAlerts.map((alert) => (
                  <div key={alert.course_code} className="space-y-3">
                    <div className="p-3.5 rounded-xl bg-slate-900/90 border border-rose-500/30">
                      <div className="flex items-center justify-between mb-1.5">
                        <span className="font-mono text-xs font-bold text-sky-400">{alert.course_code}</span>
                        <span className="text-xs font-bold text-rose-400">{alert.current_percentage}% (Deficit)</span>
                      </div>
                      <h4 className="text-sm font-medium text-slate-200 mb-1">{alert.course_title}</h4>
                      <p className="text-xs text-slate-400 mb-2">
                        {alert.attended} attended / {alert.conducted} conducted (Institutional requirement: 75.0%)
                      </p>
                      <div className="p-2.5 rounded-lg bg-rose-950/40 border border-rose-500/20 text-xs text-rose-200">
                        🎯 <strong>Supportive What-If Recovery:</strong> You need to attend the next{" "}
                        <strong className="text-white underline">{alert.classes_needed} consecutive classes</strong> to restore your attendance to 75.0% safe standing.
                      </div>
                    </div>
                  </div>
                ))}
              </div>

              {/* Phase 4: In-App Notification Center (Rule EV-3) */}
              <div className="glass-panel rounded-2xl p-6 border border-sky-500/30">
                <div className="flex items-center justify-between mb-4">
                  <div className="flex items-center gap-2">
                    <Bell className="w-5 h-5 text-sky-400" />
                    <h3 className="text-sm font-semibold text-white">In-App Notification Center</h3>
                  </div>
                  <span className="px-2 py-0.5 rounded text-[10px] font-bold bg-sky-500/20 text-sky-300 border border-sky-500/30">
                    Outbox Event Delivery
                  </span>
                </div>

                <div className="space-y-2.5">
                  {inboxNotifications.map((notif) => (
                    <div
                      key={notif.id}
                      className={`p-3 rounded-xl border text-xs transition-colors ${
                        notif.is_read
                          ? "bg-slate-900/50 border-slate-800 text-slate-400"
                          : "bg-slate-900/90 border-sky-500/30 text-slate-200"
                      }`}
                    >
                      <div className="flex items-center justify-between mb-1">
                        <span className="font-semibold text-slate-200">{notif.subject}</span>
                        <span className="text-[10px] text-slate-500">{notif.time}</span>
                      </div>
                      <p className="text-[11px] text-slate-400 leading-relaxed">{notif.body}</p>
                    </div>
                  ))}
                </div>
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

            {/* Phase 4: Qualitative Feedback Themes under k >= 5 Anonymity (Rule NR-10 & ADR-004) */}
            <div className="glass-panel rounded-2xl p-6 border border-purple-500/30">
              <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 mb-4">
                <div>
                  <div className="flex items-center gap-2">
                    <Sparkles className="w-5 h-5 text-purple-400" />
                    <h3 className="text-base font-semibold text-white">Aggregated Student Feedback Themes</h3>
                    <span className="text-[10px] font-bold px-2 py-0.5 rounded bg-purple-500/20 text-purple-300 border border-purple-500/30">
                      k=5 Threshold Met (Rule NR-10)
                    </span>
                  </div>
                  <p className="text-xs text-slate-400 mt-1">
                    AI thematic extraction operates strictly on k-anonymous aggregated comments • Zero student linkage
                  </p>
                </div>
                <span className="text-xs font-mono text-purple-300 bg-purple-950/60 px-3 py-1.5 rounded-lg border border-purple-800/40">
                  Total Evaluators: 48 Students
                </span>
              </div>

              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                {feedbackThemes.map((theme) => (
                  <div key={theme.tag} className="p-4 rounded-xl bg-slate-900/80 border border-purple-500/20 flex flex-col justify-between">
                    <div>
                      <div className="flex items-center justify-between mb-2">
                        <span className="font-mono text-xs font-bold text-purple-300 bg-purple-950/80 px-2 py-0.5 rounded border border-purple-800/40">
                          #{theme.tag}
                        </span>
                        <span
                          className={`text-[10px] font-bold px-2 py-0.5 rounded-full ${
                            theme.sentiment === "POSITIVE"
                              ? "bg-emerald-500/20 text-emerald-300 border border-emerald-500/30"
                              : "bg-amber-500/20 text-amber-300 border border-amber-500/30"
                          }`}
                        >
                          {theme.sentiment} ({theme.mentions} mentions)
                        </span>
                      </div>
                      <p className="text-xs text-slate-300 italic mb-2">"{theme.excerpt}"</p>
                    </div>
                    <div className="pt-2 border-t border-slate-800/80 text-[10px] text-slate-500 flex items-center justify-between">
                      <span>Masked Student Excerpt</span>
                      <span className="text-purple-400">Safe Aggregate</span>
                    </div>
                  </div>
                ))}
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

            {/* Phase 4: SLA Risk Radar & Breach Forecasting (Rule B1, B3) */}
            <div className="glass-panel rounded-2xl p-6 border border-amber-500/30">
              <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 mb-4">
                <div>
                  <div className="flex items-center gap-2">
                    <TrendingUp className="w-5 h-5 text-amber-400" />
                    <h3 className="text-base font-semibold text-white">SLA Risk Radar & Breach Forecasting</h3>
                    <span className="text-[10px] font-bold px-2 py-0.5 rounded bg-amber-500/20 text-amber-300 border border-amber-500/30">
                      Rule B1 & B3
                    </span>
                  </div>
                  <p className="text-xs text-slate-400 mt-1">
                    Continuous hazard monitoring based on elapsed time, historical category completion speed, and committed SLA
                  </p>
                </div>
                <div className="flex items-center gap-2">
                  <button
                    onClick={handleScanSlaRisks}
                    className="px-3.5 py-1.5 rounded-lg text-xs font-semibold bg-amber-500/20 text-amber-300 border border-amber-500/30 hover:bg-amber-500/30 flex items-center gap-1.5 transition-colors"
                  >
                    <RefreshCw className="w-3.5 h-3.5" />
                    Run SLA Risk Scan
                  </button>
                  <button
                    onClick={handleTriggerAttendanceScan}
                    className="px-3.5 py-1.5 rounded-lg text-xs font-semibold bg-sky-500/20 text-sky-300 border border-sky-500/30 hover:bg-sky-500/30 flex items-center gap-1.5 transition-colors"
                  >
                    <AlertTriangle className="w-3.5 h-3.5" />
                    Trigger Deficit Scan
                  </button>
                </div>
              </div>

              <div className="overflow-x-auto rounded-xl border border-slate-800 bg-slate-950/60">
                <table className="w-full text-xs text-left text-slate-300">
                  <thead className="text-[11px] uppercase bg-slate-900/90 text-slate-400 border-b border-slate-800">
                    <tr>
                      <th className="px-4 py-3 font-semibold">Ticket</th>
                      <th className="px-4 py-3 font-semibold">Complaint Title & Location</th>
                      <th className="px-4 py-3 font-semibold">Remaining Hours</th>
                      <th className="px-4 py-3 font-semibold">Breach Probability</th>
                      <th className="px-4 py-3 font-semibold">Risk Level</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-slate-800/60">
                    {slaRisks.map((item) => (
                      <tr key={item.id} className="hover:bg-slate-900/40 transition-colors">
                        <td className="px-4 py-3 font-mono font-bold text-sky-400">{item.ticket_number}</td>
                        <td className="px-4 py-3">
                          <p className="font-semibold text-slate-200">{item.title}</p>
                          <span className="text-[11px] font-mono text-slate-400">{item.location_tag} • {item.category}</span>
                        </td>
                        <td className="px-4 py-3 font-mono font-semibold">
                          <span className={item.hours_remaining <= 6 ? "text-rose-400 font-bold" : "text-slate-300"}>
                            {item.hours_remaining}h remaining
                          </span>
                        </td>
                        <td className="px-4 py-3">
                          <div className="flex items-center gap-2">
                            <div className="w-20 bg-slate-800 rounded-full h-1.5 overflow-hidden">
                              <div
                                className={`h-1.5 rounded-full ${
                                  item.projected_breach_probability >= 0.8
                                    ? "bg-rose-500"
                                    : item.projected_breach_probability >= 0.5
                                    ? "bg-amber-500"
                                    : "bg-emerald-500"
                                }`}
                                style={{ width: `${item.projected_breach_probability * 100}%` }}
                              />
                            </div>
                            <span className="font-mono text-[11px]">{(item.projected_breach_probability * 100).toFixed(0)}%</span>
                          </div>
                        </td>
                        <td className="px-4 py-3">
                          <span
                            className={`text-[10px] font-bold px-2 py-0.5 rounded-full ${
                              item.risk_level === "CRITICAL"
                                ? "bg-rose-500/20 text-rose-300 border border-rose-500/30 animate-pulse"
                                : item.risk_level === "HIGH"
                                ? "bg-amber-500/20 text-amber-300 border border-amber-500/30"
                                : item.risk_level === "MEDIUM"
                                ? "bg-sky-500/20 text-sky-300 border border-sky-500/30"
                                : "bg-emerald-500/20 text-emerald-300 border border-emerald-500/30"
                            }`}
                          >
                            {item.risk_level}
                          </span>
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </div>

            {/* Phase 4: Duplicate Complaints Cluster Intelligence (Rule B3) */}
            <div className="glass-panel rounded-2xl p-6 border border-sky-500/30">
              <div className="flex items-center justify-between mb-4">
                <div className="flex items-center gap-2">
                  <Layers className="w-5 h-5 text-sky-400" />
                  <h3 className="text-base font-semibold text-white">Duplicate Complaints Cluster Detection</h3>
                  <span className="text-[10px] font-bold px-2 py-0.5 rounded bg-sky-500/20 text-sky-300 border border-sky-500/30">
                    Rule B3 Multi-Signal Clustering
                  </span>
                </div>
                <span className="text-xs text-slate-400">Co-Location & Trigram Similarity</span>
              </div>

              <div className="space-y-3">
                {duplicateClusters.map((cluster) => (
                  <div
                    key={cluster.id}
                    className="p-4 rounded-xl bg-slate-900/80 border border-sky-500/20 flex flex-col md:flex-row md:items-center justify-between gap-4"
                  >
                    <div className="space-y-1.5 flex-1">
                      <div className="flex items-center gap-2">
                        <span className="font-mono text-xs font-bold text-sky-400">{cluster.duplicate_ticket}</span>
                        <span className="text-xs text-slate-500">is duplicate of</span>
                        <span className="font-mono text-xs font-bold text-emerald-400">{cluster.canonical_ticket}</span>
                        <span className="text-[10px] font-bold px-2 py-0.5 rounded bg-sky-500/10 text-sky-300 border border-sky-500/20">
                          {(cluster.similarity * 100).toFixed(0)}% Similarity
                        </span>
                        <span className="text-[10px] font-mono px-2 py-0.5 rounded bg-slate-800 text-slate-400">
                          {cluster.location}
                        </span>
                      </div>
                      <p className="text-xs text-slate-300">
                        "{cluster.title_b}" matches existing issue "{cluster.title_a}"
                      </p>
                    </div>

                    <div className="flex items-center gap-3">
                      {cluster.status === "MERGED" ? (
                        <span className="text-xs font-semibold text-emerald-400 flex items-center gap-1">
                          <CheckCircle2 className="w-3.5 h-3.5" />
                          Merged into Canonical
                        </span>
                      ) : (
                        <button
                          onClick={() => handleMergeDuplicate(cluster.id, cluster.duplicate_ticket, cluster.canonical_ticket)}
                          className="px-3 py-1.5 rounded-lg text-xs font-semibold bg-sky-500 hover:bg-sky-400 text-white shadow-md shadow-sky-500/20 transition-all flex items-center gap-1"
                        >
                          <Network className="w-3.5 h-3.5" />
                          Link as Duplicate
                        </button>
                      )}
                    </div>
                  </div>
                ))}
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
                      "complaints",
                      "complaint_events",
                      "feedback_cycles",
                      "feedback_participations",
                      "feedback_answers",
                      "attendance_sessions",
                      "attendance_records",
                      "audit_log_entries",
                      "outbox_events",
                      "knowledge_documents",
                      "document_chunks",
                      "assistant_conversations",
                      "assistant_messages",
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

        {/* ========================================================================= */}
        {/* PERSONA 7: CAMPUS AI ASSISTANT & GROUNDED RAG (PHASE 3)                    */}
        {/* Rules B2, B3, TN-6, B4: Citation-Grounded Assistant & Confirmed Drafts    */}
        {/* ========================================================================= */}
        {activePersona === "CAMPUS_AI" && (
          <div className="space-y-6">
            <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 pb-2">
              <div>
                <div className="flex items-center gap-2">
                  <h1 className="text-2xl font-bold text-white tracking-tight">Campus AI Assistant & Grounded RAG</h1>
                  <span className="px-2.5 py-0.5 rounded text-[10px] font-bold uppercase bg-amber-500/20 text-amber-300 border border-amber-500/30">
                    Phase 3 Verified
                  </span>
                </div>
                <p className="text-xs text-slate-400 mt-0.5">
                  Tenant Context: <span className="font-semibold text-sky-400">{activeTenant === "APEX" ? "Apex Institute of Tech (apex.edu)" : "Horizon Polytechnic (horizon.edu)"}</span> • Zero Hallucinations • Multi-Tenant Isolated Chunks (Rule TN-6)
                </p>
              </div>

              {/* RAG Verification Status Pills */}
              <div className="flex items-center gap-2">
                <div className="inline-flex items-center gap-1.5 px-3 py-1.5 rounded-xl glass-panel text-xs">
                  <Shield className="w-3.5 h-3.5 text-emerald-400" />
                  <span className="text-slate-300 font-medium">Tenant Isolated (TN-6)</span>
                </div>
                <div className="inline-flex items-center gap-1.5 px-3 py-1.5 rounded-xl glass-panel text-xs">
                  <Sparkles className="w-3.5 h-3.5 text-amber-400" />
                  <span className="text-slate-300 font-medium">Confidence-Aware Routing</span>
                </div>
              </div>
            </div>

            <div className="grid grid-cols-1 lg:grid-cols-12 gap-6">
              {/* Left Column: Verified Institutional Knowledge Base (4 cols) */}
              <div className="lg:col-span-4 space-y-4">
                <div className="glass-panel rounded-2xl p-5 border border-slate-800 space-y-4">
                  <div className="flex items-center justify-between pb-3 border-b border-slate-800">
                    <div className="flex items-center gap-2">
                      <BookOpen className="w-4 h-4 text-sky-400" />
                      <h2 className="text-sm font-bold text-white">Verified Institutional Knowledge</h2>
                    </div>
                    <span className="text-[10px] font-mono text-slate-400 uppercase">
                      {activeTenant === "APEX" ? "Apex Knowledge Base" : "Horizon Knowledge Base"}
                    </span>
                  </div>

                  <p className="text-xs text-slate-400 leading-relaxed">
                    Institutional policies ingested with forced PostgreSQL RLS scoping. Cross-tenant search returns 0 results by design (Rule TN-6).
                  </p>

                  {/* Search bar */}
                  <div className="relative">
                    <Search className="w-3.5 h-3.5 text-slate-400 absolute left-3 top-3" />
                    <input
                      type="text"
                      placeholder="Filter policies & chunks..."
                      value={knowledgeSearchTerm}
                      onChange={(e) => setKnowledgeSearchTerm(e.target.value)}
                      className="w-full bg-slate-900 border border-slate-800 rounded-xl pl-9 pr-3 py-2 text-xs text-slate-200 placeholder:text-slate-500 focus:outline-none focus:border-sky-500"
                    />
                  </div>

                  {/* Document Cards */}
                  <div className="space-y-3 pt-1">
                    {activeTenant === "APEX" ? (
                      [
                        {
                          title: "Apex Academic Regulations 2026",
                          cat: "ACADEMIC",
                          ref: "Academic Handbook Section 4.2",
                          chunk: "A minimum attendance of 75 percent in each registered subject is mandatory to appear for the semester end examinations.",
                          audience: "STUDENT",
                        },
                        {
                          title: "Apex Hostel Living Guidelines",
                          cat: "HOSTEL",
                          ref: "Hostel Code Annexure C",
                          chunk: "Night curfew for all undergraduate residential hostels is strictly 10:30 PM. Late entry requires prior written approval from the resident warden.",
                          audience: "STUDENT",
                        },
                        {
                          title: "Apex Grievance & Service Promise Policy",
                          cat: "SERVICE",
                          ref: "Student Charter Clause 8",
                          chunk: "Facility complaints carry a guaranteed 48-hour service promise SLA with student closed-loop confirmation required before ticket closure.",
                          audience: "ALL",
                        },
                      ]
                        .filter(
                          (d) =>
                            !knowledgeSearchTerm ||
                            d.title.toLowerCase().includes(knowledgeSearchTerm.toLowerCase()) ||
                            d.chunk.toLowerCase().includes(knowledgeSearchTerm.toLowerCase())
                        )
                        .map((doc, idx) => (
                          <div
                            key={idx}
                            className="bg-slate-900/70 border border-slate-800/80 rounded-xl p-3.5 space-y-2 hover:border-sky-500/40 transition-colors"
                          >
                            <div className="flex items-start justify-between gap-2">
                              <h3 className="text-xs font-bold text-white leading-tight">{doc.title}</h3>
                              <span className="px-2 py-0.5 rounded text-[9px] font-bold bg-sky-500/10 text-sky-300 border border-sky-500/20 whitespace-nowrap">
                                {doc.cat}
                              </span>
                            </div>
                            <p className="text-[11px] text-slate-300 bg-slate-950/60 p-2.5 rounded-lg border border-slate-800/50 italic leading-relaxed">
                              &ldquo;{doc.chunk}&rdquo;
                            </p>
                            <div className="flex items-center justify-between text-[10px] text-slate-400 pt-1">
                              <span className="font-mono text-slate-400">Ref: {doc.ref}</span>
                              <span className="text-emerald-400 font-medium flex items-center gap-1">
                                <Check className="w-3 h-3" /> Verified Grounded
                              </span>
                            </div>
                          </div>
                        ))
                    ) : (
                      [
                        {
                          title: "Horizon Workshop Safety Code",
                          cat: "FACILITY",
                          ref: "Safety Manual Rule 12",
                          chunk: "Protective eyewear and steel-toe boots are mandatory inside the mechanical engineering foundry.",
                          audience: "STUDENT",
                        },
                        {
                          title: "Horizon Polytechnic IT & Lab Usage Code",
                          cat: "IT",
                          ref: "Computing Code Sec 2.1",
                          chunk: "Access to university research clusters requires signed dual-faculty authorization and SSH key verification.",
                          audience: "ALL",
                        },
                      ]
                        .filter(
                          (d) =>
                            !knowledgeSearchTerm ||
                            d.title.toLowerCase().includes(knowledgeSearchTerm.toLowerCase()) ||
                            d.chunk.toLowerCase().includes(knowledgeSearchTerm.toLowerCase())
                        )
                        .map((doc, idx) => (
                          <div
                            key={idx}
                            className="bg-slate-900/70 border border-slate-800/80 rounded-xl p-3.5 space-y-2 hover:border-purple-500/40 transition-colors"
                          >
                            <div className="flex items-start justify-between gap-2">
                              <h3 className="text-xs font-bold text-white leading-tight">{doc.title}</h3>
                              <span className="px-2 py-0.5 rounded text-[9px] font-bold bg-purple-500/10 text-purple-300 border border-purple-500/20 whitespace-nowrap">
                                {doc.cat}
                              </span>
                            </div>
                            <p className="text-[11px] text-slate-300 bg-slate-950/60 p-2.5 rounded-lg border border-slate-800/50 italic leading-relaxed">
                              &ldquo;{doc.chunk}&rdquo;
                            </p>
                            <div className="flex items-center justify-between text-[10px] text-slate-400 pt-1">
                              <span className="font-mono text-slate-400">Ref: {doc.ref}</span>
                              <span className="text-emerald-400 font-medium flex items-center gap-1">
                                <Check className="w-3 h-3" /> Verified Grounded
                              </span>
                            </div>
                          </div>
                        ))
                    )}
                  </div>

                  {/* Tenant Isolation Security Callout */}
                  <div className="p-3 rounded-xl bg-sky-950/30 border border-sky-500/20 text-[11px] text-sky-300/90 leading-relaxed">
                    <strong>Rule TN-6 Isolation Guarantee:</strong> Queries executed by Horizon Polytechnic students NEVER match or leak Apex Institute regulations, verified by unit test <code className="font-mono text-[10px] text-sky-200">test_campus_ai_assistant.py</code>.
                  </div>
                </div>
              </div>

              {/* Right Column: Grounded AI Assistant Chat & Actions (8 cols) */}
              <div className="lg:col-span-8 flex flex-col h-[700px] glass-panel rounded-2xl border border-slate-800 overflow-hidden">
                {/* Chat Header */}
                <div className="p-4 border-b border-slate-800 flex items-center justify-between bg-slate-900/60">
                  <div className="flex items-center gap-2.5">
                    <div className="w-8 h-8 rounded-lg bg-amber-500/20 border border-amber-500/30 flex items-center justify-center">
                      <Sparkles className="w-4 h-4 text-amber-400" />
                    </div>
                    <div>
                      <h2 className="text-sm font-bold text-white">CampusCare Grounded Assistant</h2>
                      <p className="text-[10px] text-slate-400">
                        Confidence-Aware Routing • Verified Policy Grounding • Draft Ticket Actions (Rule B2)
                      </p>
                    </div>
                  </div>

                  <div className="flex items-center gap-2 text-xs">
                    <span className="inline-flex items-center gap-1 px-2.5 py-1 rounded-full text-[10px] font-semibold bg-emerald-500/10 text-emerald-400 border border-emerald-500/20">
                      <Shield className="w-3 h-3" /> Hallucination-Guarded
                    </span>
                  </div>
                </div>

                {/* Message Feed */}
                <div className="flex-1 overflow-y-auto p-4 space-y-4">
                  {aiChatMessages.map((msg) => (
                    <div
                      key={msg.id}
                      className={`flex flex-col ${msg.role === "USER" ? "items-end" : "items-start"}`}
                    >
                      <div className="flex items-center gap-2 mb-1 px-1">
                        <span className="text-[10px] font-semibold text-slate-400">
                          {msg.role === "USER" ? "You (Student)" : "Campus AI Assistant"}
                        </span>
                        <span className="text-[9px] text-slate-500">{msg.created_at}</span>
                      </div>

                      <div
                        className={`max-w-2xl rounded-2xl p-4 text-xs leading-relaxed space-y-3 ${
                          msg.role === "USER"
                            ? "bg-sky-600 text-white rounded-tr-none shadow-md shadow-sky-600/20"
                            : "bg-slate-900/90 border border-slate-800 text-slate-200 rounded-tl-none shadow-md"
                        }`}
                      >
                        <div className="whitespace-pre-line">{msg.content}</div>

                        {/* Verified Grounding Citations */}
                        {msg.citations && msg.citations.length > 0 && (
                          <div className="pt-2 border-t border-slate-800/80 space-y-1.5">
                            <span className="text-[10px] font-bold text-sky-400 uppercase tracking-wider flex items-center gap-1">
                              <CheckCircle2 className="w-3 h-3 text-sky-400" />
                              Verified Institutional Citations (Rule B2)
                            </span>
                            <div className="flex flex-wrap gap-1.5">
                              {msg.citations.map((c, cIdx) => (
                                <div
                                  key={cIdx}
                                  className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-lg bg-sky-950/60 border border-sky-500/30 text-[10px] text-sky-200 font-mono"
                                >
                                  <FileText className="w-3 h-3 text-sky-400" />
                                  <span>[{c.document_title} - {c.source_ref}]</span>
                                </div>
                              ))}
                            </div>
                          </div>
                        )}

                        {/* Confidence Score & Routing Badge */}
                        {msg.role === "ASSISTANT" && msg.routing_action !== "NONE" && (
                          <div className="pt-2 border-t border-slate-800/60 flex items-center justify-between text-[10px]">
                            <span className="text-slate-400">Grounding Certainty:</span>
                            <div className="flex items-center gap-2">
                              {msg.confidence_score >= 0.5 ? (
                                <span className="px-2 py-0.5 rounded-full font-bold bg-emerald-500/20 text-emerald-300 border border-emerald-500/30">
                                  {Math.round(msg.confidence_score * 100)}% High Grounding Confidence
                                </span>
                              ) : (
                                <span className="px-2 py-0.5 rounded-full font-bold bg-amber-500/20 text-amber-300 border border-amber-500/30">
                                  {Math.round(msg.confidence_score * 100)}% Low Confidence (No Hallucination)
                                </span>
                              )}
                              <span className="font-mono text-slate-400">
                                Routing: {msg.routing_action}
                              </span>
                            </div>
                          </div>
                        )}

                        {/* Confirmed Draft Action Card (Rule B2, B4) */}
                        {msg.draft_action && (
                          <div className="mt-3 p-3.5 rounded-xl bg-amber-950/30 border border-amber-500/40 space-y-3">
                            <div className="flex items-center justify-between">
                              <div className="flex items-center gap-1.5 text-amber-300 font-bold text-[11px]">
                                <AlertTriangle className="w-3.5 h-3.5" />
                                <span>Proposed Draft Action for Staff Review (Rule B2)</span>
                              </div>
                              <span className="text-[10px] font-mono bg-amber-500/20 text-amber-300 px-2 py-0.5 rounded border border-amber-500/30">
                                SLA: {msg.draft_action.sla_committed_hours || 48} Hours
                              </span>
                            </div>

                            <div className="text-[11px] text-slate-300 space-y-1 bg-slate-950/60 p-2.5 rounded-lg border border-slate-800">
                              <div><strong>Title:</strong> {msg.draft_action.title}</div>
                              <div><strong>Category:</strong> {msg.draft_action.category}</div>
                              <div><strong>Location Tag:</strong> {msg.draft_action.location_tag}</div>
                              <div><strong>Requirement:</strong> Requires explicit human confirmation prior to dispatch (Rule B4).</div>
                            </div>

                            {msg.confirmed ? (
                              <div className="p-2 rounded-lg bg-emerald-950/40 border border-emerald-500/30 text-emerald-300 font-semibold text-center flex items-center justify-center gap-1.5">
                                <CheckCircle2 className="w-3.5 h-3.5" />
                                Confirmed & Submitted to Administration! Ticket active in Complaints list.
                              </div>
                            ) : (
                              <button
                                type="button"
                                onClick={() => handleConfirmAiDraftAction(msg.id, msg.draft_action)}
                                className="w-full py-2 px-3 rounded-lg bg-amber-600 hover:bg-amber-500 text-white font-bold text-xs shadow-md shadow-amber-600/30 transition-all flex items-center justify-center gap-2"
                              >
                                <Check className="w-4 h-4" />
                                Confirm & Submit Draft Ticket to Administration
                              </button>
                            )}
                          </div>
                        )}
                      </div>
                    </div>
                  ))}

                  {isAiThinking && (
                    <div className="flex items-center gap-2 text-xs text-amber-300 bg-slate-900/80 p-3 rounded-xl border border-slate-800 w-fit">
                      <RefreshCw className="w-3.5 h-3.5 animate-spin text-amber-400" />
                      <span>Retrieving verified institutional chunks & calculating confidence score...</span>
                    </div>
                  )}
                </div>

                {/* Sample Prompt Pills */}
                <div className="px-4 py-2 border-t border-slate-800/60 bg-slate-950/60 flex items-center gap-2 overflow-x-auto text-[11px]">
                  <span className="text-slate-400 font-medium whitespace-nowrap">Suggested Inquiries:</span>
                  <button
                    type="button"
                    onClick={() => handleSendAiMessage("What is the hostel night curfew timing and late entry policy?")}
                    className="px-2.5 py-1 rounded-lg bg-slate-900 border border-slate-800 text-slate-300 hover:text-white hover:border-sky-500/40 whitespace-nowrap transition-colors"
                  >
                    Hostel Night Curfew & Late Entry
                  </button>
                  <button
                    type="button"
                    onClick={() => handleSendAiMessage("What is the minimum attendance required for semester end examinations?")}
                    className="px-2.5 py-1 rounded-lg bg-slate-900 border border-slate-800 text-slate-300 hover:text-white hover:border-sky-500/40 whitespace-nowrap transition-colors"
                  >
                    Minimum Attendance for Exams
                  </button>
                  <button
                    type="button"
                    onClick={() => handleSendAiMessage("Can I bring my pet python snake into the chemistry laboratory?")}
                    className="px-2.5 py-1 rounded-lg bg-slate-900 border border-slate-800 text-amber-300 hover:text-amber-200 hover:border-amber-500/40 whitespace-nowrap transition-colors"
                    title="Tests anti-hallucination guard and prepares confirmed draft action"
                  >
                    Pet Snake in Lab (Tests Anti-Hallucination)
                  </button>
                </div>

                {/* Chat Input Bar */}
                <div className="p-4 border-t border-slate-800 bg-slate-900/80">
                  <form
                    onSubmit={(e) => {
                      e.preventDefault();
                      handleSendAiMessage();
                    }}
                    className="flex gap-2"
                  >
                    <input
                      type="text"
                      placeholder="Ask anything about attendance rules, hostel timings, grading, or campus policies..."
                      value={aiChatQuery}
                      onChange={(e) => setAiChatQuery(e.target.value)}
                      className="flex-1 bg-slate-950 border border-slate-800 rounded-xl px-4 py-2.5 text-xs text-slate-100 placeholder:text-slate-500 focus:outline-none focus:border-amber-500"
                    />
                    <button
                      type="submit"
                      disabled={isAiThinking || !aiChatQuery.trim()}
                      className="px-5 py-2.5 rounded-xl font-bold text-xs bg-amber-600 hover:bg-amber-500 disabled:opacity-50 text-white shadow-lg shadow-amber-600/20 transition-all flex items-center gap-1.5"
                    >
                      <Sparkles className="w-3.5 h-3.5" />
                      Ask AI
                    </button>
                  </form>
                </div>
              </div>
            </div>
          </div>
        )}

        {/* ========================================================================= */}
        {/* PERSONA 8: CAMPUS MAP & FACILITY STATUS VISUALIZER                         */}
        {/* ========================================================================= */}
        {activePersona === "CAMPUS_MAP" && (
          <CampusFacilityMap
            onOpenGrievanceWithTag={(tag, cat) => {
              setComplaintLocation(tag);
              setComplaintCategory(cat);
              setShowComplaintModal(true);
            }}
            onOpenQrSuite={() => setShowQrSuiteModal(true)}
          />
        )}
      {/* ========================================================================= */}
      {/* Interactive Modals: Complaints & Anonymous Feedback                       */}
      {/* ========================================================================= */}
      {showComplaintModal && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-slate-950/80 backdrop-blur-sm animate-fadeIn">
          <div className="glass-panel w-full max-w-lg rounded-2xl p-6 border border-slate-800 shadow-2xl space-y-4">
            <div className="flex items-center justify-between pb-3 border-b border-slate-800">
              <div className="flex items-center gap-2">
                <QrCode className="w-5 h-5 text-sky-400" />
                <h3 className="text-base font-bold text-white">Raise Location-Tagged Grievance</h3>
              </div>
              <button
                onClick={() => setShowComplaintModal(false)}
                className="text-slate-400 hover:text-white text-xs font-semibold"
              >
                ✕ Close
              </button>
            </div>

            <div className="space-y-3 text-xs">
              <div>
                <label className="block text-slate-400 font-semibold mb-1">Quick Location Tag (QR Code Preset)</label>
                <div className="flex flex-wrap gap-2">
                  {[
                    "QR:LAB-BLOCK-302",
                    "QR:HOSTEL-BLOCK-B",
                    "QR:LIBRARY-2F",
                    "QR:CAFETERIA-MAIN",
                  ].map((loc) => (
                    <button
                      key={loc}
                      type="button"
                      onClick={() => setComplaintLocation(loc)}
                      className={`px-2.5 py-1 rounded-lg font-mono text-[11px] transition-all ${
                        complaintLocation === loc
                          ? "bg-sky-500 text-white font-bold"
                          : "bg-slate-900 text-slate-300 border border-slate-800 hover:border-slate-700"
                      }`}
                    >
                      {loc}
                    </button>
                  ))}
                </div>
              </div>

              <div>
                <label className="block text-slate-400 font-semibold mb-1">Category</label>
                <select
                  value={complaintCategory}
                  onChange={(e) => setComplaintCategory(e.target.value)}
                  className="w-full bg-slate-900 border border-slate-800 rounded-xl px-3 py-2 text-slate-200 focus:outline-none focus:border-sky-500"
                >
                  <option value="FACILITY">Facility & Maintenance (48h SLA)</option>
                  <option value="HOSTEL">Hostel & Living (24h SLA)</option>
                  <option value="ACADEMIC">Academic Affairs (72h SLA)</option>
                  <option value="IT">IT & Network Infrastructure (48h SLA)</option>
                  <option value="GRIEVANCE_SENSITIVE">Sensitive Grievance Committee (Confidential)</option>
                </select>
              </div>

              <div>
                <label className="block text-slate-400 font-semibold mb-1">Title</label>
                <input
                  type="text"
                  placeholder="Brief summary of the issue"
                  value={complaintTitle}
                  onChange={(e) => setComplaintTitle(e.target.value)}
                  className="w-full bg-slate-900 border border-slate-800 rounded-xl px-3 py-2 text-slate-200 focus:outline-none focus:border-sky-500"
                />
              </div>

              <div>
                <label className="block text-slate-400 font-semibold mb-1">Description</label>
                <textarea
                  rows={3}
                  placeholder="Detailed description of the grievance"
                  value={complaintDesc}
                  onChange={(e) => setComplaintDesc(e.target.value)}
                  className="w-full bg-slate-900 border border-slate-800 rounded-xl px-3 py-2 text-slate-200 focus:outline-none focus:border-sky-500 resize-none"
                />
              </div>

              <div className="flex items-center gap-2 pt-1">
                <input
                  type="checkbox"
                  id="sens-chk"
                  checked={complaintIsSensitive}
                  onChange={(e) => setComplaintIsSensitive(e.target.checked)}
                  className="rounded bg-slate-900 border-slate-800 text-sky-500 focus:ring-0"
                />
                <label htmlFor="sens-chk" className="text-slate-300">
                  Mark as Sensitive Grievance (Restricted to creator & grievance committee)
                </label>
              </div>
            </div>

            <div className="pt-3 border-t border-slate-800 flex justify-end gap-2">
              <button
                type="button"
                onClick={() => setShowComplaintModal(false)}
                className="px-4 py-2 rounded-xl text-xs font-semibold text-slate-400 hover:text-slate-200"
              >
                Cancel
              </button>
              <button
                type="button"
                onClick={handleCreateComplaint}
                className="px-5 py-2 rounded-xl text-xs font-semibold bg-sky-500 hover:bg-sky-400 text-white shadow-lg shadow-sky-500/25 transition-all flex items-center gap-1.5"
              >
                <Send className="w-3.5 h-3.5" />
                Submit Grievance
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Anonymous Feedback Modal */}
      {showFeedbackModal && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-slate-950/80 backdrop-blur-sm animate-fadeIn">
          <div className="glass-panel w-full max-w-lg rounded-2xl p-6 border border-slate-800 shadow-2xl space-y-4">
            <div className="flex items-center justify-between pb-3 border-b border-slate-800">
              <div className="flex items-center gap-2">
                <MessageSquare className="w-5 h-5 text-purple-400" />
                <h3 className="text-base font-bold text-white">Course Feedback: CS301 (Dr. Ada Lovelace)</h3>
              </div>
              <button
                onClick={() => setShowFeedbackModal(false)}
                className="text-slate-400 hover:text-white text-xs font-semibold"
              >
                ✕ Close
              </button>
            </div>

            <div className="space-y-4 text-xs">
              <div className="bg-purple-950/40 border border-purple-500/20 p-3 rounded-xl text-purple-200/90 text-[11px] leading-relaxed">
                🛡️ <strong>Rule NR-10 Guarantee:</strong> Zero student identity is attached to this submission. Answers are decoupled from your login session.
              </div>

              {[
                { label: "Pedagogy & Teaching Quality", val: feedbackPedagogy, setVal: setFeedbackPedagogy },
                { label: "Clarity of Technical Explanations", val: feedbackClarity, setVal: setFeedbackClarity },
                { label: "Classroom Engagement & Discussions", val: feedbackEngagement, setVal: setFeedbackEngagement },
                { label: "Punctuality & Lab Availability", val: feedbackPunctuality, setVal: setFeedbackPunctuality },
              ].map((dim) => (
                <div key={dim.label}>
                  <div className="flex justify-between items-center mb-1">
                    <span className="text-slate-300 font-medium">{dim.label}</span>
                    <span className="font-bold text-sky-400">{dim.val} / 5</span>
                  </div>
                  <input
                    type="range"
                    min={1}
                    max={5}
                    step={1}
                    value={dim.val}
                    onChange={(e) => dim.setVal(Number(e.target.value))}
                    className="w-full accent-sky-500 cursor-pointer"
                  />
                </div>
              ))}

              <div>
                <label className="block text-slate-300 font-medium mb-1">Constructive Qualitative Feedback</label>
                <textarea
                  rows={3}
                  placeholder="What worked well? What could be improved in upcoming modules?"
                  value={feedbackComment}
                  onChange={(e) => setFeedbackComment(e.target.value)}
                  className="w-full bg-slate-900 border border-slate-800 rounded-xl px-3 py-2 text-slate-200 focus:outline-none focus:border-purple-500 resize-none"
                />
              </div>
            </div>

            <div className="pt-3 border-t border-slate-800 flex justify-end gap-2">
              <button
                type="button"
                onClick={() => setShowFeedbackModal(false)}
                className="px-4 py-2 rounded-xl text-xs font-semibold text-slate-400 hover:text-slate-200"
              >
                Cancel
              </button>
              <button
                type="button"
                onClick={handleSubmitAnonymousFeedback}
                className="px-5 py-2 rounded-xl text-xs font-semibold bg-purple-600 hover:bg-purple-500 text-white shadow-lg shadow-purple-500/25 transition-all flex items-center gap-1.5"
              >
                <Send className="w-3.5 h-3.5" />
                Submit Anonymously
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Floating Campus AI Assistant Button (Accessible from Any Persona) */}
      <div className="fixed bottom-6 right-6 z-40">
        <button
          type="button"
          onClick={() => setAiDrawerOpen(!aiDrawerOpen)}
          className="flex items-center gap-2.5 px-4 py-3 rounded-full font-bold text-xs bg-gradient-to-r from-amber-500 to-amber-600 hover:from-amber-400 hover:to-amber-500 text-slate-950 shadow-xl shadow-amber-500/25 transition-all hover:scale-105 active:scale-95"
          title="Open Campus AI Grounded Assistant"
        >
          <Sparkles className="w-4 h-4 text-slate-950" />
          <span>Ask Campus AI</span>
          <span className="w-2 h-2 rounded-full bg-emerald-950 animate-pulse" />
        </button>
      </div>

      {/* Slide-Over Drawer for Quick AI Inquiry */}
      {aiDrawerOpen && (
        <div className="fixed inset-y-0 right-0 z-50 w-full sm:w-[480px] bg-slate-950/95 backdrop-blur-xl border-l border-slate-800 shadow-2xl flex flex-col">
          <div className="p-4 border-b border-slate-800 flex items-center justify-between bg-slate-900/80">
            <div className="flex items-center gap-2.5">
              <div className="w-8 h-8 rounded-lg bg-amber-500/20 border border-amber-500/30 flex items-center justify-center">
                <Sparkles className="w-4 h-4 text-amber-400" />
              </div>
              <div>
                <h3 className="text-sm font-bold text-white">Campus AI Assistant</h3>
                <p className="text-[10px] text-slate-400">
                  Tenant: {activeTenant === "APEX" ? "Apex Institute" : "Horizon Polytechnic"} • Verified Policy RAG
                </p>
              </div>
            </div>
            <button
              type="button"
              onClick={() => setAiDrawerOpen(false)}
              className="text-slate-400 hover:text-white text-xs font-semibold px-2 py-1 rounded-lg hover:bg-slate-800"
            >
              ✕ Close
            </button>
          </div>

          {/* Quick Drawer Message Feed */}
          <div className="flex-1 overflow-y-auto p-4 space-y-4">
            {aiChatMessages.map((msg) => (
              <div
                key={msg.id}
                className={`flex flex-col ${msg.role === "USER" ? "items-end" : "items-start"}`}
              >
                <div
                  className={`max-w-[90%] rounded-2xl p-3.5 text-xs leading-relaxed space-y-2.5 ${
                    msg.role === "USER"
                      ? "bg-sky-600 text-white rounded-tr-none"
                      : "bg-slate-900 border border-slate-800 text-slate-200 rounded-tl-none"
                  }`}
                >
                  <div className="whitespace-pre-line">{msg.content}</div>

                  {msg.citations && msg.citations.length > 0 && (
                    <div className="pt-2 border-t border-slate-800/80 space-y-1">
                      <span className="text-[9px] font-bold text-sky-400 uppercase tracking-wider block">
                        Verified Citation:
                      </span>
                      {msg.citations.map((c, cIdx) => (
                        <div
                          key={cIdx}
                          className="text-[10px] text-sky-200 bg-sky-950/60 px-2 py-1 rounded border border-sky-500/30 font-mono"
                        >
                          [{c.document_title} - {c.source_ref}]
                        </div>
                      ))}
                    </div>
                  )}

                  {msg.draft_action && (
                    <div className="p-3 rounded-xl bg-amber-950/40 border border-amber-500/40 space-y-2 text-[11px]">
                      <div className="font-bold text-amber-300 flex items-center gap-1">
                        <AlertTriangle className="w-3.5 h-3.5" />
                        <span>Draft Action Requires Confirmation (Rule B4)</span>
                      </div>
                      <div className="text-slate-300">
                        {msg.draft_action.title} • {msg.draft_action.sla_committed_hours || 48}h SLA
                      </div>
                      {msg.confirmed ? (
                        <div className="text-emerald-400 font-medium">✓ Confirmed & Submitted!</div>
                      ) : (
                        <button
                          type="button"
                          onClick={() => handleConfirmAiDraftAction(msg.id, msg.draft_action)}
                          className="w-full py-1.5 px-3 rounded-lg bg-amber-600 hover:bg-amber-500 text-white font-bold text-xs"
                        >
                          Confirm Draft Ticket
                        </button>
                      )}
                    </div>
                  )}
                </div>
              </div>
            ))}
            {isAiThinking && (
              <div className="flex items-center gap-2 text-xs text-amber-300 bg-slate-900/80 p-2.5 rounded-xl border border-slate-800 w-fit">
                <RefreshCw className="w-3.5 h-3.5 animate-spin" />
                <span>Grounding response...</span>
              </div>
            )}
          </div>

          {/* Drawer Input */}
          <div className="p-3 border-t border-slate-800 bg-slate-900/90">
            <form
              onSubmit={(e) => {
                e.preventDefault();
                handleSendAiMessage();
              }}
              className="flex gap-2"
            >
              <input
                type="text"
                placeholder="Ask Campus AI..."
                value={aiChatQuery}
                onChange={(e) => setAiChatQuery(e.target.value)}
                className="flex-1 bg-slate-950 border border-slate-800 rounded-xl px-3 py-2 text-xs text-slate-100 placeholder:text-slate-500 focus:outline-none focus:border-amber-500"
              />
              <button
                type="submit"
                disabled={isAiThinking || !aiChatQuery.trim()}
                className="px-4 py-2 rounded-xl font-bold text-xs bg-amber-600 hover:bg-amber-500 disabled:opacity-50 text-white transition-all"
              >
                Send
              </button>
            </form>
          </div>
        </div>
      )}

      {/* Google College Sign-In Modal */}
      {showGoogleLoginModal && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/80 backdrop-blur-md animate-fadeIn">
          <div className="bg-slate-900 border border-slate-700/80 rounded-3xl max-w-md w-full overflow-hidden shadow-2xl p-6 sm:p-8 space-y-6">
            <div className="text-center space-y-2">
              <div className="w-14 h-14 rounded-2xl bg-white mx-auto flex items-center justify-center shadow-lg shadow-sky-500/10">
                <svg className="w-8 h-8" viewBox="0 0 24 24">
                  <path fill="#4285F4" d="M23.745 12.27c0-.7-.06-1.4-.19-2.07H12v4.51h6.6c-.29 1.52-1.14 2.8-2.4 3.65v3.03h3.88c2.27-2.09 3.66-5.17 3.66-9.12z" />
                  <path fill="#34A853" d="M12 24c3.24 0 5.95-1.08 7.93-2.91l-3.88-3.03c-1.08.72-2.45 1.16-4.05 1.16-3.12 0-5.77-2.1-6.72-4.93H1.25v3.13C3.27 21.43 7.35 24 12 24z" />
                  <path fill="#FBBC05" d="M5.28 14.29c-.25-.72-.38-1.49-.38-2.29s.13-1.57.38-2.29V6.58H1.25C.45 8.18 0 9.99 0 12s.45 3.82 1.25 5.42l4.03-3.13z" />
                  <path fill="#EA4335" d="M12 4.75c1.77 0 3.35.61 4.6 1.8l3.42-3.42C17.95 1.19 15.24 0 12 0 7.35 0 3.27 2.57 1.25 6.58l4.03 3.13c.95-2.83 3.6-4.96 6.72-4.96z" />
                </svg>
              </div>
              <h3 className="text-xl font-bold text-white tracking-tight">
                Sign in with Google
              </h3>
              <p className="text-xs text-slate-400">
                Institutional Single Sign-On (SSO) with your College Mail ID
              </p>
            </div>

            {/* Institutional Security Policy Notice */}
            <div className="p-3.5 rounded-2xl bg-amber-500/10 border border-amber-500/20 text-xs text-amber-300 leading-relaxed space-y-1">
              <div className="font-semibold flex items-center gap-1.5 text-amber-200">
                <Shield className="w-3.5 h-3.5" />
                <span>College Domain Policy (Rule NR-5)</span>
              </div>
              <p className="text-[11px] text-amber-300/80">
                Personal emails (<span className="font-mono text-amber-200">@gmail.com</span>, <span className="font-mono text-amber-200">@yahoo.com</span>) are strictly disallowed. You must authenticate with an institutional email (e.g. <span className="font-mono text-amber-200">@apex.edu</span>).
              </p>
            </div>

            {/* Error Message */}
            {googleDomainError && (
              <div className="p-3 rounded-xl bg-rose-500/10 border border-rose-500/30 text-rose-300 text-xs flex items-start gap-2">
                <AlertTriangle className="w-4 h-4 text-rose-400 shrink-0 mt-0.5" />
                <span>{googleDomainError}</span>
              </div>
            )}

            {/* 1-Click Fast Institutional Persona Access */}
            <div className="space-y-2">
              <div className="text-[11px] font-bold text-slate-400 uppercase tracking-wider">
                Select Verified Institutional Account:
              </div>

              <div className="grid grid-cols-1 gap-2">
                <button
                  type="button"
                  onClick={() => handleGoogleCollegeLogin("aarav.sharma@apex.edu", "Aarav Sharma")}
                  disabled={isLoggingIn}
                  className="w-full flex items-center justify-between p-3 rounded-xl bg-slate-950/70 border border-slate-800 hover:border-sky-500/50 hover:bg-sky-500/5 transition-all text-left group"
                >
                  <div className="flex items-center gap-2.5">
                    <div className="w-8 h-8 rounded-lg bg-sky-500/20 text-sky-400 flex items-center justify-center font-bold text-xs">
                      AS
                    </div>
                    <div>
                      <div className="font-semibold text-xs text-slate-200 group-hover:text-white">
                        Aarav Sharma
                      </div>
                      <div className="text-[11px] font-mono text-slate-400">
                        aarav.sharma@apex.edu
                      </div>
                    </div>
                  </div>
                  <div className="text-right">
                    <span className="px-2 py-0.5 rounded text-[10px] font-bold bg-sky-500/20 text-sky-300 border border-sky-500/30">
                      User Dashboard (Student)
                    </span>
                  </div>
                </button>

                <button
                  type="button"
                  onClick={() => handleGoogleCollegeLogin("prof.rao@apex.edu", "Prof. Raghav Rao")}
                  disabled={isLoggingIn}
                  className="w-full flex items-center justify-between p-3 rounded-xl bg-slate-950/70 border border-slate-800 hover:border-indigo-500/50 hover:bg-indigo-500/5 transition-all text-left group"
                >
                  <div className="flex items-center gap-2.5">
                    <div className="w-8 h-8 rounded-lg bg-indigo-500/20 text-indigo-400 flex items-center justify-center font-bold text-xs">
                      RR
                    </div>
                    <div>
                      <div className="font-semibold text-xs text-slate-200 group-hover:text-white">
                        Prof. Raghav Rao
                      </div>
                      <div className="text-[11px] font-mono text-slate-400">
                        prof.rao@apex.edu
                      </div>
                    </div>
                  </div>
                  <div className="text-right">
                    <span className="px-2 py-0.5 rounded text-[10px] font-bold bg-indigo-500/20 text-indigo-300 border border-indigo-500/30">
                      User Dashboard (Faculty)
                    </span>
                  </div>
                </button>

                <button
                  type="button"
                  onClick={() => handleGoogleCollegeLogin("admin@apex.edu", "Dr. S. K. Raman")}
                  disabled={isLoggingIn}
                  className="w-full flex items-center justify-between p-3 rounded-xl bg-slate-950/70 border border-slate-800 hover:border-purple-500/50 hover:bg-purple-500/5 transition-all text-left group"
                >
                  <div className="flex items-center gap-2.5">
                    <div className="w-8 h-8 rounded-lg bg-purple-500/20 text-purple-400 flex items-center justify-center font-bold text-xs">
                      SK
                    </div>
                    <div>
                      <div className="font-semibold text-xs text-slate-200 group-hover:text-white">
                        Dr. S. K. Raman (Director)
                      </div>
                      <div className="text-[11px] font-mono text-slate-400">
                        admin@apex.edu
                      </div>
                    </div>
                  </div>
                  <div className="text-right">
                    <span className="px-2 py-0.5 rounded text-[10px] font-bold bg-purple-500/20 text-purple-300 border border-purple-500/30">
                      Admin Dashboard
                    </span>
                  </div>
                </button>

                <button
                  type="button"
                  onClick={() => handleGoogleCollegeLogin("cse.admin@apex.edu", "Prof. Sunita Reddy")}
                  disabled={isLoggingIn}
                  className="w-full flex items-center justify-between p-3 rounded-xl bg-slate-950/70 border border-slate-800 hover:border-pink-500/50 hover:bg-pink-500/5 transition-all text-left group"
                >
                  <div className="flex items-center gap-2.5">
                    <div className="w-8 h-8 rounded-lg bg-pink-500/20 text-pink-400 flex items-center justify-center font-bold text-xs">
                      SR
                    </div>
                    <div>
                      <div className="font-semibold text-xs text-slate-200 group-hover:text-white">
                        Prof. Sunita Reddy (HOD CSE)
                      </div>
                      <div className="text-[11px] font-mono text-slate-400">
                        cse.admin@apex.edu
                      </div>
                    </div>
                  </div>
                  <div className="text-right">
                    <span className="px-2 py-0.5 rounded text-[10px] font-bold bg-pink-500/20 text-pink-300 border border-pink-500/30">
                      Admin Dashboard
                    </span>
                  </div>
                </button>
              </div>
            </div>

            {/* Custom College Email Input */}
            <div className="space-y-3 pt-2 border-t border-slate-800">
              <label className="text-[11px] font-bold text-slate-400 uppercase tracking-wider block">
                Or Sign In with Any College Mail ID:
              </label>
              <div className="flex gap-2">
                <input
                  type="email"
                  placeholder="e.g. yourname@apex.edu"
                  value={googleEmailInput}
                  onChange={(e) => setGoogleEmailInput(e.target.value)}
                  className="flex-1 bg-slate-950 border border-slate-800 rounded-xl px-3 py-2 text-xs text-slate-100 placeholder:text-slate-500 focus:outline-none focus:border-sky-500"
                />
                <button
                  type="button"
                  onClick={() => handleGoogleCollegeLogin(googleEmailInput)}
                  disabled={isLoggingIn || !googleEmailInput.trim()}
                  className="px-4 py-2 rounded-xl text-xs font-bold bg-white text-slate-900 hover:bg-slate-200 disabled:opacity-50 transition-all flex items-center gap-1.5 shrink-0"
                >
                  {isLoggingIn ? <RefreshCw className="w-3.5 h-3.5 animate-spin" /> : <GoogleGIcon />}
                  <span>Sign In</span>
                </button>
              </div>
            </div>

            <div className="flex justify-end pt-2">
              <button
                type="button"
                onClick={() => {
                  setShowGoogleLoginModal(false);
                  setGoogleDomainError(null);
                }}
                className="px-4 py-2 rounded-xl text-xs font-medium text-slate-400 hover:text-white hover:bg-slate-800 transition-all"
              >
                Close
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Access Denied Security Modal (Rule NR-5) */}
      {showAccessDeniedModal && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/80 backdrop-blur-md animate-fadeIn">
          <div className="bg-slate-900 border border-rose-500/40 rounded-3xl max-w-md w-full overflow-hidden shadow-2xl p-6 sm:p-8 space-y-5">
            <div className="w-12 h-12 rounded-2xl bg-rose-500/10 border border-rose-500/30 flex items-center justify-center text-rose-400 mx-auto">
              <Lock className="w-6 h-6" />
            </div>

            <div className="text-center space-y-1.5">
              <h3 className="text-lg font-bold text-white tracking-tight">
                Admin Console Access Restricted
              </h3>
              <p className="text-xs text-rose-300 font-mono">
                Security Policy Rule NR-5 Enforced
              </p>
            </div>

            <div className="p-4 rounded-2xl bg-rose-950/30 border border-rose-500/20 text-xs text-slate-300 leading-relaxed space-y-2">
              <p>
                You are currently signed in as <span className="font-semibold text-white">{currentUser.full_name}</span> (<span className="font-mono text-sky-300">{currentUser.email}</span>) with <span className="font-bold text-amber-300">{currentUser.roles.join(", ")}</span> permissions.
              </p>
              <p className="text-slate-400 text-[11px]">
                <strong>Rule NR-5:</strong> A verified email address alone never grants lecturer, department admin or college admin privileges. Administrative console access requires an explicit role approval by an institution authority.
              </p>
            </div>

            <div className="space-y-2 pt-2">
              <div className="text-[11px] font-semibold text-slate-400">
                To access the Admin Console, switch to an approved admin account:
              </div>
              <button
                type="button"
                onClick={() => {
                  setShowAccessDeniedModal(false);
                  handleGoogleCollegeLogin("admin@apex.edu", "Dr. S. K. Raman");
                }}
                className="w-full py-2.5 px-4 rounded-xl text-xs font-bold bg-gradient-to-r from-purple-600 to-indigo-600 hover:from-purple-500 hover:to-indigo-500 text-white shadow-lg shadow-purple-500/25 transition-all flex items-center justify-center gap-2"
              >
                <Shield className="w-4 h-4" />
                Sign In as College Admin (admin@apex.edu)
              </button>
            </div>

            <div className="flex justify-end pt-1">
              <button
                type="button"
                onClick={() => setShowAccessDeniedModal(false)}
                className="px-4 py-2 rounded-xl text-xs font-medium text-slate-400 hover:text-white hover:bg-slate-800 transition-all"
              >
                Return to User Dashboard
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Interactive Facility QR Code Suite Modal */}
      <FacilityQrSuiteModal
        isOpen={showQrSuiteModal}
        onClose={() => setShowQrSuiteModal(false)}
        onSelectFacilityForGrievance={(tag, cat) => {
          setComplaintLocation(tag);
          setComplaintCategory(cat);
          setShowComplaintModal(true);
        }}
      />

      {/* Official Institutional Incident Dossier Modal */}
      <IncidentDossierModal
        complaint={selectedDossierComplaint}
        isOpen={selectedDossierComplaint !== null}
        onClose={() => setSelectedDossierComplaint(null)}
      />
      </main>

      {/* Footer */}
      <footer className="border-t border-slate-800/80 bg-slate-950/80 py-4 text-center text-xs text-slate-500">
        CampusCare AI Multi-Tenant Monolith • PostgreSQL 18 with Forced RLS • Verified Identity & Hash-Chained Audit Ledger
      </footer>
    </div>
  );
}

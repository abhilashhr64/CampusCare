// OpenAPI-generated TypeScript client contract for CampusCare AI

export interface College {
  id: string;
  name: string;
  code: string;
  domain: string;
  is_active: boolean;
  settings: Record<string, any>;
}

export interface User {
  id: string;
  college_id: string;
  email: string;
  full_name: string;
  is_email_verified: boolean;
  is_mfa_enabled: boolean;
  roles: string[];
  role_scopes: Record<string, any>;
}

export interface TokenResponse {
  session_token: string;
  expires_at: string;
  user: User;
}

export interface RoleGrant {
  id: string;
  college_id: string;
  user_id: string;
  role: string;
  scope: Record<string, any>;
  granted_by: string | null;
  reason: string;
  expires_at: string | null;
  is_revoked: boolean;
  created_at: string;
}

export interface Department {
  id: string;
  college_id: string;
  code: string;
  name: string;
  created_at: string;
}

export interface Course {
  id: string;
  college_id: string;
  department_id: string;
  code: string;
  title: string;
  credits: number;
  created_at: string;
}

export interface ClassSection {
  id: string;
  college_id: string;
  course_id: string;
  lecturer_id: string | null;
  section_name: string;
  semester: number;
  academic_year: string;
  created_at: string;
}

export interface Complaint {
  id: string;
  college_id: string;
  ticket_number: string;
  creator_id: string;
  category: string;
  title: string;
  description: string;
  location_tag: string | null;
  is_sensitive: boolean;
  status: string;
  assigned_to_user_id: string | null;
  assigned_department_id: string | null;
  sla_committed_hours: number;
  sla_deadline: string;
  resolved_at: string | null;
  closed_at: string | null;
  student_confirmed: boolean | null;
  student_feedback_rating: number | null;
  student_feedback_comment: string | null;
  created_at: string;
  updated_at: string;
}

export interface FeedbackCycle {
  id: string;
  college_id: string;
  title: string;
  academic_term: string;
  is_active: boolean;
  k_anonymity_threshold: number;
  created_at: string;
}

export interface FeedbackAggregate {
  lecturer_id: string;
  cycle_id: string;
  response_count: number;
  k_anonymity_met: boolean;
  k_threshold: number;
  avg_pedagogy: number | null;
  avg_clarity: number | null;
  avg_engagement: number | null;
  avg_punctuality: number | null;
  overall_rating: number | null;
  qualitative_summary: string | null;
}

export interface AttendanceSession {
  id: string;
  class_section_id: string;
  lecturer_id: string;
  session_date: string;
  start_time: string;
  end_time: string;
  topic: string | null;
  version: number;
  created_at: string;
}

export interface SyncOutcome {
  op_id: string;
  outcome: "applied" | "duplicate" | "conflict" | "rejected";
  reason?: string;
  server_version?: number;
  server_records?: Array<{ student_id: string; status: string }>;
}

const API_BASE = process.env.NEXT_PUBLIC_API_URL || "http://127.0.0.1:8000/api/v1";

async function request<T>(endpoint: string, options: RequestInit = {}): Promise<T> {
  const token = typeof window !== "undefined" ? localStorage.getItem("campuscare_token") : null;
  const headers: Record<string, string> = {
    "Content-Type": "application/json",
    ...(options.headers as Record<string, string>),
  };

  if (token) {
    headers["Authorization"] = `Bearer ${token}`;
  }

  const response = await fetch(`${API_BASE}${endpoint}`, {
    ...options,
    headers,
    credentials: "include",
  });

  if (!response.ok) {
    let errorDetail = "An unexpected error occurred.";
    try {
      const errJson = await response.json();
      errorDetail = errJson.detail || errorDetail;
    } catch {
      // response was not JSON
    }
    throw new Error(errorDetail);
  }

  return response.json();
}

export const api = {
  system: {
    health: () => request<{ status: string; service: string; version: string }>("/system/health"),
  },
  tenancy: {
    listColleges: () => request<College[]>("/tenancy/colleges"),
  },
  auth: {
    signupStudent: (data: { college_id: string; email: string; full_name: string; password: string }) =>
      request<{ message: string; user_id: string; synthetic_verification_code: string }>("/auth/signup-student", {
        method: "POST",
        body: JSON.stringify(data),
      }),
    verifyCode: (data: { college_id: string; email: string; code: string }) =>
      request<{ message: string }>("/auth/verify-code", {
        method: "POST",
        body: JSON.stringify(data),
      }),
    login: (data: { college_id: string; email: string; password: string }) =>
      request<TokenResponse>("/auth/login", {
        method: "POST",
        body: JSON.stringify(data),
      }),
    logout: () =>
      request<{ message: string }>("/auth/logout", {
        method: "POST",
      }),
    getMe: () => request<User>("/auth/me"),
  },
  access: {
    listGrants: () => request<RoleGrant[]>("/access/grants"),
    grantRole: (data: { user_id: string; role: string; scope?: Record<string, any>; reason: string; expires_at?: string }) =>
      request<RoleGrant>("/access/grants", {
        method: "POST",
        body: JSON.stringify(data),
      }),
    revokeRole: (grantId: string, reason: string) =>
      request<RoleGrant>(`/access/grants/${grantId}/revoke`, {
        method: "POST",
        body: JSON.stringify({ reason }),
      }),
  },
  directory: {
    listDepartments: () => request<Department[]>("/directory/departments"),
    createDepartment: (data: { code: string; name: string }) =>
      request<Department>("/directory/departments", {
        method: "POST",
        body: JSON.stringify(data),
      }),
    listCourses: (departmentId?: string) =>
      request<Course[]>(`/directory/courses${departmentId ? `?department_id=${departmentId}` : ""}`),
    createCourse: (data: { department_id: string; code: string; title: string; credits?: number }) =>
      request<Course>("/directory/courses", {
        method: "POST",
        body: JSON.stringify(data),
      }),
    listClasses: (lecturerId?: string) =>
      request<ClassSection[]>(`/directory/classes${lecturerId ? `?lecturer_id=${lecturerId}` : ""}`),
  },
  complaints: {
    list: (category?: string, status?: string) => {
      const params = new URLSearchParams();
      if (category) params.append("category", category);
      if (status) params.append("status", status);
      const query = params.toString();
      return request<Complaint[]>(`/complaints${query ? `?${query}` : ""}`);
    },
    create: (data: {
      category: string;
      title: string;
      description: string;
      location_tag?: string;
      is_sensitive?: boolean;
      sla_committed_hours?: number;
    }) =>
      request<Complaint>("/complaints", {
        method: "POST",
        body: JSON.stringify(data),
      }),
    get: (id: string) => request<Complaint>(`/complaints/${id}`),
    assign: (id: string, data: { assigned_to_user_id?: string; assigned_department_id?: string; comment?: string }) =>
      request<Complaint>(`/complaints/${id}/assign`, {
        method: "POST",
        body: JSON.stringify(data),
      }),
    resolve: (id: string, data: { resolution_note: string }) =>
      request<Complaint>(`/complaints/${id}/resolve`, {
        method: "POST",
        body: JSON.stringify(data),
      }),
    confirm: (id: string, data: { student_confirmed: boolean; feedback_rating?: number; feedback_comment?: string }) =>
      request<Complaint>(`/complaints/${id}/confirm`, {
        method: "POST",
        body: JSON.stringify(data),
      }),
  },
  feedback: {
    listCycles: () => request<FeedbackCycle[]>("/feedback/cycles"),
    createCycle: (data: { title: string; academic_term: string; k_anonymity_threshold?: number }) =>
      request<FeedbackCycle>("/feedback/cycles", {
        method: "POST",
        body: JSON.stringify(data),
      }),
    submit: (data: {
      cycle_id: string;
      class_section_id: string;
      course_id: string;
      lecturer_id: string;
      rating_pedagogy: number;
      rating_clarity: number;
      rating_engagement: number;
      rating_punctuality: number;
      comment?: string;
    }) =>
      request<{ status: string; message: string }>("/feedback/submit", {
        method: "POST",
        body: JSON.stringify(data),
      }),
    getAggregates: (cycleId: string, lecturerId: string) =>
      request<FeedbackAggregate>(`/feedback/aggregates?cycle_id=${cycleId}&lecturer_id=${lecturerId}`),
  },
  attendance: {
    createSession: (data: {
      class_section_id: string;
      session_date: string;
      start_time: string;
      end_time: string;
      topic?: string;
    }) =>
      request<AttendanceSession>("/attendance/sessions", {
        method: "POST",
        body: JSON.stringify(data),
      }),
    syncBatch: (
      batch: Array<{
        op_id: string;
        session_id: string;
        class_section_id: string;
        base_version: number;
        student_records: Array<{ student_id: string; status: string }>;
      }>
    ) =>
      request<SyncOutcome[]>("/attendance/sync-batch", {
        method: "POST",
        body: JSON.stringify(batch),
      }),
    getStudentSummary: () => request<any>("/attendance/summary/me"),
    getWhatIf: (conducted: number, attended: number, target_percentage?: number) =>
      request<any>(
        `/attendance/what-if?conducted=${conducted}&attended=${attended}${
          target_percentage ? `&target_percentage=${target_percentage}` : ""
        }`
      ),
  },
};


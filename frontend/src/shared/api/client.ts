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
};

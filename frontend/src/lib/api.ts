/**
 * MediSync AI — Axios API Client
 * Centralised HTTP client with JWT auth interceptor.
 */
import axios, { type AxiosInstance, type InternalAxiosRequestConfig } from "axios";

const BASE_URL =
  typeof window !== "undefined"
    ? "/api" // browser → proxy via next.config.ts rewrites
    : process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000/api";

export const apiClient: AxiosInstance = axios.create({
  baseURL: BASE_URL,
  headers: { "Content-Type": "application/json" },
  timeout: 15_000,
});

// ── Request interceptor — attach Bearer token ─────────────────────────────────

apiClient.interceptors.request.use((config: InternalAxiosRequestConfig) => {
  if (typeof window !== "undefined") {
    const token = localStorage.getItem("access_token");
    if (token) {
      config.headers.Authorization = `Bearer ${token}`;
    }
  }
  return config;
});

// ── Response interceptor — handle 401 globally ───────────────────────────────

apiClient.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response?.status === 401 && typeof window !== "undefined") {
      localStorage.removeItem("access_token");
      window.location.href = "/login";
    }
    return Promise.reject(error);
  }
);

// ─────────────────────────────────────────────────────────────────────────────
// Auth API
// ─────────────────────────────────────────────────────────────────────────────

export const authApi = {
  /** Authenticate and obtain JWT token (OAuth2 form format). */
  login: async (email: string, password: string) => {
    const form = new URLSearchParams();
    form.append("username", email);
    form.append("password", password);
    const { data } = await apiClient.post<{ access_token: string; token_type: string }>(
      "/auth/login",
      form,
      { headers: { "Content-Type": "application/x-www-form-urlencoded" } }
    );
    return data;
  },

  register: async (email: string, password: string, role: string) => {
    const { data } = await apiClient.post("/auth/register", { email, password, role });
    return data;
  },
};

// ─────────────────────────────────────────────────────────────────────────────
// Admin API
// ─────────────────────────────────────────────────────────────────────────────

export const adminApi = {
  getStats: async () => {
    const { data } = await apiClient.get("/admin/stats");
    return data;
  },
  listDoctors: async () => {
    const { data } = await apiClient.get("/admin/doctors");
    return data;
  },
  listPatients: async (skip = 0, limit = 20) => {
    const { data } = await apiClient.get(`/admin/patients?skip=${skip}&limit=${limit}`);
    return data;
  },
  listQueues: async (poli?: string, status?: string) => {
    const params = new URLSearchParams();
    if (poli) params.append("poli_name", poli);
    if (status) params.append("status", status);
    const { data } = await apiClient.get(`/admin/queues?${params}`);
    return data;
  },
};

// ─────────────────────────────────────────────────────────────────────────────
// Doctor API
// ─────────────────────────────────────────────────────────────────────────────

export const doctorApi = {
  /** List all patients — doctors need this to create encounters. */
  listPatients: async () => {
    const { data } = await apiClient.get("/doctor/patients");
    return data;
  },
  getMyEncounters: async () => {
    const { data } = await apiClient.get("/doctor/encounters");
    return data;
  },
  createEncounter: async (payload: {
    patient_id: string;
    complaint_text?: string;
    tabular_metrics_json?: Record<string, number>;
  }) => {
    const { data } = await apiClient.post("/doctor/encounters", payload);
    return data;
  },
  runPrediction: async (payload: {
    encounter_id: string;
    run_tabular: boolean;
    run_nlp: boolean;
    run_vision: boolean;
  }) => {
    const { data } = await apiClient.post("/doctor/predict", payload);
    return data;
  },
  createTreatmentPlan: async (
    encounterId: string,
    payload: {
      diagnosis?: string;
      prescription_drugs?: unknown[];
      behavioral_advice?: string;
      ews_level?: number;
    }
  ) => {
    const { data } = await apiClient.post(
      `/doctor/encounters/${encounterId}/treatment-plan`,
      payload
    );
    return data;
  },
  generateReport: async (encounterId: string) => {
    const { data } = await apiClient.post(
      `/doctor/encounters/${encounterId}/generate-report`
    );
    return data;
  },
  approveReport: async (reportId: string, approved: boolean) => {
    const { data } = await apiClient.patch(`/doctor/reports/${reportId}/approve`, {
      approved,
    });
    return data;
  },
};

// ─────────────────────────────────────────────────────────────────────────────
// Patient API
// ─────────────────────────────────────────────────────────────────────────────

export const patientApi = {
  getProfile: async () => {
    const { data } = await apiClient.get("/patient/profile");
    return data;
  },
  createProfile: async (payload: {
    nik: string;
    full_name: string;
    dob: string;
    gender: string;
    phone?: string;
  }) => {
    const { data } = await apiClient.post("/patient/profile", payload);
    return data;
  },
  getMyQueue: async () => {
    const { data } = await apiClient.get("/patient/queue");
    return data;
  },
  getMyEncounters: async () => {
    const { data } = await apiClient.get("/patient/encounters");
    return data;
  },
  getMyReports: async () => {
    const { data } = await apiClient.get("/patient/reports");
    return data;
  },
  getReport: async (reportId: string) => {
    const { data } = await apiClient.get(`/patient/reports/${reportId}`);
    return data;
  },
};

// ─────────────────────────────────────────────────────────────────────────────
// Queue API
// ─────────────────────────────────────────────────────────────────────────────

export const queueApi = {
  createEntry: async (payload: {
    patient_id: string;
    doctor_id?: string;
    poli_name: string;
  }) => {
    const { data } = await apiClient.post("/queue/", payload);
    return data;
  },
  updateStatus: async (queueId: string, status: string) => {
    const { data } = await apiClient.patch(`/queue/${queueId}/status`, { status });
    return data;
  },
  getPoliQueue: async (poliName: string) => {
    const { data } = await apiClient.get(`/queue/poli/${encodeURIComponent(poliName)}`);
    return data;
  },
};

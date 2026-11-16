/**
 * MediSync AI — TypeScript type definitions
 * Mirrors the Pydantic schemas from the FastAPI backend.
 */

// ── Auth ──────────────────────────────────────────────────────────────────────

export interface TokenResponse {
  access_token: string;
  token_type: string;
}

export interface LoginRequest {
  email: string;
  password: string;
}

// ── Users ─────────────────────────────────────────────────────────────────────

export type UserRole = "admin" | "doctor" | "patient";

export interface User {
  id: string;
  email: string;
  role: UserRole;
  is_active: boolean;
  created_at: string;
}

// ── Patients ──────────────────────────────────────────────────────────────────

export type Gender = "male" | "female";

export interface Patient {
  id: string;
  user_id: string;
  nik: string;
  full_name: string;
  dob: string;
  gender: Gender;
  phone: string | null;
  medical_history_json: Record<string, unknown> | null;
}

export interface PatientCreate {
  nik: string;
  full_name: string;
  dob: string;
  gender: Gender;
  phone?: string;
  medical_history_json?: Record<string, unknown>;
}

// ── Doctors ───────────────────────────────────────────────────────────────────

export type DoctorStatus = "available" | "busy" | "off";

export interface Doctor {
  id: string;
  user_id: string;
  specialization: string;
  license_number: string;
  room_number: string | null;
  status: DoctorStatus;
}

// ── Queues ────────────────────────────────────────────────────────────────────

export type QueueStatus = "waiting" | "serving" | "done" | "cancelled";

export interface Queue {
  id: string;
  patient_id: string;
  doctor_id: string | null;
  poli_name: string;
  queue_number: number;
  status: QueueStatus;
  created_at: string;
  updated_at: string;
}

export interface QueueCreate {
  patient_id: string;
  doctor_id?: string;
  poli_name: string;
}

// ── Medical Encounters ────────────────────────────────────────────────────────

export type EncounterStatus = "open" | "closed" | "pending_report";

export interface Encounter {
  id: string;
  patient_id: string;
  doctor_id: string | null;
  complaint_text: string | null;
  tabular_metrics_json: Record<string, number> | null;
  medical_image_key: string | null;
  status: EncounterStatus;
  created_at: string;
}

export interface EncounterCreate {
  patient_id: string;
  complaint_text?: string;
  tabular_metrics_json?: Record<string, number>;
}

// ── AI Predictions ────────────────────────────────────────────────────────────

export interface AIPrediction {
  id: string;
  encounter_id: string;
  model_name: string;
  prediction_result_json: Record<string, unknown>;
  confidence_score: number | null;
  created_at: string;
}

export interface MultiModalPredictRequest {
  encounter_id: string;
  run_tabular: boolean;
  run_nlp: boolean;
  run_vision: boolean;
}

// ── Treatment Plans ───────────────────────────────────────────────────────────

export interface Drug {
  drug: string;
  dose: string;
  frequency: string;
}

export interface TreatmentPlan {
  id: string;
  encounter_id: string;
  diagnosis: string | null;
  prescription_drugs: Drug[] | null;
  behavioral_advice: string | null;
  ews_level: number;
}

export interface TreatmentPlanCreate {
  diagnosis?: string;
  prescription_drugs?: Drug[];
  behavioral_advice?: string;
  ews_level?: number;
}

// ── Clinical Reports ──────────────────────────────────────────────────────────

export type ReportStatus = "draft" | "approved";

export interface ClinicalReport {
  id: string;
  encounter_id: string;
  raw_notes: string | null;
  patient_friendly_report: string | null;
  status: ReportStatus;
  created_at: string;
  updated_at: string;
}

// ── EWS ───────────────────────────────────────────────────────────────────────

export interface EWSAlert {
  encounter_id: string;
  patient_name: string;
  ews_level: number;
  triggered_params: string[];
  message: string;
}

// ── Dashboard Stats ───────────────────────────────────────────────────────────

export interface AdminStats {
  total_patients: number;
  total_doctors: number;
  waiting_queues: number;
  serving_queues: number;
}

"""
MediSync AI — Pydantic Schemas
All request/response models with strict validation for API contracts.
"""
import uuid
from datetime import date, datetime
from typing import Any

from pydantic import BaseModel, ConfigDict, EmailStr, Field


# ─────────────────────────────────────────────────────────────────────────────
# Shared base config — all schema models are ORM-read-safe
# ─────────────────────────────────────────────────────────────────────────────

class _Base(BaseModel):
    model_config = ConfigDict(from_attributes=True)


# ─────────────────────────────────────────────────────────────────────────────
# Auth
# ─────────────────────────────────────────────────────────────────────────────

class TokenResponse(BaseModel):
    """JWT access token returned after successful login."""
    access_token: str
    token_type: str = "bearer"


class LoginRequest(BaseModel):
    email: EmailStr
    password: str = Field(min_length=6)


# ─────────────────────────────────────────────────────────────────────────────
# User
# ─────────────────────────────────────────────────────────────────────────────

class UserCreate(BaseModel):
    email: EmailStr
    password: str = Field(min_length=8)
    role: str = Field(pattern="^(admin|doctor|patient)$")


class UserRead(_Base):
    id: uuid.UUID
    email: str
    role: str
    is_active: bool
    created_at: datetime


# ─────────────────────────────────────────────────────────────────────────────
# Patient
# ─────────────────────────────────────────────────────────────────────────────

class PatientCreate(BaseModel):
    nik: str = Field(min_length=16, max_length=16, pattern=r"^\d{16}$")
    full_name: str = Field(min_length=2, max_length=255)
    dob: date
    gender: str = Field(pattern="^(male|female)$")
    phone: str | None = None
    medical_history_json: dict[str, Any] | None = None


class PatientRead(_Base):
    id: uuid.UUID
    user_id: uuid.UUID
    nik: str
    full_name: str
    dob: date
    gender: str
    phone: str | None
    medical_history_json: dict[str, Any] | None


# ─────────────────────────────────────────────────────────────────────────────
# Doctor
# ─────────────────────────────────────────────────────────────────────────────

class DoctorCreate(BaseModel):
    specialization: str = Field(min_length=2, max_length=100)
    license_number: str = Field(min_length=4, max_length=50)
    room_number: str | None = None


class DoctorRead(_Base):
    id: uuid.UUID
    user_id: uuid.UUID
    specialization: str
    license_number: str
    room_number: str | None
    status: str


class DoctorStatusUpdate(BaseModel):
    status: str = Field(pattern="^(available|busy|off)$")


# ─────────────────────────────────────────────────────────────────────────────
# Queue
# ─────────────────────────────────────────────────────────────────────────────

class QueueCreate(BaseModel):
    patient_id: uuid.UUID
    doctor_id: uuid.UUID | None = None
    poli_name: str = Field(min_length=2, max_length=100)


class QueueRead(_Base):
    id: uuid.UUID
    patient_id: uuid.UUID
    doctor_id: uuid.UUID | None
    poli_name: str
    queue_number: int
    status: str
    created_at: datetime
    updated_at: datetime


class QueueStatusUpdate(BaseModel):
    status: str = Field(pattern="^(waiting|serving|done|cancelled)$")


# ─────────────────────────────────────────────────────────────────────────────
# Medical Encounter
# ─────────────────────────────────────────────────────────────────────────────

class EncounterCreate(BaseModel):
    patient_id: uuid.UUID
    complaint_text: str | None = None
    tabular_metrics_json: dict[str, Any] | None = None


class EncounterRead(_Base):
    id: uuid.UUID
    patient_id: uuid.UUID
    doctor_id: uuid.UUID | None
    complaint_text: str | None
    tabular_metrics_json: dict[str, Any] | None
    medical_image_key: str | None
    status: str
    created_at: datetime


# ─────────────────────────────────────────────────────────────────────────────
# AI Prediction
# ─────────────────────────────────────────────────────────────────────────────

class AIPredictionRead(_Base):
    id: uuid.UUID
    encounter_id: uuid.UUID
    model_name: str
    prediction_result_json: dict[str, Any]
    confidence_score: float | None
    created_at: datetime


class MultiModalPredictRequest(BaseModel):
    """Request body to trigger multi-modal AI inference for an encounter."""
    encounter_id: uuid.UUID
    run_tabular: bool = True
    run_nlp: bool = True
    run_vision: bool = False  # Requires medical_image_key on the encounter


# ─────────────────────────────────────────────────────────────────────────────
# Treatment Plan
# ─────────────────────────────────────────────────────────────────────────────

class TreatmentPlanCreate(BaseModel):
    diagnosis: str | None = None
    prescription_drugs: list[dict[str, Any]] | None = Field(default_factory=list)
    behavioral_advice: str | None = None
    ews_level: int = Field(default=0, ge=0, le=3)


class TreatmentPlanRead(_Base):
    id: uuid.UUID
    encounter_id: uuid.UUID
    diagnosis: str | None
    prescription_drugs: list[dict[str, Any]] | None
    behavioral_advice: str | None
    ews_level: int


# ─────────────────────────────────────────────────────────────────────────────
# Clinical Report
# ─────────────────────────────────────────────────────────────────────────────

class ClinicalReportRead(_Base):
    id: uuid.UUID
    encounter_id: uuid.UUID
    raw_notes: str | None
    patient_friendly_report: str | None
    status: str
    created_at: datetime
    updated_at: datetime


class ReportApproveRequest(BaseModel):
    approved: bool = True


# ─────────────────────────────────────────────────────────────────────────────
# EWS Alert
# ─────────────────────────────────────────────────────────────────────────────

class EWSAlert(BaseModel):
    encounter_id: uuid.UUID
    patient_name: str
    ews_level: int
    triggered_params: list[str]
    message: str


# ─────────────────────────────────────────────────────────────────────────────
# Generic paginated response wrapper
# ─────────────────────────────────────────────────────────────────────────────

class PaginatedResponse(_Base):
    total: int
    page: int
    size: int
    items: list[Any]

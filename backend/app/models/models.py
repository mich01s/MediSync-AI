"""
MediSync AI — SQLAlchemy ORM Models
Defines all database tables as Python classes following the spec.md schema.
"""
import uuid
from datetime import date, datetime

from sqlalchemy import (
    JSON,
    Boolean,
    Date,
    DateTime,
    Enum,
    Float,
    ForeignKey,
    Integer,
    String,
    Text,
    func,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base

# ── Enums ─────────────────────────────────────────────────────────────────────

UserRoleEnum = Enum("admin", "doctor", "patient", name="user_role")
QueueStatusEnum = Enum("waiting", "serving", "done", "cancelled", name="queue_status")
EncounterStatusEnum = Enum("open", "closed", "pending_report", name="encounter_status")
ReportStatusEnum = Enum("draft", "approved", name="report_status")
DoctorStatusEnum = Enum("available", "busy", "off", name="doctor_status")


# ── users ─────────────────────────────────────────────────────────────────────

class User(Base):
    """Authentication & RBAC table — one record per platform user."""

    __tablename__ = "users"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    email: Mapped[str] = mapped_column(String(255), unique=True, nullable=False, index=True)
    password_hash: Mapped[str] = mapped_column(String(255), nullable=False)
    role: Mapped[str] = mapped_column(UserRoleEnum, nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )

    # Relationships
    patient_profile: Mapped["Patient"] = relationship("Patient", back_populates="user", uselist=False)
    doctor_profile: Mapped["Doctor"] = relationship("Doctor", back_populates="user", uselist=False)


# ── patients ──────────────────────────────────────────────────────────────────

class Patient(Base):
    """Detailed patient profile linked to a user account."""

    __tablename__ = "patients"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), unique=True
    )
    nik: Mapped[str] = mapped_column(String(16), unique=True, nullable=False)
    full_name: Mapped[str] = mapped_column(String(255), nullable=False)
    dob: Mapped[date] = mapped_column(Date, nullable=False)
    gender: Mapped[str] = mapped_column(Enum("male", "female", name="gender_enum"), nullable=False)
    phone: Mapped[str | None] = mapped_column(String(20))
    # Stored as JSON — e.g. {"allergies": [], "chronic_conditions": []}
    medical_history_json: Mapped[dict | None] = mapped_column(JSON, default=dict)

    user: Mapped["User"] = relationship("User", back_populates="patient_profile")
    queues: Mapped[list["Queue"]] = relationship("Queue", back_populates="patient")
    encounters: Mapped[list["MedicalEncounter"]] = relationship(
        "MedicalEncounter", back_populates="patient"
    )


# ── doctors ───────────────────────────────────────────────────────────────────

class Doctor(Base):
    """Doctor profile — specialization, license, and availability."""

    __tablename__ = "doctors"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), unique=True
    )
    specialization: Mapped[str] = mapped_column(String(100), nullable=False)
    license_number: Mapped[str] = mapped_column(String(50), unique=True, nullable=False)
    room_number: Mapped[str | None] = mapped_column(String(20))
    status: Mapped[str] = mapped_column(DoctorStatusEnum, default="available", nullable=False)

    user: Mapped["User"] = relationship("User", back_populates="doctor_profile")
    queues: Mapped[list["Queue"]] = relationship("Queue", back_populates="doctor")
    encounters: Mapped[list["MedicalEncounter"]] = relationship(
        "MedicalEncounter", back_populates="doctor"
    )


# ── queues ────────────────────────────────────────────────────────────────────

class Queue(Base):
    """Real-time queue entry — updated via WebSocket push."""

    __tablename__ = "queues"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    patient_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("patients.id", ondelete="CASCADE")
    )
    doctor_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("doctors.id", ondelete="SET NULL"), nullable=True
    )
    poli_name: Mapped[str] = mapped_column(String(100), nullable=False)
    queue_number: Mapped[int] = mapped_column(Integer, nullable=False)
    status: Mapped[str] = mapped_column(QueueStatusEnum, default="waiting", nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    patient: Mapped["Patient"] = relationship("Patient", back_populates="queues")
    doctor: Mapped["Doctor"] = relationship("Doctor", back_populates="queues")


# ── medical_encounters ────────────────────────────────────────────────────────

class MedicalEncounter(Base):
    """A single examination session — holds complaint text and vital signs."""

    __tablename__ = "medical_encounters"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    patient_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("patients.id", ondelete="CASCADE")
    )
    doctor_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("doctors.id", ondelete="SET NULL"), nullable=True
    )
    # Raw complaint narrative from the patient
    complaint_text: Mapped[str | None] = mapped_column(Text)
    # Vital signs — e.g. {"bp_systolic": 120, "hr": 72, "temp": 36.8, "glucose": 95}
    tabular_metrics_json: Mapped[dict | None] = mapped_column(JSON, default=dict)
    # Optional path/key to medical image in MinIO
    medical_image_key: Mapped[str | None] = mapped_column(String(512))
    status: Mapped[str] = mapped_column(EncounterStatusEnum, default="open", nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )

    patient: Mapped["Patient"] = relationship("Patient", back_populates="encounters")
    doctor: Mapped["Doctor"] = relationship("Doctor", back_populates="encounters")
    ai_predictions: Mapped[list["AIPrediction"]] = relationship(
        "AIPrediction", back_populates="encounter"
    )
    treatment_plan: Mapped["TreatmentPlan"] = relationship(
        "TreatmentPlan", back_populates="encounter", uselist=False
    )
    clinical_report: Mapped["ClinicalReport"] = relationship(
        "ClinicalReport", back_populates="encounter", uselist=False
    )


# ── ai_predictions ────────────────────────────────────────────────────────────

class AIPrediction(Base):
    """
    Stores per-modality inference results.
    model_name examples: 'tabular_xgboost', 'nlp_extractor', 'vision_cnn'
    """

    __tablename__ = "ai_predictions"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    encounter_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("medical_encounters.id", ondelete="CASCADE")
    )
    model_name: Mapped[str] = mapped_column(String(100), nullable=False)
    # JSON — e.g. {"label": "hypertension", "probabilities": {...}}
    prediction_result_json: Mapped[dict] = mapped_column(JSON, nullable=False)
    confidence_score: Mapped[float | None] = mapped_column(Float)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )

    encounter: Mapped["MedicalEncounter"] = relationship(
        "MedicalEncounter", back_populates="ai_predictions"
    )


# ── treatment_plans ───────────────────────────────────────────────────────────

class TreatmentPlan(Base):
    """Doctor-authored treatment plan + LLM-generated behavioral advice."""

    __tablename__ = "treatment_plans"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    encounter_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("medical_encounters.id", ondelete="CASCADE"), unique=True
    )
    diagnosis: Mapped[str | None] = mapped_column(Text)
    # JSON list — [{"drug": "Amlodipine", "dose": "5mg", "frequency": "once daily"}]
    prescription_drugs: Mapped[list | None] = mapped_column(JSON, default=list)
    behavioral_advice: Mapped[str | None] = mapped_column(Text)
    # EWS level: 0 (normal) → 3 (critical)
    ews_level: Mapped[int] = mapped_column(Integer, default=0, nullable=False)

    encounter: Mapped["MedicalEncounter"] = relationship(
        "MedicalEncounter", back_populates="treatment_plan"
    )


# ── clinical_reports ──────────────────────────────────────────────────────────

class ClinicalReport(Base):
    """LLM-generated patient-friendly report; requires doctor approval."""

    __tablename__ = "clinical_reports"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    encounter_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("medical_encounters.id", ondelete="CASCADE"), unique=True
    )
    raw_notes: Mapped[str | None] = mapped_column(Text)
    patient_friendly_report: Mapped[str | None] = mapped_column(Text)
    status: Mapped[str] = mapped_column(ReportStatusEnum, default="draft", nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    encounter: Mapped["MedicalEncounter"] = relationship(
        "MedicalEncounter", back_populates="clinical_report"
    )

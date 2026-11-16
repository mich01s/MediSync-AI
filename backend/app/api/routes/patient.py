"""
MediSync AI — Patient Routes
Patients can view their own queue status, encounter history,
and approved clinical reports.
"""
import uuid

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user, require_role
from app.core.database import get_db
from app.models.models import (
    ClinicalReport,
    MedicalEncounter,
    Patient,
    Queue,
    TreatmentPlan,
    User,
)
from app.schemas.schemas import (
    ClinicalReportRead,
    EncounterRead,
    PatientCreate,
    PatientRead,
    QueueRead,
    TreatmentPlanRead,
)

router = APIRouter(prefix="/patient", tags=["patient"])


# ── Profile ───────────────────────────────────────────────────────────────────

@router.post("/profile", response_model=PatientRead, status_code=201,
             dependencies=[Depends(require_role("patient"))])
async def create_patient_profile(
    payload: PatientCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> Patient:
    """
    Create a patient profile for the authenticated user.
    Can only be called once per user account.
    """
    existing = await db.execute(select(Patient).where(Patient.user_id == current_user.id))
    if existing.scalar_one_or_none():
        raise HTTPException(status_code=409, detail="Profile already exists.")

    patient = Patient(
        user_id=current_user.id,
        nik=payload.nik,
        full_name=payload.full_name,
        dob=payload.dob,
        gender=payload.gender,
        phone=payload.phone,
        medical_history_json=payload.medical_history_json or {},
    )
    db.add(patient)
    await db.commit()
    await db.refresh(patient)
    return patient


@router.get("/profile", response_model=PatientRead,
            dependencies=[Depends(require_role("patient"))])
async def get_patient_profile(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> Patient:
    """Return the authenticated patient's own profile."""
    result = await db.execute(select(Patient).where(Patient.user_id == current_user.id))
    patient = result.scalar_one_or_none()
    if not patient:
        raise HTTPException(status_code=404, detail="Profile not found.")
    return patient


# ── Queue ─────────────────────────────────────────────────────────────────────

@router.get("/queue", response_model=list[QueueRead],
            dependencies=[Depends(require_role("patient"))])
async def get_my_queue(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> list[Queue]:
    """Return all active queue entries for the authenticated patient."""
    result = await db.execute(select(Patient).where(Patient.user_id == current_user.id))
    patient = result.scalar_one_or_none()
    if not patient:
        raise HTTPException(status_code=404, detail="Patient profile not found.")

    queue_result = await db.execute(
        select(Queue)
        .where(Queue.patient_id == patient.id)
        .where(Queue.status.in_(["waiting", "serving"]))
        .order_by(Queue.created_at)
    )
    return list(queue_result.scalars().all())


# ── Medical Encounters ────────────────────────────────────────────────────────

@router.get("/encounters", response_model=list[EncounterRead],
            dependencies=[Depends(require_role("patient"))])
async def get_my_encounters(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> list[MedicalEncounter]:
    """Return the encounter history of the authenticated patient."""
    result = await db.execute(select(Patient).where(Patient.user_id == current_user.id))
    patient = result.scalar_one_or_none()
    if not patient:
        raise HTTPException(status_code=404, detail="Patient profile not found.")

    enc_result = await db.execute(
        select(MedicalEncounter)
        .where(MedicalEncounter.patient_id == patient.id)
        .order_by(MedicalEncounter.created_at.desc())
    )
    return list(enc_result.scalars().all())


# ── Clinical Reports ──────────────────────────────────────────────────────────

@router.get("/reports", response_model=list[ClinicalReportRead],
            dependencies=[Depends(require_role("patient"))])
async def get_my_reports(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> list[ClinicalReport]:
    """Return approved clinical reports visible to the patient."""
    result = await db.execute(select(Patient).where(Patient.user_id == current_user.id))
    patient = result.scalar_one_or_none()
    if not patient:
        raise HTTPException(status_code=404, detail="Patient profile not found.")

    # Join through encounters to fetch approved reports for this patient
    enc_ids_result = await db.execute(
        select(MedicalEncounter.id).where(MedicalEncounter.patient_id == patient.id)
    )
    enc_ids = [row[0] for row in enc_ids_result.fetchall()]
    if not enc_ids:
        return []

    report_result = await db.execute(
        select(ClinicalReport)
        .where(ClinicalReport.encounter_id.in_(enc_ids))
        .where(ClinicalReport.status == "approved")
        .order_by(ClinicalReport.created_at.desc())
    )
    return list(report_result.scalars().all())


@router.get("/reports/{report_id}", response_model=ClinicalReportRead,
            dependencies=[Depends(require_role("patient"))])
async def get_report_detail(
    report_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> ClinicalReport:
    """Get a single approved clinical report."""
    report = await db.get(ClinicalReport, report_id)
    if not report or report.status != "approved":
        raise HTTPException(status_code=404, detail="Report not found or not approved yet.")
    return report


# ── Treatment Plan (read-only for patient) ────────────────────────────────────

@router.get("/encounters/{encounter_id}/treatment-plan",
            response_model=TreatmentPlanRead,
            dependencies=[Depends(require_role("patient"))])
async def get_treatment_plan(
    encounter_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
) -> TreatmentPlan:
    """Return the treatment plan (including behavioral advice) for an encounter."""
    result = await db.execute(
        select(TreatmentPlan).where(TreatmentPlan.encounter_id == encounter_id)
    )
    plan = result.scalar_one_or_none()
    if not plan:
        raise HTTPException(status_code=404, detail="Treatment plan not found.")
    return plan

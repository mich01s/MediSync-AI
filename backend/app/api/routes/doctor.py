"""
MediSync AI — Doctor Routes
Handles encounters, AI prediction triggering, treatment plans,
and clinical report approval.
"""
import uuid

from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user, require_role
from app.core.database import get_db
from app.models.models import (
    AIPrediction,
    ClinicalReport,
    Doctor,
    MedicalEncounter,
    Patient,
    TreatmentPlan,
    User,
)
from app.schemas.schemas import (
    AIPredictionRead,
    ClinicalReportRead,
    EncounterCreate,
    EncounterRead,
    MultiModalPredictRequest,
    PatientRead,
    ReportApproveRequest,
    TreatmentPlanCreate,
    TreatmentPlanRead,
)
from app.services.ews_service import evaluate_ews
from app.services.llm_report_service import generate_patient_report
from app.ai_pipeline.tabular_predictor import predict_tabular
from app.ai_pipeline.nlp_extractor import extract_nlp_features
from app.ai_pipeline.vision_analyzer import analyze_medical_image

router = APIRouter(prefix="/doctor", tags=["doctor"])


# ── Helpers ───────────────────────────────────────────────────────────────────

async def _get_doctor_for_user(user: User, db: AsyncSession) -> Doctor:
    """Resolve the Doctor profile for the authenticated user."""
    result = await db.execute(select(Doctor).where(Doctor.user_id == user.id))
    doctor = result.scalar_one_or_none()
    if not doctor:
        raise HTTPException(status_code=404, detail="Doctor profile not found.")
    return doctor


# ── Patients (read-only for doctors) ─────────────────────────────────────────

@router.get("/patients", response_model=list[PatientRead],
            dependencies=[Depends(require_role("doctor"))])
async def list_patients_for_doctor(
    db: AsyncSession = Depends(get_db),
) -> list[Patient]:
    """
    Return all patient profiles — doctors need this to create encounters.
    Read-only access; no PII modification allowed from this endpoint.
    """
    result = await db.execute(select(Patient))
    return list(result.scalars().all())


# ── Encounters ────────────────────────────────────────────────────────────────

@router.post("/encounters", response_model=EncounterRead, status_code=201,
             dependencies=[Depends(require_role("doctor"))])
async def create_encounter(
    payload: EncounterCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> MedicalEncounter:
    """Open a new medical encounter for a patient."""
    doctor = await _get_doctor_for_user(current_user, db)

    # Verify patient exists
    patient = await db.get(Patient, payload.patient_id)
    if not patient:
        raise HTTPException(status_code=404, detail="Patient not found.")

    encounter = MedicalEncounter(
        patient_id=payload.patient_id,
        doctor_id=doctor.id,
        complaint_text=payload.complaint_text,
        tabular_metrics_json=payload.tabular_metrics_json,
    )
    db.add(encounter)
    await db.commit()
    await db.refresh(encounter)
    return encounter


@router.get("/encounters/{encounter_id}", response_model=EncounterRead,
            dependencies=[Depends(require_role("doctor", "admin"))])
async def get_encounter(
    encounter_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
) -> MedicalEncounter:
    """Retrieve a single encounter by ID."""
    enc = await db.get(MedicalEncounter, encounter_id)
    if not enc:
        raise HTTPException(status_code=404, detail="Encounter not found.")
    return enc


@router.get("/encounters", response_model=list[EncounterRead],
            dependencies=[Depends(require_role("doctor"))])
async def list_my_encounters(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> list[MedicalEncounter]:
    """Return all encounters assigned to the authenticated doctor."""
    doctor = await _get_doctor_for_user(current_user, db)
    result = await db.execute(
        select(MedicalEncounter).where(MedicalEncounter.doctor_id == doctor.id)
    )
    return list(result.scalars().all())


# ── Upload medical image ───────────────────────────────────────────────────────

@router.post("/encounters/{encounter_id}/upload-image",
             dependencies=[Depends(require_role("doctor"))])
async def upload_medical_image(
    encounter_id: uuid.UUID,
    file: UploadFile = File(...),
    db: AsyncSession = Depends(get_db),
) -> dict:
    """
    Upload a medical image (X-Ray, MRI, CT) to MinIO/S3 and
    attach the storage key to the encounter.
    """
    from app.core.config import settings
    from minio import Minio
    import io

    enc = await db.get(MedicalEncounter, encounter_id)
    if not enc:
        raise HTTPException(status_code=404, detail="Encounter not found.")

    # Upload to MinIO
    client = Minio(
        settings.MINIO_ENDPOINT,
        access_key=settings.MINIO_ACCESS_KEY,
        secret_key=settings.MINIO_SECRET_KEY,
        secure=settings.MINIO_USE_SSL,
    )
    bucket = settings.MINIO_BUCKET_MEDICAL_IMAGES
    if not client.bucket_exists(bucket):
        client.make_bucket(bucket)

    object_key = f"{encounter_id}/{file.filename}"
    data = await file.read()
    client.put_object(bucket, object_key, io.BytesIO(data), length=len(data),
                      content_type=file.content_type or "application/octet-stream")

    enc.medical_image_key = object_key
    await db.commit()
    return {"message": "Image uploaded successfully.", "object_key": object_key}


# ── AI Multi-Modal Prediction ─────────────────────────────────────────────────

@router.post("/predict", response_model=list[AIPredictionRead],
             dependencies=[Depends(require_role("doctor"))])
async def run_multimodal_prediction(
    payload: MultiModalPredictRequest,
    db: AsyncSession = Depends(get_db),
) -> list[AIPrediction]:
    """
    Trigger multi-modal AI inference pipeline for the given encounter.
    Returns stored AIPrediction records for each active modality.
    """
    enc = await db.get(MedicalEncounter, payload.encounter_id)
    if not enc:
        raise HTTPException(status_code=404, detail="Encounter not found.")

    new_predictions: list[AIPrediction] = []

    # 1. Tabular prediction (vital signs)
    if payload.run_tabular and enc.tabular_metrics_json:
        result = predict_tabular(enc.tabular_metrics_json)
        pred = AIPrediction(
            encounter_id=enc.id,
            model_name="tabular_xgboost",
            prediction_result_json=result["output"],
            confidence_score=result.get("confidence"),
        )
        db.add(pred)
        new_predictions.append(pred)

    # 2. NLP extraction (complaint text)
    if payload.run_nlp and enc.complaint_text:
        result = extract_nlp_features(enc.complaint_text)
        pred = AIPrediction(
            encounter_id=enc.id,
            model_name="nlp_extractor",
            prediction_result_json=result["output"],
            confidence_score=result.get("confidence"),
        )
        db.add(pred)
        new_predictions.append(pred)

    # 3. Vision analysis (medical image)
    if payload.run_vision and enc.medical_image_key:
        result = analyze_medical_image(enc.medical_image_key)
        pred = AIPrediction(
            encounter_id=enc.id,
            model_name="vision_cnn",
            prediction_result_json=result["output"],
            confidence_score=result.get("confidence"),
        )
        db.add(pred)
        new_predictions.append(pred)

    if not new_predictions:
        raise HTTPException(
            status_code=400,
            detail="No modalities could run — check encounter data.",
        )

    await db.commit()
    for p in new_predictions:
        await db.refresh(p)
    return new_predictions


# ── Treatment Plans ───────────────────────────────────────────────────────────

@router.post("/encounters/{encounter_id}/treatment-plan",
             response_model=TreatmentPlanRead, status_code=201,
             dependencies=[Depends(require_role("doctor"))])
async def create_treatment_plan(
    encounter_id: uuid.UUID,
    payload: TreatmentPlanCreate,
    db: AsyncSession = Depends(get_db),
) -> TreatmentPlan:
    """Create or replace the treatment plan for an encounter."""
    enc = await db.get(MedicalEncounter, encounter_id)
    if not enc:
        raise HTTPException(status_code=404, detail="Encounter not found.")

    # Determine EWS level from vital signs
    ews_data = evaluate_ews(enc.tabular_metrics_json or {})
    ews_level = payload.ews_level or ews_data["level"]

    plan = TreatmentPlan(
        encounter_id=encounter_id,
        diagnosis=payload.diagnosis,
        prescription_drugs=payload.prescription_drugs,
        behavioral_advice=payload.behavioral_advice,
        ews_level=ews_level,
    )
    db.add(plan)
    enc.status = "pending_report"
    await db.commit()
    await db.refresh(plan)
    return plan


# ── Clinical Reports ──────────────────────────────────────────────────────────

@router.post("/encounters/{encounter_id}/generate-report",
             response_model=ClinicalReportRead,
             dependencies=[Depends(require_role("doctor"))])
async def generate_report(
    encounter_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
) -> ClinicalReport:
    """
    Invoke the LLM service to generate a patient-friendly clinical report
    draft from the encounter data. Saved with status='draft'.
    """
    enc = await db.get(MedicalEncounter, encounter_id)
    if not enc:
        raise HTTPException(status_code=404, detail="Encounter not found.")

    plan_result = await db.execute(
        select(TreatmentPlan).where(TreatmentPlan.encounter_id == encounter_id)
    )
    plan = plan_result.scalar_one_or_none()

    raw_notes = (
        f"Complaint: {enc.complaint_text}\n"
        f"Vitals: {enc.tabular_metrics_json}\n"
        f"Diagnosis: {plan.diagnosis if plan else 'N/A'}\n"
        f"Prescription: {plan.prescription_drugs if plan else 'N/A'}"
    )

    friendly_report = await generate_patient_report(raw_notes)

    # Upsert report
    existing_result = await db.execute(
        select(ClinicalReport).where(ClinicalReport.encounter_id == encounter_id)
    )
    report = existing_result.scalar_one_or_none()
    if report:
        report.raw_notes = raw_notes
        report.patient_friendly_report = friendly_report
        report.status = "draft"
    else:
        report = ClinicalReport(
            encounter_id=encounter_id,
            raw_notes=raw_notes,
            patient_friendly_report=friendly_report,
            status="draft",
        )
        db.add(report)

    await db.commit()
    await db.refresh(report)
    return report


@router.patch("/reports/{report_id}/approve",
              response_model=ClinicalReportRead,
              dependencies=[Depends(require_role("doctor"))])
async def approve_report(
    report_id: uuid.UUID,
    payload: ReportApproveRequest,
    db: AsyncSession = Depends(get_db),
) -> ClinicalReport:
    """Doctor approves (or rejects back to draft) a clinical report."""
    report = await db.get(ClinicalReport, report_id)
    if not report:
        raise HTTPException(status_code=404, detail="Report not found.")
    report.status = "approved" if payload.approved else "draft"
    await db.commit()
    await db.refresh(report)
    return report

"""
MediSync AI — Admin Routes
Hospital Admin can manage doctors, patients, and global queue overview.
"""
import uuid

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import require_role
from app.core.database import get_db
from app.models.models import Doctor, Patient, Queue, User
from app.schemas.schemas import (
    DoctorCreate,
    DoctorRead,
    DoctorStatusUpdate,
    PaginatedResponse,
    PatientRead,
    QueueRead,
    UserCreate,
    UserRead,
)
from app.core.security import hash_password

router = APIRouter(prefix="/admin", tags=["admin"])

# ── Doctors management ────────────────────────────────────────────────────────

@router.post("/doctors", response_model=DoctorRead, status_code=status.HTTP_201_CREATED,
             dependencies=[Depends(require_role("admin"))])
async def create_doctor(
    user_payload: UserCreate,
    doctor_payload: DoctorCreate,
    db: AsyncSession = Depends(get_db),
) -> Doctor:
    """
    Admin creates a doctor account (user record + doctor profile in one call).
    """
    existing = await db.execute(select(User).where(User.email == user_payload.email))
    if existing.scalar_one_or_none():
        raise HTTPException(status_code=409, detail="Email already registered.")

    user = User(
        email=user_payload.email,
        password_hash=hash_password(user_payload.password),
        role="doctor",
    )
    db.add(user)
    await db.flush()  # Obtain user.id before creating doctor profile

    doctor = Doctor(
        user_id=user.id,
        specialization=doctor_payload.specialization,
        license_number=doctor_payload.license_number,
        room_number=doctor_payload.room_number,
    )
    db.add(doctor)
    await db.commit()
    await db.refresh(doctor)
    return doctor


@router.get("/doctors", response_model=list[DoctorRead],
            dependencies=[Depends(require_role("admin"))])
async def list_doctors(db: AsyncSession = Depends(get_db)) -> list[Doctor]:
    """Return all registered doctors."""
    result = await db.execute(select(Doctor))
    return list(result.scalars().all())


@router.patch("/doctors/{doctor_id}/status", response_model=DoctorRead,
              dependencies=[Depends(require_role("admin"))])
async def update_doctor_status(
    doctor_id: uuid.UUID,
    payload: DoctorStatusUpdate,
    db: AsyncSession = Depends(get_db),
) -> Doctor:
    """Update a doctor's availability status."""
    result = await db.execute(select(Doctor).where(Doctor.id == doctor_id))
    doctor = result.scalar_one_or_none()
    if not doctor:
        raise HTTPException(status_code=404, detail="Doctor not found.")
    doctor.status = payload.status
    await db.commit()
    await db.refresh(doctor)
    return doctor


# ── Patients listing ──────────────────────────────────────────────────────────

@router.get("/patients", response_model=list[PatientRead],
            dependencies=[Depends(require_role("admin"))])
async def list_patients(
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
) -> list[Patient]:
    """Paginated list of all patients."""
    result = await db.execute(select(Patient).offset(skip).limit(limit))
    return list(result.scalars().all())


# ── Queue overview ────────────────────────────────────────────────────────────

@router.get("/queues", response_model=list[QueueRead],
            dependencies=[Depends(require_role("admin"))])
async def list_all_queues(
    poli_name: str | None = Query(None),
    status_filter: str | None = Query(None, alias="status"),
    db: AsyncSession = Depends(get_db),
) -> list[Queue]:
    """Return all queues, optionally filtered by poli or status."""
    query = select(Queue)
    if poli_name:
        query = query.where(Queue.poli_name == poli_name)
    if status_filter:
        query = query.where(Queue.status == status_filter)
    result = await db.execute(query)
    return list(result.scalars().all())


# ── Stats / Dashboard ─────────────────────────────────────────────────────────

@router.get("/stats", dependencies=[Depends(require_role("admin"))])
async def get_dashboard_stats(db: AsyncSession = Depends(get_db)) -> dict:
    """High-level operational stats for the admin dashboard."""
    total_patients = (await db.execute(select(func.count(Patient.id)))).scalar()
    total_doctors = (await db.execute(select(func.count(Doctor.id)))).scalar()
    waiting_queues = (
        await db.execute(select(func.count(Queue.id)).where(Queue.status == "waiting"))
    ).scalar()
    serving_queues = (
        await db.execute(select(func.count(Queue.id)).where(Queue.status == "serving"))
    ).scalar()

    return {
        "total_patients": total_patients,
        "total_doctors": total_doctors,
        "waiting_queues": waiting_queues,
        "serving_queues": serving_queues,
    }

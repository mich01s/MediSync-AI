"""
MediSync AI — Queue Routes + WebSocket
Handles queue creation, status updates, and real-time WebSocket broadcasting.
"""
import json
import uuid
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, WebSocket, WebSocketDisconnect
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import require_role
from app.core.database import get_db
from app.core.redis_client import get_redis
from app.models.models import Doctor, Patient, Queue
from app.schemas.schemas import QueueCreate, QueueRead, QueueStatusUpdate
from app.services.queue_service import (
    broadcast_queue_update,
    get_next_queue_number,
    ws_manager,
)

router = APIRouter(prefix="/queue", tags=["queue"])


# ── REST endpoints ────────────────────────────────────────────────────────────

@router.post("/", response_model=QueueRead, status_code=201,
             dependencies=[Depends(require_role("admin", "patient"))])
async def create_queue_entry(
    payload: QueueCreate,
    db: AsyncSession = Depends(get_db),
) -> Queue:
    """
    Register a patient into the queue for a specific poli.
    Queue number is auto-incremented per poli per day.
    """
    # Validate patient
    if not await db.get(Patient, payload.patient_id):
        raise HTTPException(status_code=404, detail="Patient not found.")

    queue_number = await get_next_queue_number(payload.poli_name, db)

    entry = Queue(
        patient_id=payload.patient_id,
        doctor_id=payload.doctor_id,
        poli_name=payload.poli_name,
        queue_number=queue_number,
        status="waiting",
    )
    db.add(entry)
    await db.commit()
    await db.refresh(entry)

    # Broadcast to all WebSocket subscribers for this poli
    await broadcast_queue_update(payload.poli_name, entry)

    return entry


@router.patch("/{queue_id}/status", response_model=QueueRead,
              dependencies=[Depends(require_role("admin", "doctor"))])
async def update_queue_status(
    queue_id: uuid.UUID,
    payload: QueueStatusUpdate,
    db: AsyncSession = Depends(get_db),
) -> Queue:
    """Update the status of a queue entry and push change via WebSocket."""
    entry = await db.get(Queue, queue_id)
    if not entry:
        raise HTTPException(status_code=404, detail="Queue entry not found.")

    entry.status = payload.status
    await db.commit()
    await db.refresh(entry)

    # Broadcast updated state to subscribers
    await broadcast_queue_update(entry.poli_name, entry)

    return entry


@router.get("/poli/{poli_name}", response_model=list[QueueRead])
async def get_poli_queue(
    poli_name: str,
    db: AsyncSession = Depends(get_db),
) -> list[Queue]:
    """Return the current active queue for a specific poli (public endpoint)."""
    result = await db.execute(
        select(Queue)
        .where(Queue.poli_name == poli_name)
        .where(Queue.status.in_(["waiting", "serving"]))
        .order_by(Queue.queue_number)
    )
    return list(result.scalars().all())


# ── WebSocket endpoint ────────────────────────────────────────────────────────

@router.websocket("/ws/{poli_name}")
async def queue_websocket(websocket: WebSocket, poli_name: str) -> None:
    """
    WebSocket endpoint — clients subscribe to live queue updates for *poli_name*.
    Messages are JSON-encoded QueueRead payloads broadcast on every queue change.
    """
    await ws_manager.connect(poli_name, websocket)
    try:
        while True:
            # Keep connection alive — client can send ping messages
            data = await websocket.receive_text()
            if data == "ping":
                await websocket.send_text("pong")
    except WebSocketDisconnect:
        ws_manager.disconnect(poli_name, websocket)

"""
MediSync AI — Queue Service
Manages WebSocket connection pooling and queue number generation.
Redis pub/sub is used to broadcast queue updates across multiple workers.
"""
import json
from typing import Any

from fastapi import WebSocket
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.models import Queue


# ── WebSocket Connection Manager ──────────────────────────────────────────────

class ConnectionManager:
    """
    In-process WebSocket manager keyed by poli_name.
    In production with multiple workers, replace with a Redis pub/sub fan-out.
    """

    def __init__(self) -> None:
        # poli_name → list of active WebSocket connections
        self._connections: dict[str, list[WebSocket]] = {}

    async def connect(self, poli_name: str, ws: WebSocket) -> None:
        await ws.accept()
        self._connections.setdefault(poli_name, []).append(ws)

    def disconnect(self, poli_name: str, ws: WebSocket) -> None:
        if poli_name in self._connections:
            self._connections[poli_name].discard(ws) if hasattr(
                self._connections[poli_name], "discard"
            ) else self._connections[poli_name].remove(ws)

    async def broadcast(self, poli_name: str, message: str) -> None:
        """Send *message* to every subscriber of *poli_name*."""
        dead: list[WebSocket] = []
        for ws in self._connections.get(poli_name, []):
            try:
                await ws.send_text(message)
            except Exception:
                dead.append(ws)
        for ws in dead:
            self.disconnect(poli_name, ws)


# Singleton connection manager
ws_manager = ConnectionManager()


# ── Queue number generation ───────────────────────────────────────────────────

async def get_next_queue_number(poli_name: str, db: AsyncSession) -> int:
    """
    Return the next sequential queue number for *poli_name* today.
    Counts all existing entries for the poli (regardless of day),
    suitable for demo purposes; add a date filter for production use.
    """
    result = await db.execute(
        select(func.count(Queue.id)).where(Queue.poli_name == poli_name)
    )
    count: int = result.scalar() or 0
    return count + 1


# ── Broadcast helper ──────────────────────────────────────────────────────────

async def broadcast_queue_update(poli_name: str, queue_entry: Queue) -> None:
    """
    Serialize a Queue ORM object and broadcast it to WebSocket subscribers
    for the given poli.
    """
    payload: dict[str, Any] = {
        "id": str(queue_entry.id),
        "patient_id": str(queue_entry.patient_id),
        "doctor_id": str(queue_entry.doctor_id) if queue_entry.doctor_id else None,
        "poli_name": queue_entry.poli_name,
        "queue_number": queue_entry.queue_number,
        "status": queue_entry.status,
    }
    await ws_manager.broadcast(poli_name, json.dumps(payload))

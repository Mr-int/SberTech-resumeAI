from fastapi import APIRouter, HTTPException
from uuid import UUID

from app.services.session_store import STORE

router = APIRouter(prefix="/session", tags=["Session"])


@router.post("/reset")
async def reset_session(session_id: UUID):
    s = STORE.get(session_id)
    if not s:
        raise HTTPException(status_code=404, detail="Session not found")
    s["messages"] = []
    return {"ok": True}

from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from typing import Optional
from data_manager import sanitize_text_field, get_db_connection
from api.routers.auth import get_current_user

router = APIRouter()

class PanganInput(BaseModel):
    jenis_pakan: str
    berat_pakan_kg: float
    tanggal: str
    notes: Optional[str] = ""

class BeratInput(BaseModel):
    berat_maggot_kg: float
    tanggal: str
    notes: Optional[str] = ""

@router.post("/pangan")
def input_pangan(req: PanganInput, user: dict = Depends(get_current_user)):
    jenis_clean, warning = sanitize_text_field(req.jenis_pakan, "Jenis pakan")
    if warning:
        raise HTTPException(status_code=400, detail=warning)
        
    notes_clean, warning_notes = sanitize_text_field(req.notes, "Catatan")
    if warning_notes:
        raise HTTPException(status_code=400, detail=warning_notes)
    
    conn = get_db_connection()
    try:
        conn.execute("""
            INSERT INTO feed_logs (user_id, date, feed_type, feed_weight_kg, notes)
            VALUES (?, ?, ?, ?, ?)
        """, (user.get("user_id"), req.tanggal, jenis_clean, req.berat_pakan_kg, notes_clean))
        conn.commit()
        return {"status": "success", "message": "Data pangan tersimpan."}
    finally:
        conn.close()

@router.post("/berat")
def input_berat(req: BeratInput, user: dict = Depends(get_current_user)):
    if req.berat_maggot_kg < 0:
        raise HTTPException(status_code=400, detail="Berat tidak boleh negatif.")
        
    notes_clean, warning_notes = sanitize_text_field(req.notes, "Catatan")
    if warning_notes:
        raise HTTPException(status_code=400, detail=warning_notes)
        
    conn = get_db_connection()
    try:
        conn.execute("""
            INSERT INTO weight_logs (user_id, date, maggot_weight_kg, notes)
            VALUES (?, ?, ?, ?)
        """, (user.get("user_id"), req.tanggal, req.berat_maggot_kg, notes_clean))
        conn.commit()
        return {"status": "success", "message": "Data berat tersimpan."}
    finally:
        conn.close()

@router.get("/history")
def get_history():
    conn = get_db_connection()
    try:
        pangan = conn.execute("SELECT * FROM feed_logs ORDER BY id DESC LIMIT 5").fetchall()
        berat = conn.execute("SELECT * FROM weight_logs ORDER BY id DESC LIMIT 5").fetchall()
        return {
            "pangan": [dict(p) for p in pangan],
            "berat": [dict(b) for b in berat]
        }
    finally:
        conn.close()

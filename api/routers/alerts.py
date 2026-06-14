from fastapi import APIRouter, Depends
from typing import List
from data_manager import get_db_connection

router = APIRouter()

@router.get("/unread")
def get_unread_alerts():
    conn = get_db_connection()
    try:
        # Assuming single user for now or no user filtering. 
        # For multi-user, we would need to get user_id from token.
        alerts = conn.execute(
            "SELECT * FROM alerts WHERE is_read = 0 ORDER BY created_at DESC LIMIT 50"
        ).fetchall()
        return {"alerts": [dict(a) for a in alerts]}
    finally:
        conn.close()

@router.post("/mark-read")
def mark_alerts_read():
    conn = get_db_connection()
    try:
        conn.execute("UPDATE alerts SET is_read = 1 WHERE is_read = 0")
        conn.commit()
        return {"status": "success"}
    finally:
        conn.close()

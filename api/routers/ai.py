import os
import json
import logging
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from dotenv import load_dotenv
from groq import Groq
from data_manager import get_db_connection

router = APIRouter()
load_dotenv()

# Setup safe logger
logging.basicConfig(level=logging.INFO)
ai_logger = logging.getLogger("ai_telemetry")

class AIRequest(BaseModel):
    prompt: str

@router.post("/analyze")
def analyze(req: AIRequest):
    groq_api_key = os.getenv("GROQ_API_KEY")
    if not groq_api_key:
        raise HTTPException(status_code=500, detail="GROQ_API_KEY tidak ditemukan di .env")
        
    conn = get_db_connection()
    try:
        # Aggregate ALL data
        feed_summary = conn.execute(
            "SELECT COUNT(*) as count, SUM(feed_weight_kg) as total_feed FROM feed_logs"
        ).fetchone()
        
        weight_summary = conn.execute(
            "SELECT COUNT(*) as count, MIN(maggot_weight_kg) as min_w, MAX(maggot_weight_kg) as max_w FROM weight_logs"
        ).fetchone()
        
        sensor_summary = conn.execute(
            "SELECT COUNT(*) as count, AVG(temperature) as avg_t, AVG(humidity) as avg_h, MAX(temperature) as max_t, MIN(temperature) as min_t FROM sensor_logs"
        ).fetchone()
        
        alert_summary = conn.execute(
            "SELECT COUNT(*) as count FROM alerts"
        ).fetchone()

        # Build summarized context
        context_lines = [
            f"Ringkasan Keseluruhan Data Operasional Kandang:",
            f"- Total pakan diberikan: {feed_summary['total_feed'] or 0:.2f} kg ({feed_summary['count']} kali)",
            f"- Rekor berat maggot: {weight_summary['min_w'] or 0:.2f} kg s/d {weight_summary['max_w'] or 0:.2f} kg ({weight_summary['count']} pencatatan)",
            f"- Sensor IoT ({sensor_summary['count']} rekaman): rata-rata {sensor_summary['avg_t'] or 0:.1f}°C, kelembapan {sensor_summary['avg_h'] or 0:.1f}%. Suhu ekstrim tercatat: {sensor_summary['min_t'] or 0}°C - {sensor_summary['max_t'] or 0}°C",
            f"- Jumlah riwayat peringatan sistem (anomali): {alert_summary['count']} peringatan"
        ]
        data_context = "\n".join(context_lines)
        
        full_prompt = (
            "Anda adalah AI asisten untuk budidaya Maggot BSF (Black Soldier Fly).\n"
            "Gunakan RINGKASAN data operasional berikut sebagai konteks analisis:\n\n"
            f"{data_context}\n\n"
            f"Pertanyaan/Permintaan Pengguna:\n{req.prompt}\n\n"
            "Jawab dengan menggunakan bahasa Indonesia yang profesional, jelas, dan berikan actionable insights."
        )
        
        # Safe Logging: Do not log the actual prompt or user data.
        est_tokens = len(full_prompt.split()) * 1.3
        ai_logger.info(
            f"AI_CALL_METADATA: prompt_length={len(req.prompt)} chars, "
            f"est_tokens={est_tokens:.0f}, period=ALL_TIME, "
            f"sensor_records_summarized={sensor_summary['count']}, "
            f"feed_records={feed_summary['count']}, alert_records={alert_summary['count']}"
        )
        
        client = Groq(api_key=groq_api_key)
        chat_completion = client.chat.completions.create(
            messages=[{"role": "user", "content": full_prompt}],
            model="llama-3.3-70b-versatile",
        )
        response = chat_completion.choices[0].message.content
        return {"analysis": response}
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Gagal memproses AI: {str(e)}")
    finally:
        conn.close()

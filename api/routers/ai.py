import os
import json
import logging
from datetime import datetime
from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from typing import List, Optional
from dotenv import load_dotenv
from groq import Groq
from data_manager import get_db_connection
from api.routers.auth import get_current_user

router = APIRouter()
load_dotenv()

# Setup safe logger
logging.basicConfig(level=logging.INFO)
ai_logger = logging.getLogger("ai_telemetry")

class Message(BaseModel):
    role: str
    content: str

class AIRequest(BaseModel):
    prompt: str
    chat_id: Optional[int] = None
    history: Optional[List[Message]] = []

def get_maggot_data(conn, start_date: str, end_date: str) -> str:
    """
    Fetch summarized maggot cultivation data for a specific date range.
    Expected format for dates: YYYY-MM-DD
    """
    try:
        # Append safe time boundaries for created_at which is DATETIME
        start_dt = f"{start_date} 00:00:00"
        end_dt = f"{end_date} 23:59:59"
        
        feed = conn.execute(
            "SELECT SUM(feed_weight_kg) as total_feed, COUNT(*) as count FROM feed_logs WHERE date >= ? AND date <= ?",
            (start_date, end_date)
        ).fetchone()
        
        weight = conn.execute(
            "SELECT MIN(maggot_weight_kg) as min_w, MAX(maggot_weight_kg) as max_w FROM weight_logs WHERE date >= ? AND date <= ?",
            (start_date, end_date)
        ).fetchone()
        
        sensor = conn.execute(
            "SELECT AVG(temperature) as avg_t, AVG(humidity) as avg_h FROM sensor_logs WHERE created_at >= ? AND created_at <= ?",
            (start_dt, end_dt)
        ).fetchone()
        
        alerts = conn.execute(
            "SELECT COUNT(*) as count FROM alerts WHERE created_at >= ? AND created_at <= ?",
            (start_dt, end_dt)
        ).fetchone()
        
        result = {
            "rentang_waktu": f"{start_date} hingga {end_date}",
            "total_pakan_kg": feed["total_feed"] or 0,
            "jumlah_pemberian_pakan": feed["count"] or 0,
            "berat_maggot_terkecil_kg": weight["min_w"] or 0,
            "berat_maggot_terbesar_kg": weight["max_w"] or 0,
            "rata_rata_suhu": round(sensor["avg_t"] or 0, 2),
            "rata_rata_kelembapan": round(sensor["avg_h"] or 0, 2),
            "jumlah_anomali_peringatan": alerts["count"] or 0
        }
        return json.dumps(result)
    except Exception as e:
        return json.dumps({"error": f"Failed to retrieve data: {str(e)}"})

# Define Groq Tool
tools = [
    {
        "type": "function",
        "function": {
            "name": "get_maggot_data",
            "description": "Ambil rekap data operasional kandang maggot (suhu, kelembapan, pakan, berat, dan anomali) pada rentang tanggal tertentu. WAJIB dipanggil jika user bertanya tentang data mingguan, harian, atau bulanan.",
            "parameters": {
                "type": "object",
                "properties": {
                    "start_date": {
                        "type": "string",
                        "description": "Tanggal mulai (format: YYYY-MM-DD)",
                    },
                    "end_date": {
                        "type": "string",
                        "description": "Tanggal akhir (format: YYYY-MM-DD)",
                    }
                },
                "required": ["start_date", "end_date"],
            },
        },
    }
]

@router.get("/chats")
def get_chats(user: dict = Depends(get_current_user)):
    conn = get_db_connection()
    try:
        chats = conn.execute(
            "SELECT id, title, created_at FROM ai_chats WHERE user_id = ? ORDER BY created_at DESC",
            (user.get("user_id"),)
        ).fetchall()
        return [dict(c) for c in chats]
    finally:
        conn.close()

@router.get("/chats/{chat_id}")
def get_chat_messages(chat_id: int, user: dict = Depends(get_current_user)):
    conn = get_db_connection()
    try:
        # Verify ownership
        chat = conn.execute("SELECT * FROM ai_chats WHERE id = ? AND user_id = ?", (chat_id, user.get("user_id"))).fetchone()
        if not chat:
            raise HTTPException(status_code=404, detail="Chat not found")
            
        messages = conn.execute(
            "SELECT role, content FROM ai_chat_messages WHERE chat_id = ? ORDER BY id ASC",
            (chat_id,)
        ).fetchall()
        return [dict(m) for m in messages]
    finally:
        conn.close()

@router.delete("/chats/{chat_id}")
def delete_chat(chat_id: int, user: dict = Depends(get_current_user)):
    conn = get_db_connection()
    try:
        chat = conn.execute("SELECT * FROM ai_chats WHERE id = ? AND user_id = ?", (chat_id, user.get("user_id"))).fetchone()
        if not chat:
            raise HTTPException(status_code=404, detail="Chat not found")
            
        conn.execute("DELETE FROM ai_chats WHERE id = ?", (chat_id,))
        conn.commit()
        return {"status": "success", "message": "Chat deleted"}
    finally:
        conn.close()

@router.post("/analyze")
def analyze(req: AIRequest, user: dict = Depends(get_current_user)):
    groq_api_key = os.getenv("GROQ_API_KEY")
    if not groq_api_key:
        raise HTTPException(status_code=500, detail="GROQ_API_KEY tidak ditemukan di .env")
        
    conn = get_db_connection()
    try:
        today_str = datetime.now().strftime("%Y-%m-%d")
        system_prompt = (
            "Anda adalah AI asisten spesialis untuk budidaya Maggot BSF (Black Soldier Fly).\n"
            f"TUGAS UTAMA: Analisis data kandang dan berikan insight actionable. Jika pengguna bertanya soal data hari/minggu/bulan tertentu, GUNAKAN TOOL get_maggot_data untuk mengambil rentang tanggal yang diminta. Hari ini adalah tanggal {today_str}.\n\n"
            "ATURAN KETAT (PROMPT GUARD):\n"
            "1. DILARANG KERAS membuat kode pemrograman apapun (HTML, CSS, JavaScript, Python, dll) walaupun diminta secara eksplisit.\n"
            "2. JIKA pengguna meminta kode pemrograman, tolak dengan tegas dan katakan Anda hanya asisten analisis data Maggot.\n"
            "3. TOLAK semua pertanyaan yang tidak berhubungan dengan Maggot BSF, IoT, atau data operasional kandang.\n"
            "4. Jawab dalam bahasa Indonesia profesional, singkat, padat, dan jelas.\n"
        )
        
        messages_to_send = [{"role": "system", "content": system_prompt}]
        
        # Load messages from DB if chat_id exists, otherwise use req.history fallback
        chat_id = req.chat_id
        
        if chat_id:
            # Verify chat ownership
            chat = conn.execute("SELECT * FROM ai_chats WHERE id = ? AND user_id = ?", (chat_id, user.get("user_id"))).fetchone()
            if not chat:
                raise HTTPException(status_code=404, detail="Chat not found")
                
            db_messages = conn.execute("SELECT role, content FROM ai_chat_messages WHERE chat_id = ? ORDER BY id ASC", (chat_id,)).fetchall()
            for msg in db_messages:
                messages_to_send.append({"role": msg["role"], "content": msg["content"]})
        else:
            for msg in req.history:
                if msg.role in ["user", "assistant"]:
                    messages_to_send.append({"role": msg.role, "content": msg.content})
                
        messages_to_send.append({"role": "user", "content": req.prompt})
        
        # Safe Logging
        ai_logger.info(
            f"AI_CALL_METADATA: prompt_length={len(req.prompt)} chars, "
            f"history_length={len(messages_to_send)-2}, tool_enabled=True"
        )
        
        client = Groq(api_key=groq_api_key)
        
        # First call to see if AI wants to use tools
        chat_completion = client.chat.completions.create(
            messages=messages_to_send,
            model="llama-3.3-70b-versatile",
            tools=tools,
            tool_choice="auto",
            max_tokens=4096
        )
        
        response_message = chat_completion.choices[0].message
        tool_calls = response_message.tool_calls
        
        # Fallback manual parsing if Llama 3.3 outputs raw XML tool call in content
        if not tool_calls and response_message.content and "<function=get_maggot_data>" in response_message.content:
            import re
            match = re.search(r'<function=get_maggot_data>(.*?)</function>', response_message.content)
            if match:
                try:
                    args = json.loads(match.group(1))
                    data_json = get_maggot_data(conn, args.get("start_date"), args.get("end_date"))
                    
                    messages_to_send.append({"role": "assistant", "content": response_message.content})
                    messages_to_send.append({"role": "user", "content": f"System Tool Response:\n{data_json}\n\nSekarang jawab pertanyaan saya berdasarkan data di atas."})
                    
                    second_completion = client.chat.completions.create(
                        messages=messages_to_send,
                        model="llama-3.3-70b-versatile",
                        max_tokens=4096
                    )
                    response_message = second_completion.choices[0].message
                except json.JSONDecodeError:
                    pass # Silently fail and use original response
        
        if getattr(response_message, "tool_calls", None):
            tool_calls = response_message.tool_calls
            # Append the assistant's tool call message
            messages_to_send.append(
                {
                    "role": "assistant",
                    "content": response_message.content,
                    "tool_calls": [
                        {
                            "id": t.id,
                            "type": "function",
                            "function": {
                                "name": t.function.name,
                                "arguments": t.function.arguments,
                            }
                        } for t in tool_calls
                    ]
                }
            )
            
            # Execute tool
            for tool_call in tool_calls:
                if tool_call.function.name == "get_maggot_data":
                    args = json.loads(tool_call.function.arguments)
                    data_json = get_maggot_data(conn, args.get("start_date"), args.get("end_date"))
                    
                    messages_to_send.append(
                        {
                            "tool_call_id": tool_call.id,
                            "role": "tool",
                            "name": tool_call.function.name,
                            "content": data_json,
                        }
                    )
            
            # Second call to get final response after tool execution
            second_completion = client.chat.completions.create(
                messages=messages_to_send,
                model="llama-3.3-70b-versatile",
                max_tokens=4096
            )
            final_response = second_completion.choices[0].message.content
        else:
            final_response = response_message.content
        
        # Save to DB
        if not chat_id:
            title = req.prompt[:30] + "..." if len(req.prompt) > 30 else req.prompt
            cursor = conn.cursor()
            cursor.execute("INSERT INTO ai_chats (user_id, title) VALUES (?, ?)", (user.get("user_id"), title))
            chat_id = cursor.lastrowid
            
            # If it's a new chat, also save any history passed by client just in case
            if req.history:
                for msg in req.history:
                    if msg.role in ["user", "assistant"]:
                        conn.execute("INSERT INTO ai_chat_messages (chat_id, role, content) VALUES (?, ?, ?)", (chat_id, msg.role, msg.content))
        
        conn.execute("INSERT INTO ai_chat_messages (chat_id, role, content) VALUES (?, ?, ?)", (chat_id, "user", req.prompt))
        conn.execute("INSERT INTO ai_chat_messages (chat_id, role, content) VALUES (?, ?, ?)", (chat_id, "assistant", final_response))
        conn.commit()
        
        return {"analysis": final_response, "chat_id": chat_id}
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Gagal memproses AI: {str(e)}")
    finally:
        conn.close()

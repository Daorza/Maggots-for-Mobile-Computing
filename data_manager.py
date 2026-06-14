import json
import os
import re
from datetime import datetime, date
from config import (
    AUTH_DB_FILE, DEFAULT_PHASE_LIMITS,
    MAX_TEXT_FIELD_CHARS, INJECTION_PATTERNS, PROMPT_CONTROL_CHARS
)

import sqlite3
from config import AUTH_DB_FILE

import sqlite3
from config import AUTH_DB_FILE

def get_db_connection():
    conn = sqlite3.connect(AUTH_DB_FILE, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    return conn

def calculate_auto_phase(start_date_str):
    if not start_date_str:
        return "Telur"
    try:
        start_date = datetime.strptime(start_date_str.split(" ")[0], "%Y-%m-%d").date()
        age = (date.today() - start_date).days
        if age <= 3: return "Telur"
        elif age <= 18: return "Larva"
        elif age <= 23: return "Prepupa"
        elif age <= 32: return "Pupa"
        else: return "Lalat Dewasa"
    except Exception:
        return "Telur"

def active_limits():
    conn = get_db_connection()
    try:
        settings = conn.execute("SELECT * FROM cultivation_settings ORDER BY id DESC LIMIT 1").fetchone()
        
        if not settings:
            active_phase = "Telur"
            is_auto = True
        else:
            if settings["phase_override_enabled"] == 1 and settings["manual_phase"]:
                active_phase = settings["manual_phase"]
                is_auto = False
            else:
                active_phase = calculate_auto_phase(settings["cultivation_start_date"])
                is_auto = True

        thresholds = conn.execute("SELECT * FROM phase_thresholds WHERE phase = ?", (active_phase,)).fetchone()
        
        limits = {}
        if thresholds:
            limits = {
                "tempMin": thresholds["temperature_min"],
                "tempMax": thresholds["temperature_max"],
                "humidMin": thresholds["humidity_min"],
                "humidMax": thresholds["humidity_max"]
            }
        else:
            # Fallback
            limits = {"tempMin": 27.0, "tempMax": 30.0, "humidMin": 60.0, "humidMax": 80.0}
            
        return {
            "phase": active_phase,
            "is_auto": is_auto,
            "limits": limits
        }
    finally:
        conn.close()

def contains_injection_pattern(value):
    normalized = str(value or "").lower()
    return any(re.search(pattern, normalized, flags=re.IGNORECASE) for pattern in INJECTION_PATTERNS)

def sanitize_text_field(value, field_label):
    raw = str(value or "").strip()
    if contains_injection_pattern(raw):
        return None, f"{field_label} mengandung pola instruksi yang tidak diizinkan."
    sanitized = raw.translate(PROMPT_CONTROL_CHARS)
    sanitized = re.sub(r"[\r\n]+", " ", sanitized)
    sanitized = re.sub(r"\s{2,}", " ", sanitized).strip()
    if len(sanitized) > MAX_TEXT_FIELD_CHARS:
        sanitized = sanitized[:MAX_TEXT_FIELD_CHARS].rstrip()
    return sanitized, None

def sanitize_log_rows_for_ai(rows, text_fields):
    sanitized_rows = []
    for row in rows:
        if not isinstance(row, dict):
            continue
        clean_row = dict(row)
        blocked = False
        for field_name, field_label in text_fields.items():
            clean_value, error = sanitize_text_field(clean_row.get(field_name, ""), field_label)
            if error:
                blocked = True
                break
            clean_row[field_name] = clean_value
        if not blocked:
            sanitized_rows.append(clean_row)
    return sanitized_rows

def validate_ai_response(content):
    text = str(content or "").strip()
    if len(text) < 200:
        return None, "Respons AI terlalu pendek untuk digunakan. Coba lagi setelah data lebih lengkap."
    if contains_injection_pattern(text):
        return None, "Respons AI tidak valid."
    return text, None

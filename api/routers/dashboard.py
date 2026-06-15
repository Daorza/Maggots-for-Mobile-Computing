# pyrefly: ignore [missing-import]
from fastapi import APIRouter
from typing import Optional
from data_manager import get_db_connection, active_limits
from datetime import datetime, timedelta

router = APIRouter()

@router.get("/metrics")
def get_dashboard_metrics():
    conn = get_db_connection()
    try:
        latest_sensor = conn.execute("SELECT * FROM sensor_logs ORDER BY id DESC LIMIT 1").fetchone()
        if latest_sensor:
            latest_temp = latest_sensor["temperature"]
            latest_hum = latest_sensor["humidity"]
            timestamp = latest_sensor["created_at"]
        else:
            latest_temp, latest_hum, timestamp = 0.0, 0.0, "N/A"

        # Calculate production
        weights = conn.execute("SELECT maggot_weight_kg FROM weight_logs ORDER BY date ASC").fetchall()
        if not weights:
            latest_berat = 0.0
            produksi = 0.0
        elif len(weights) == 1:
            latest_berat = weights[0]["maggot_weight_kg"]
            produksi = latest_berat
        else:
            latest_berat = weights[-1]["maggot_weight_kg"]
            produksi = max(0.0, latest_berat - weights[0]["maggot_weight_kg"])

        phase_info = active_limits()

        return {
            "sensor": {
                "temperature": latest_temp,
                "humidity": latest_hum,
                "timestamp": timestamp,
            },
            "fase": phase_info,
            "produksi": {
                "berat_maggot": latest_berat,
                "total_produksi": produksi
            }
        }
    finally:
        conn.close()

@router.get("/monitoring")
def get_monitoring_data(limit: int = 100):
    conn = get_db_connection()
    try:
        logs = conn.execute("SELECT created_at as timestamp, temperature, humidity FROM sensor_logs ORDER BY id DESC LIMIT ?", (limit,)).fetchall()
        data = [dict(row) for row in reversed(logs)]
        return {"data": data}
    finally:
        conn.close()

from config import BROKER, PORT

@router.get("/mqtt-config")
def get_mqtt_config():
    return {"broker": BROKER, "port": PORT}

@router.get("/status")
def get_device_status():
    conn = get_db_connection()
    try:
        latest = conn.execute("SELECT created_at, temperature, humidity FROM sensor_logs ORDER BY id DESC LIMIT 1").fetchone()
        
        from mqtt_worker import is_mqtt_connected_flag
        mqtt_connected = is_mqtt_connected_flag
        last_seen = None
        
        if latest:
            last_seen = latest["created_at"]
                
        phase_info = active_limits()
        
        return {
            "mqtt_connected": mqtt_connected,
            "last_seen": last_seen,
            "last_temperature": latest["temperature"] if latest else None,
            "last_humidity": latest["humidity"] if latest else None,
            "active_phase": phase_info["phase"],
            "active_threshold": phase_info["limits"],
            "is_auto": phase_info["is_auto"]
        }
    finally:
        conn.close()

from pydantic import BaseModel

class SettingsUpdate(BaseModel):
    phase_override_enabled: int
    manual_phase: str

@router.post("/settings")
def update_settings(req: SettingsUpdate):
    conn = get_db_connection()
    try:
        # We always keep the same cultivation_start_date but update the override settings
        # Let's get the latest row
        latest = conn.execute("SELECT * FROM cultivation_settings ORDER BY id DESC LIMIT 1").fetchone()
        user_id = latest["user_id"] if latest else None
        start_date = latest["cultivation_start_date"] if latest else datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S")
        
        conn.execute("""
            INSERT INTO cultivation_settings (user_id, cultivation_start_date, phase_override_enabled, manual_phase)
            VALUES (?, ?, ?, ?)
        """, (user_id, start_date, req.phase_override_enabled, req.manual_phase))
        conn.commit()
        
        from mqtt_worker import publish_fase
        if req.phase_override_enabled == 1 and req.manual_phase:
            publish_fase(req.manual_phase)
            
        return {"status": "success"}
    finally:
        conn.close()

@router.post("/mqtt-reconnect")
def reconnect_mqtt():
    from mqtt_worker import force_reconnect
    success = force_reconnect()
    if success:
        return {"status": "success", "message": "Berhasil memicu koneksi ulang MQTT"}
    return {"status": "error", "message": "Gagal memicu koneksi ulang"}

from typing import List

class ThresholdUpdate(BaseModel):
    phase: str
    temperature_min: float
    temperature_max: float
    humidity_min: float
    humidity_max: float

class BulkThresholdUpdate(BaseModel):
    thresholds: List[ThresholdUpdate]

@router.get("/thresholds")
def get_thresholds():
    conn = get_db_connection()
    try:
        data = conn.execute("SELECT phase, temperature_min, temperature_max, humidity_min, humidity_max FROM phase_thresholds").fetchall()
        return {"thresholds": [dict(row) for row in data]}
    finally:
        conn.close()

@router.put("/thresholds")
def update_thresholds(req: BulkThresholdUpdate):
    conn = get_db_connection()
    try:
        from mqtt_worker import publish_limits
        for th in req.thresholds:
            conn.execute("""
                UPDATE phase_thresholds 
                SET temperature_min = ?, temperature_max = ?, humidity_min = ?, humidity_max = ?, updated_at = CURRENT_TIMESTAMP
                WHERE phase = ?
            """, (th.temperature_min, th.temperature_max, th.humidity_min, th.humidity_max, th.phase))
            
            # Publish to ESP32
            payload = {
                "fase": th.phase,
                "tempMin": th.temperature_min,
                "tempMax": th.temperature_max,
                "humidMin": th.humidity_min,
                "humidMax": th.humidity_max
            }
            publish_limits(payload)
            
        conn.commit()
        return {"status": "success", "message": "Ambang batas berhasil diperbarui"}
    except Exception as e:
        return {"status": "error", "message": str(e)}
    finally:
        conn.close()

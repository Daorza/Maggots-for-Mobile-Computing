import json
import os
import ssl
import time
import threading
from collections import deque
from datetime import datetime
import paho.mqtt.client as mqtt

from config import (
    BROKER, PORT, USERNAME, PASSWORD, TOPIC_SENSOR, TOPIC_STATUS, TOPIC_STATUS_BATAS, TOPIC_KONTROL, TOPIC_BATAS
)

_conn_log = deque(maxlen=8)
_client = None

from data_manager import get_db_connection, active_limits
from config import SENSOR_LOG_INTERVAL_SECONDS

last_sensor_log_time = 0
is_mqtt_connected_flag = False
last_alert_time = {"temperature": 0.0, "humidity": 0.0}
ALERT_COOLDOWN_SECONDS = 600

def _mqtt_worker():
    def on_connect(client, userdata, flags, reason_code, properties=None):
        global is_mqtt_connected_flag
        rc = reason_code if isinstance(reason_code, int) else reason_code.value
        if rc == 0:
            _conn_log.append(f"[OK] Connected -> {BROKER}:{PORT}")
            is_mqtt_connected_flag = True
            client.subscribe(TOPIC_SENSOR)
        else:
            _conn_log.append(f"[ERR] Connect failed: rc={rc}")

    def on_disconnect(client, userdata, flags, reason_code, properties=None):
        global is_mqtt_connected_flag
        is_mqtt_connected_flag = False
        _conn_log.append(f"[ERR] Disconnected: rc={reason_code}")

    def on_message(client, userdata, msg):
        global last_sensor_log_time
        topic = msg.topic
        payload = msg.payload.decode("utf-8").strip()

        if topic == TOPIC_SENSOR:
            try:
                data = json.loads(payload)
                suhu = float(data.get("suhu", data.get("temperature", data.get("temp", 0))))
                kelembapan = float(data.get("kelembapan", data.get("humidity", data.get("hum", 0))))
                
                now = time.time()
                if now - last_sensor_log_time >= SENSOR_LOG_INTERVAL_SECONDS:
                    last_sensor_log_time = now
                    
                    # 1. Retrieve Active Phase & Limits
                    phase_info = active_limits()
                    current_phase = phase_info["phase"]
                    limits = phase_info["limits"]
                    
                    # 2. Insert into sensor_logs
                    conn = get_db_connection()
                    try:
                        conn.execute("""
                            INSERT INTO sensor_logs (temperature, humidity, phase)
                            VALUES (?, ?, ?)
                        """, (suhu, kelembapan, current_phase))
                        
                        # 3. Check for Alerts with Cooldown
                        alerts_to_insert = []
                        if suhu < limits["tempMin"] or suhu > limits["tempMax"]:
                            if now - last_alert_time["temperature"] >= ALERT_COOLDOWN_SECONDS:
                                severity = "danger" if (suhu < limits["tempMin"] - 2 or suhu > limits["tempMax"] + 2) else "warning"
                                msg = f"Suhu tidak normal: {suhu}°C (Batas: {limits['tempMin']}-{limits['tempMax']})"
                                alerts_to_insert.append(("temperature", severity, msg, suhu, limits["tempMin"], limits["tempMax"]))
                                last_alert_time["temperature"] = now
                            
                        if kelembapan < limits["humidMin"] or kelembapan > limits["humidMax"]:
                            if now - last_alert_time["humidity"] >= ALERT_COOLDOWN_SECONDS:
                                severity = "danger" if (kelembapan < limits["humidMin"] - 10 or kelembapan > limits["humidMax"] + 10) else "warning"
                                msg = f"Kelembapan tidak normal: {kelembapan}% (Batas: {limits['humidMin']}-{limits['humidMax']})"
                                alerts_to_insert.append(("humidity", severity, msg, kelembapan, limits["humidMin"], limits["humidMax"]))
                                last_alert_time["humidity"] = now
                            
                        for alert in alerts_to_insert:
                            conn.execute("""
                                INSERT INTO alerts (type, severity, message, value, min_threshold, max_threshold, phase)
                                VALUES (?, ?, ?, ?, ?, ?, ?)
                            """, (*alert, current_phase))
                            
                        conn.commit()
                    finally:
                        conn.close()

            except Exception as e:
                import traceback
                print(f"[MQTT ERROR] sensor loop: {e}")
                traceback.print_exc()
                _conn_log.append(f"[ERR] sensor loop: {e}")

    def on_disconnect(client, userdata, flags, reason_code, properties=None):
        global is_mqtt_connected_flag
        is_mqtt_connected_flag = False
        rc = reason_code if isinstance(reason_code, int) else reason_code.value
        _conn_log.append(f"[DISC] rc={rc} - reconnecting...")

    global _client
    _client = mqtt.Client(
        mqtt.CallbackAPIVersion.VERSION2,
        client_id=f"bsf-dash-{int(time.time() * 1000) % 99999}",
        clean_session=True,
    )
    _client.username_pw_set(USERNAME, PASSWORD)
    _client.tls_set(cert_reqs=ssl.CERT_REQUIRED, tls_version=ssl.PROTOCOL_TLS_CLIENT)
    _client.on_connect = on_connect
    _client.on_message = on_message
    _client.on_disconnect = on_disconnect

    _conn_log.append(f"[INFO] Connecting -> {BROKER}:{PORT}")
    while True:
        try:
            _client.connect(BROKER, PORT, keepalive=60)
            _client.loop_forever()
        except Exception as e:
            _conn_log.append(f"[ERR] {str(e)[:60]} - retry 5s")
            time.sleep(5)

def mqtt_loop(daemon=True):
    threading.Thread(target=_mqtt_worker, daemon=daemon).start()
def _pub_thread(topic, payload_str):
    def _run():
        try:
            c = mqtt.Client(
                mqtt.CallbackAPIVersion.VERSION2,
                client_id=f"bsf-pub-{int(time.time() * 1000) % 99999}",
                clean_session=True,
            )
            c.username_pw_set(USERNAME, PASSWORD)
            c.tls_set(cert_reqs=ssl.CERT_REQUIRED, tls_version=ssl.PROTOCOL_TLS_CLIENT)
            c.connect(BROKER, PORT, keepalive=10)
            c.publish(topic, payload_str, qos=1)
            c.loop(timeout=2)
            c.disconnect()
        except Exception as e:
            _conn_log.append(f"[PUB ERR] {e}")

    threading.Thread(target=_run, daemon=True).start()

def publish_fase(fase_str):
    _pub_thread(TOPIC_KONTROL, fase_str)

def force_reconnect():
    global _client
    if _client:
        try:
            _client.reconnect()
            return True
        except Exception as e:
            _conn_log.append(f"[ERR] Reconnect manual gagal: {e}")
            return False
    return False

def publish_limits(payload_dict):
    _pub_thread(TOPIC_BATAS, json.dumps(payload_dict))

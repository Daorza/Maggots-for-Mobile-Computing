import streamlit as st
import paho.mqtt.client as mqtt
import json
import pandas as pd
import threading
import time
import os
from datetime import datetime
from collections import deque

# ── Config ────────────────────────────────────────────────────────────────────
BROKER_IP   = "10.30.91.86"
BROKER_PORT = 1883
TOPIC       = "iot/sensor"
MAX_POINTS  = 100
DATA_FILE   = "/tmp/iot_sensor_data.json"  # File jembatan antar re-run
REFRESH_SEC = 2

# ── Page Config ───────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="IoT Dashboard ESP32",
    page_icon="🌡️",
    layout="wide",
    initial_sidebar_state="collapsed",
)

st.markdown("""
<style>
  @import url('https://fonts.googleapis.com/css2?family=Space+Mono:wght@400;700&family=Syne:wght@400;600;800&display=swap');
  html, body, [class*="css"] { font-family: 'Syne', sans-serif; background-color: #0d1117; color: #e6edf3; }
  .stApp { background: #0d1117; }
  #MainMenu, footer, header { visibility: hidden; }
  h1, h2, h3 { font-family: 'Syne', sans-serif !important; font-weight: 800 !important; color: #e6edf3 !important; }
  .metric-card { background: #161b22; border: 1px solid #30363d; border-radius: 12px; padding: 20px 24px; text-align: center; }
  .metric-label { font-family: 'Space Mono', monospace; font-size: 0.7rem; letter-spacing: 2px; text-transform: uppercase; color: #8b949e; margin-bottom: 6px; }
  .metric-value { font-family: 'Space Mono', monospace; font-size: 2.2rem; font-weight: 700; line-height: 1; }
  .metric-unit { font-size: 1rem; color: #8b949e; margin-left: 4px; }
  .temp-value { color: #ff7b72; }
  .hum-value  { color: #58a6ff; }
  .chart-header { font-family: 'Space Mono', monospace; font-size: 0.75rem; letter-spacing: 3px; text-transform: uppercase; color: #8b949e; margin-bottom: 8px; padding-bottom: 8px; border-bottom: 1px solid #21262d; }
  .status-badge { display: inline-block; font-family: 'Space Mono', monospace; font-size: 0.65rem; letter-spacing: 1.5px; text-transform: uppercase; padding: 3px 10px; border-radius: 20px; }
  .status-live { background: rgba(35,134,54,0.15); color: #3fb950; border: 1px solid rgba(63,185,80,0.3); }
  .status-waiting { background: rgba(187,128,9,0.15); color: #d29922; border: 1px solid rgba(210,153,34,0.3); }
  hr { border-color: #21262d !important; }
</style>
""", unsafe_allow_html=True)


# ── MQTT Thread (berjalan sekali, terpisah dari Streamlit) ────────────────────
def _mqtt_worker():
    """
    Berjalan di background thread.
    Tulis data ke file JSON agar bisa dibaca lintas Streamlit re-run.
    """
    buffer = deque(maxlen=MAX_POINTS)

    # Baca data lama kalau ada
    if os.path.exists(DATA_FILE):
        try:
            with open(DATA_FILE) as f:
                old = json.load(f)
            buffer.extend(old[-MAX_POINTS:])
        except Exception:
            pass

    def on_message(client, userdata, msg):
        try:
            data = json.loads(msg.payload.decode())
            data["timestamp"] = datetime.now().strftime("%H:%M:%S")
            buffer.append(data)
            with open(DATA_FILE, "w") as f:
                json.dump(list(buffer), f)
        except Exception as e:
            print(f"[MQTT] Parse error: {e}")

    def on_connect(client, userdata, flags, rc):
        if rc == 0:
            print(f"[MQTT] Connected ke {BROKER_IP}:{BROKER_PORT}")
            client.subscribe(TOPIC)
        else:
            print(f"[MQTT] Gagal connect, rc={rc}")

    def on_disconnect(client, userdata, rc):
        print(f"[MQTT] Disconnected (rc={rc}), mencoba reconnect...")

    client = mqtt.Client(client_id="streamlit-dashboard", clean_session=True)
    client.on_connect    = on_connect
    client.on_message    = on_message
    client.on_disconnect = on_disconnect

    while True:
        try:
            client.connect(BROKER_IP, BROKER_PORT, keepalive=60)
            client.loop_forever()
        except Exception as e:
            print(f"[MQTT] Connection error: {e} — retry in 5s")
            time.sleep(5)

# Jalankan thread MQTT hanya sekali per proses Python
if "mqtt_thread_started" not in st.session_state:
    t = threading.Thread(target=_mqtt_worker, daemon=True)
    t.start()
    st.session_state["mqtt_thread_started"] = True


# ── Baca data dari file ───────────────────────────────────────────────────────
def load_data():
    if not os.path.exists(DATA_FILE):
        return []
    try:
        with open(DATA_FILE) as f:
            return json.load(f)
    except Exception:
        return []


# ── UI ────────────────────────────────────────────────────────────────────────
data_list = load_data()
has_data  = len(data_list) > 0

# Header
col_title, col_status = st.columns([5, 1])
with col_title:
    st.markdown("## 🌡️ IoT Dashboard — ESP32")
with col_status:
    st.markdown("<br>", unsafe_allow_html=True)
    if has_data:
        st.markdown('<span class="status-badge status-live">● LIVE</span>', unsafe_allow_html=True)
    else:
        st.markdown('<span class="status-badge status-waiting">○ WAITING</span>', unsafe_allow_html=True)

st.markdown("---")

# ── Metric cards ──────────────────────────────────────────────────────────────
latest_temp = latest_hum = "—"
min_temp = max_temp = min_hum = max_hum = None
df = None

if has_data:
    df = pd.DataFrame(data_list)

    if "temperature" in df.columns:
        latest_temp = f"{df['temperature'].iloc[-1]:.1f}"
        min_temp    = df["temperature"].min()
        max_temp    = df["temperature"].max()

    if "humidity" in df.columns:
        latest_hum = f"{df['humidity'].iloc[-1]:.1f}"
        min_hum    = df["humidity"].min()
        max_hum    = df["humidity"].max()

c1, c2, c3, c4, c5, c6 = st.columns(6)
cards = [
    (c1, "Temperature", latest_temp, "°C", "temp-value"),
    (c2, "Min Temp",    f"{min_temp:.1f}" if min_temp is not None else "—", "°C", "temp-value"),
    (c3, "Max Temp",    f"{max_temp:.1f}" if max_temp is not None else "—", "°C", "temp-value"),
    (c4, "Humidity",    latest_hum,  "%",  "hum-value"),
    (c5, "Min Hum",     f"{min_hum:.1f}"  if min_hum  is not None else "—", "%",  "hum-value"),
    (c6, "Max Hum",     f"{max_hum:.1f}"  if max_hum  is not None else "—", "%",  "hum-value"),
]
for col, label, val, unit, cls in cards:
    with col:
        st.markdown(f"""
        <div class="metric-card">
          <div class="metric-label">{label}</div>
          <div class="metric-value {cls}">{val}<span class="metric-unit">{unit}</span></div>
        </div>""", unsafe_allow_html=True)

st.markdown("<br>", unsafe_allow_html=True)

# ── Charts ────────────────────────────────────────────────────────────────────
col_temp, col_hum = st.columns(2)

with col_temp:
    st.markdown('<div class="chart-header">🔴 Temperature (°C)</div>', unsafe_allow_html=True)
    if has_data and df is not None and "temperature" in df.columns:
        temp_df = df[["temperature"]].copy()
        if "timestamp" in df.columns:
            temp_df.index = df["timestamp"]
        st.line_chart(temp_df, color="#ff7b72", height=280)
    else:
        st.info("⏳ Menunggu data temperature dari sensor...")

with col_hum:
    st.markdown('<div class="chart-header">🔵 Humidity (%)</div>', unsafe_allow_html=True)
    if has_data and df is not None and "humidity" in df.columns:
        hum_df = df[["humidity"]].copy()
        if "timestamp" in df.columns:
            hum_df.index = df["timestamp"]
        st.line_chart(hum_df, color="#58a6ff", height=280)
    else:
        st.info("⏳ Menunggu data humidity dari sensor...")

# ── Footer ────────────────────────────────────────────────────────────────────
st.markdown("---")
fl, fr = st.columns([3, 1])
with fl:
    st.caption(f"📡 Broker: `{BROKER_IP}:{BROKER_PORT}` | Topic: `{TOPIC}` | Buffer: {len(data_list)}/{MAX_POINTS} data points")
with fr:
    col_btn, col_clr = st.columns(2)
    with col_btn:
        if st.button("🔄 Refresh"):
            st.rerun()
    with col_clr:
        if st.button("🗑️ Clear"):
            if os.path.exists(DATA_FILE):
                os.remove(DATA_FILE)
            st.rerun()

# ── Auto-refresh ──────────────────────────────────────────────────────────────
time.sleep(REFRESH_SEC)
st.rerun()

# Jalankan:
# streamlit run dashboard.py
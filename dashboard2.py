import streamlit as st
import paho.mqtt.client as mqtt
import json
import pandas as pd
import threading
import time
import os
from datetime import datetime
from collections import deque

# ── Config ─────────────────────────────────────────────────────────────────────
BROKER_IP   = "10.30.91.86"
BROKER_PORT = 1883
TOPIC       = "iot/sensor"
MAX_POINTS  = 100
DATA_FILE   = "/tmp/iot_sensor_data.json"
REFRESH_SEC = 2

# ── Page Config ────────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="ESP32 Sensor Monitor",
    page_icon="🌡️",
    layout="wide",
    initial_sidebar_state="collapsed",
)

st.markdown("""
<style>
  @import url('https://fonts.googleapis.com/css2?family=JetBrains+Mono:wght@300;400;600;700&family=Bebas+Neue&family=DM+Sans:wght@300;400;500;600&display=swap');

  :root {
    --bg:        #080c10;
    --surface:   #0e1318;
    --border:    #1c2530;
    --border2:   #253040;
    --muted:     #4a6070;
    --text:      #c8d8e8;
    --bright:    #e8f0f8;
    --red:       #ff5050;
    --red-dim:   rgba(255,80,80,0.12);
    --red-glow:  rgba(255,80,80,0.25);
    --blue:      #38b6ff;
    --blue-dim:  rgba(56,182,255,0.12);
    --blue-glow: rgba(56,182,255,0.25);
    --green:     #30d980;
    --amber:     #ffb830;
    --amber-dim: rgba(255,184,48,0.12);
  }

  html, body, [class*="css"] {
    font-family: 'DM Sans', sans-serif;
    background: var(--bg);
    color: var(--text);
  }

  .stApp { background: var(--bg); }
  #MainMenu, footer, header { visibility: hidden; }

  /* ── Metric Cards ── */
  .cards-row { display: grid; grid-template-columns: repeat(3, 1fr); gap: 14px; margin-bottom: 20px; }
  .metric-card {
    background: var(--surface);
    border: 1px solid var(--border);
    border-radius: 14px;
    padding: 22px 24px;
    position: relative;
    overflow: hidden;
    transition: border-color 0.3s;
  }
  .metric-card::before {
    content: '';
    position: absolute;
    top: 0; left: 0; right: 0;
    height: 2px;
    border-radius: 14px 14px 0 0;
  }
  .card-temp::before { background: linear-gradient(90deg, var(--red), transparent); }
  .card-hum::before  { background: linear-gradient(90deg, var(--blue), transparent); }
  .card-stat::before { background: linear-gradient(90deg, var(--amber), transparent); }

  .metric-icon { font-size: 1.2rem; margin-bottom: 8px; }
  .metric-label {
    font-family: 'JetBrains Mono', monospace;
    font-size: 0.62rem;
    letter-spacing: 2.5px;
    text-transform: uppercase;
    color: var(--muted);
    margin-bottom: 10px;
  }
  .metric-big {
    font-family: 'Bebas Neue', sans-serif;
    font-size: 3rem;
    line-height: 1;
    color: var(--bright);
    letter-spacing: 1px;
  }
  .metric-unit { font-size: 1.4rem; color: var(--muted); }
  .metric-sub { font-size: 0.75rem; color: var(--muted); margin-top: 6px; font-family: 'JetBrains Mono', monospace; }
  .metric-sub span { color: var(--text); }
  .val-temp { color: var(--red) !important; }
  .val-hum  { color: var(--blue) !important; }

  /* ── Status Badge ── */
  .status-pill {
    display: inline-flex; align-items: center; gap: 6px;
    font-family: 'JetBrains Mono', monospace;
    font-size: 0.62rem;
    letter-spacing: 2px;
    text-transform: uppercase;
    padding: 5px 12px;
    border-radius: 99px;
    font-weight: 600;
  }
  .pill-live    { background: rgba(48,217,128,0.12); color: var(--green); border: 1px solid rgba(48,217,128,0.3); }
  .pill-waiting { background: rgba(255,184,48,0.12); color: var(--amber); border: 1px solid rgba(255,184,48,0.3); }

  /* ── Condition Badge ── */
  .cond-badge {
    display: inline-block;
    font-family: 'JetBrains Mono', monospace;
    font-size: 0.65rem;
    letter-spacing: 1.5px;
    text-transform: uppercase;
    padding: 3px 10px;
    border-radius: 6px;
    margin-top: 8px;
    font-weight: 600;
  }
  .cond-normal  { background: rgba(48,217,128,0.12); color: var(--green); border: 1px solid rgba(48,217,128,0.3); }
  .cond-warn    { background: rgba(255,184,48,0.12);  color: var(--amber); border: 1px solid rgba(255,184,48,0.3); }
  .cond-danger  { background: rgba(255,80,80,0.12);   color: var(--red);   border: 1px solid rgba(255,80,80,0.3); }

  /* ── Chart section ── */
  .chart-box {
    background: var(--surface);
    border: 1px solid var(--border);
    border-radius: 14px;
    padding: 20px 22px 14px;
    margin-bottom: 14px;
  }
  .chart-title {
    font-family: 'JetBrains Mono', monospace;
    font-size: 0.65rem;
    letter-spacing: 3px;
    text-transform: uppercase;
    color: var(--muted);
    display: flex;
    align-items: center;
    gap: 8px;
    margin-bottom: 4px;
  }
  .chart-title .dot-temp { width: 8px; height: 8px; border-radius: 50%; background: var(--red); display: inline-block; }
  .chart-title .dot-hum  { width: 8px; height: 8px; border-radius: 50%; background: var(--blue); display: inline-block; }

  /* ── Raw Table ── */
  .raw-section {
    background: var(--surface);
    border: 1px solid var(--border);
    border-radius: 14px;
    padding: 18px 22px;
  }

  /* ── Footer ── */
  .footer-bar {
    display: flex;
    justify-content: space-between;
    align-items: center;
    font-family: 'JetBrains Mono', monospace;
    font-size: 0.63rem;
    color: var(--muted);
    letter-spacing: 1px;
    padding-top: 6px;
  }

  /* ── Override Streamlit chart bg ── */
  .element-container iframe { border-radius: 10px; }
  [data-testid="stMetric"] { display: none; }

  /* ── Header ── */
  .page-header {
    display: flex;
    align-items: flex-end;
    justify-content: space-between;
    margin-bottom: 6px;
    padding-bottom: 16px;
    border-bottom: 1px solid var(--border);
  }
  .page-title {
    font-family: 'Bebas Neue', sans-serif;
    font-size: 2.2rem;
    letter-spacing: 3px;
    color: var(--bright);
    line-height: 1;
  }
  .page-sub {
    font-family: 'JetBrains Mono', monospace;
    font-size: 0.62rem;
    color: var(--muted);
    letter-spacing: 2px;
    margin-top: 4px;
  }
  .timestamp-badge {
    font-family: 'JetBrains Mono', monospace;
    font-size: 0.65rem;
    color: var(--muted);
    letter-spacing: 1px;
    text-align: right;
  }
</style>
""", unsafe_allow_html=True)


# ── Condition logic ─────────────────────────────────────────────────────────
def temp_condition(t):
    if t is None:
        return "—", "cond-warn"
    if t < 18:
        return "❄️ Dingin", "cond-warn"
    elif t <= 26:
        return "✅ Normal", "cond-normal"
    elif t <= 32:
        return "🌡️ Hangat", "cond-warn"
    else:
        return "🔥 Panas", "cond-danger"

def hum_condition(h):
    if h is None:
        return "—", "cond-warn"
    if h < 30:
        return "🏜️ Sangat Kering", "cond-danger"
    elif h < 40:
        return "💨 Kurang Lembab", "cond-warn"
    elif h <= 60:
        return "✅ Normal", "cond-normal"
    elif h <= 70:
        return "💧 Agak Lembab", "cond-warn"
    else:
        return "🌊 Terlalu Lembab", "cond-danger"


# ── MQTT Thread ────────────────────────────────────────────────────────────────
def _mqtt_worker():
    buffer = deque(maxlen=MAX_POINTS)

    if os.path.exists(DATA_FILE):
        try:
            with open(DATA_FILE) as f:
                raw = f.read().strip()
                if raw:
                    old = json.loads(raw)
                    if isinstance(old, list):
                        buffer.extend(old[-MAX_POINTS:])
        except Exception as e:
            print(f"[MQTT] Load file error: {e}")

    def on_message(client, userdata, msg):
        try:
            payload = msg.payload.decode("utf-8").strip()
            data = json.loads(payload)

            # Pastikan field ada dan bertipe angka
            entry = {
                "timestamp":   datetime.now().strftime("%H:%M:%S"),
                "temperature": float(data.get("temperature", data.get("temp", 0))),
                "humidity":    float(data.get("humidity",    data.get("hum",  0))),
            }
            buffer.append(entry)

            # Tulis atomik ke file
            tmp = DATA_FILE + ".tmp"
            with open(tmp, "w") as f:
                json.dump(list(buffer), f, ensure_ascii=False)
            os.replace(tmp, DATA_FILE)

        except json.JSONDecodeError as e:
            print(f"[MQTT] JSON error: {e} | payload: {msg.payload}")
        except Exception as e:
            print(f"[MQTT] Error: {e}")

    def on_connect(client, userdata, flags, rc):
        if rc == 0:
            print(f"[MQTT] Connected → {BROKER_IP}:{BROKER_PORT} | topic: {TOPIC}")
            client.subscribe(TOPIC)
        else:
            codes = {1:"bad protocol",2:"client id rejected",3:"server unavailable",4:"bad credentials",5:"not authorized"}
            print(f"[MQTT] Connect failed: {codes.get(rc, f'rc={rc}')}")

    def on_disconnect(client, userdata, rc):
        print(f"[MQTT] Disconnected (rc={rc})")

    client = mqtt.Client(client_id="esp32-dashboard-v2", clean_session=True, protocol=mqtt.MQTTv311)
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


if "mqtt_thread_started" not in st.session_state:
    t = threading.Thread(target=_mqtt_worker, daemon=True)
    t.start()
    st.session_state["mqtt_thread_started"] = True


# ── Load data ─────────────────────────────────────────────────────────────────
def load_data():
    if not os.path.exists(DATA_FILE):
        return []
    try:
        with open(DATA_FILE) as f:
            raw = f.read().strip()
        if not raw:
            return []
        parsed = json.loads(raw)
        if not isinstance(parsed, list):
            return []
        return parsed
    except Exception as e:
        print(f"[UI] Load error: {e}")
        return []


# ── UI ─────────────────────────────────────────────────────────────────────────
data_list = load_data()
has_data  = len(data_list) > 0
now_str   = datetime.now().strftime("%d %b %Y  %H:%M:%S")

# Header
col_h1, col_h2 = st.columns([5, 2])
with col_h1:
    st.markdown(f"""
    <div class="page-header">
      <div>
        <div class="page-title">🌡️ ESP32 SENSOR MONITOR</div>
        <div class="page-sub">MQTT BROKER · {BROKER_IP}:{BROKER_PORT} · {TOPIC}</div>
      </div>
    </div>""", unsafe_allow_html=True)
with col_h2:
    badge_class = "pill-live" if has_data else "pill-waiting"
    badge_dot   = "●" if has_data else "○"
    badge_text  = "LIVE" if has_data else "WAITING"
    st.markdown(f"""
    <div class="page-header" style="justify-content:flex-end; border-bottom:1px solid var(--border); padding-bottom:16px;">
      <div style="text-align:right">
        <div><span class="status-pill {badge_class}">{badge_dot} {badge_text}</span></div>
        <div class="timestamp-badge" style="margin-top:8px">{now_str}</div>
        <div class="timestamp-badge">{len(data_list)} / {MAX_POINTS} data points</div>
      </div>
    </div>""", unsafe_allow_html=True)

# ── Compute values ─────────────────────────────────────────────────────────────
latest_temp = latest_hum = None
min_temp = max_temp = avg_temp = None
min_hum  = max_hum  = avg_hum  = None
df = None

if has_data:
    df = pd.DataFrame(data_list)
    df["temperature"] = pd.to_numeric(df.get("temperature", pd.Series(dtype=float)), errors="coerce")
    df["humidity"]    = pd.to_numeric(df.get("humidity",    pd.Series(dtype=float)), errors="coerce")

    if "temperature" in df.columns and df["temperature"].notna().any():
        latest_temp = df["temperature"].dropna().iloc[-1]
        min_temp    = df["temperature"].min()
        max_temp    = df["temperature"].max()
        avg_temp    = df["temperature"].mean()

    if "humidity" in df.columns and df["humidity"].notna().any():
        latest_hum = df["humidity"].dropna().iloc[-1]
        min_hum    = df["humidity"].min()
        max_hum    = df["humidity"].max()
        avg_hum    = df["humidity"].mean()

temp_cond_label, temp_cond_cls = temp_condition(latest_temp)
hum_cond_label,  hum_cond_cls  = hum_condition(latest_hum)

fmt = lambda v, dec=1: f"{v:.{dec}f}" if v is not None else "—"


# ── Metric Cards ───────────────────────────────────────────────────────────────
col_t, col_h = st.columns(2)

with col_t:
    st.markdown(f"""
    <div class="metric-card card-temp">
      <div class="metric-label">🌡️ Temperature</div>
      <div class="metric-big val-temp">{fmt(latest_temp)}<span class="metric-unit"> °C</span></div>
      <div class="metric-sub">
        min <span>{fmt(min_temp)}</span> &nbsp;·&nbsp;
        max <span>{fmt(max_temp)}</span> &nbsp;·&nbsp;
        avg <span>{fmt(avg_temp)}</span>
      </div>
      <div><span class="cond-badge {temp_cond_cls}">{temp_cond_label}</span></div>
      <div class="metric-sub" style="margin-top:6px">Normal: 18 – 26 °C</div>
    </div>
    """, unsafe_allow_html=True)

with col_h:
    st.markdown(f"""
    <div class="metric-card card-hum">
      <div class="metric-label">💧 Humidity</div>
      <div class="metric-big val-hum">{fmt(latest_hum)}<span class="metric-unit"> %</span></div>
      <div class="metric-sub">
        min <span>{fmt(min_hum)}</span> &nbsp;·&nbsp;
        max <span>{fmt(max_hum)}</span> &nbsp;·&nbsp;
        avg <span>{fmt(avg_hum)}</span>
      </div>
      <div><span class="cond-badge {hum_cond_cls}">{hum_cond_label}</span></div>
      <div class="metric-sub" style="margin-top:6px">Normal: 40 – 60 % RH</div>
    </div>
    """, unsafe_allow_html=True)

st.markdown("<div style='height:16px'></div>", unsafe_allow_html=True)


# ── Charts ─────────────────────────────────────────────────────────────────────
col_ct, col_ch = st.columns(2)

with col_ct:
    st.markdown("""
    <div class="chart-box">
      <div class="chart-title"><span class="dot-temp"></span> Temperature History (°C)</div>
    </div>
    """, unsafe_allow_html=True)
    if has_data and df is not None and "temperature" in df.columns and df["temperature"].notna().any():
        temp_chart = df[["temperature"]].copy()
        if "timestamp" in df.columns:
            temp_chart.index = df["timestamp"]
        st.line_chart(temp_chart, color="#ff5050", height=260, use_container_width=True)
    else:
        st.info("⏳ Menunggu data temperature dari ESP32...")

with col_ch:
    st.markdown("""
    <div class="chart-box">
      <div class="chart-title"><span class="dot-hum"></span> Humidity History (%)</div>
    </div>
    """, unsafe_allow_html=True)
    if has_data and df is not None and "humidity" in df.columns and df["humidity"].notna().any():
        hum_chart = df[["humidity"]].copy()
        if "timestamp" in df.columns:
            hum_chart.index = df["timestamp"]
        st.line_chart(hum_chart, color="#38b6ff", height=260, use_container_width=True)
    else:
        st.info("⏳ Menunggu data humidity dari ESP32...")


# ── Condition Legend ───────────────────────────────────────────────────────────
with st.expander("📋 Tabel Kondisi & Acuan Nilai", expanded=False):
    leg1, leg2 = st.columns(2)
    with leg1:
        st.markdown("**Suhu (°C)**")
        st.markdown("""
| Rentang | Status |
|---------|--------|
| < 18 °C | ❄️ Dingin |
| 18 – 26 °C | ✅ Normal |
| 27 – 32 °C | 🌡️ Hangat |
| > 32 °C | 🔥 Panas |
""")
    with leg2:
        st.markdown("**Kelembapan (% RH)**")
        st.markdown("""
| Rentang | Status |
|---------|--------|
| < 30 % | 🏜️ Sangat Kering |
| 30 – 39 % | 💨 Kurang Lembab |
| 40 – 60 % | ✅ Normal |
| 61 – 70 % | 💧 Agak Lembab |
| > 70 % | 🌊 Terlalu Lembab |
""")


# ── Raw Data Table ─────────────────────────────────────────────────────────────
if has_data and df is not None:
    with st.expander("🗃️ Raw Data (10 terbaru)", expanded=False):
        show_cols = [c for c in ["timestamp","temperature","humidity"] if c in df.columns]
        st.dataframe(
            df[show_cols].tail(10).iloc[::-1].reset_index(drop=True),
            use_container_width=True,
            hide_index=True,
        )


# ── Footer ─────────────────────────────────────────────────────────────────────
st.markdown("<div style='height:8px'></div>", unsafe_allow_html=True)
fl, fr = st.columns([4, 1])
with fl:
    st.markdown(f"""
    <div class="footer-bar">
      <span>📡 {BROKER_IP}:{BROKER_PORT} &nbsp;|&nbsp; topic: {TOPIC} &nbsp;|&nbsp; refresh: {REFRESH_SEC}s</span>
    </div>""", unsafe_allow_html=True)
with fr:
    bc, cc = st.columns(2)
    with bc:
        if st.button("🔄", help="Refresh manual", use_container_width=True):
            st.rerun()
    with cc:
        if st.button("🗑️", help="Hapus semua data", use_container_width=True):
            if os.path.exists(DATA_FILE):
                os.remove(DATA_FILE)
            st.rerun()


# ── Auto-refresh ───────────────────────────────────────────────────────────────
time.sleep(REFRESH_SEC)
st.rerun()

# ─────────────────────────────────────────────────────────────────────────────
# Format JSON yang diterima dari ESP32 (salah satu dari ini):
#   {"temperature": 28.5, "humidity": 65.2}
#   {"temp": 28.5, "hum": 65.2}
#
# Jalankan:
#   pip install streamlit paho-mqtt pandas
#   streamlit run dashboard.py
# ─────────────────────────────────────────────────────────────────────────────
import streamlit as st
import paho.mqtt.client as mqtt
import ssl
import json
import pandas as pd
import threading
import time
import os
from datetime import datetime
from collections import deque
from pathlib import Path

# ── Config ─────────────────────────────────────────────────────────────────────
BROKER            = "hayasaka.takofaru.dpdns.org"
PORT              = 8883
USERNAME          = "web_maggot"
PASSWORD          = "NJkyX*L47EEpzzFd@1W#fIf@"

TOPIC_SENSOR      = "maggot/sensor/data"
TOPIC_STATUS      = "maggot/status/fase"
TOPIC_STATUS_BATAS= "maggot/status/batas"
TOPIC_KONTROL     = "maggot/kontrol/fase"
TOPIC_BATAS       = "maggot/kontrol/batas"

MAX_POINTS        = 100
# ── Path — otomatis pakai folder yang sama dengan script ini (Windows & Linux) ─
_BASE             = Path(__file__).parent
DATA_FILE         = str(_BASE / "maggot_sensor_data.json")
FASE_FILE         = str(_BASE / "maggot_fase.json")
BATAS_STATUS_FILE = str(_BASE / "maggot_status_batas.json")
ALL_LIMITS_FILE   = str(_BASE / "maggot_all_limits.json")
REFRESH_SEC       = 2

DEFAULT_PHASE_LIMITS = {
    "Fase Telur": {"tempMin": 28.0, "tempMax": 35.0, "humidMin": 60.0, "humidMax": 80.0},
    "Fase Larva": {"tempMin": 27.0, "tempMax": 30.0, "humidMin": 60.0, "humidMax": 80.0},
    "Fase Pupa":  {"tempMin": 27.0, "tempMax": 30.0, "humidMin":  0.0, "humidMax": 40.0},
    "Fase Lalat": {"tempMin": 27.5, "tempMax": 37.5, "humidMin": 60.0, "humidMax": 70.0},
}

# ── Page Config ────────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="Maggot BSF Monitor",
    page_icon="🐛",
    layout="wide",
    initial_sidebar_state="collapsed",
)

st.markdown("""
<style>
/* ═══════════════════════════════════════════════════════════════
   MAGGOT BSF MONITOR — Industrial Biotech Terminal UI
   Aesthetic: Dense data terminal meets organic biolab
═══════════════════════════════════════════════════════════════ */

@import url('https://fonts.googleapis.com/css2?family=Azeret+Mono:wght@300;400;500;600;700&family=Barlow+Condensed:wght@300;400;500;600;700;800;900&family=Barlow:wght@300;400;500&display=swap');

:root {
  /* Core palette */
  --void:        #040608;
  --bg:          #070b0f;
  --panel:       #0b1017;
  --raised:      #0f161e;
  --border-dim:  #131d27;
  --border:      #1a2735;
  --border-lit:  #243648;

  /* Text */
  --text-ghost:  #1e3347;
  --text-dim:    #334d63;
  --text-muted:  #4d6b82;
  --text-base:   #7a9bb5;
  --text-bright: #b8d4ea;
  --text-white:  #e4f0f8;

  /* Accents */
  --acid:        #00ff88;       /* bioluminescent green  */
  --acid-dim:    rgba(0,255,136,0.08);
  --acid-glow:   rgba(0,255,136,0.18);
  --acid-border: rgba(0,255,136,0.25);

  --heat:        #ff4d2e;       /* thermal red */
  --heat-dim:    rgba(255,77,46,0.08);
  --heat-border: rgba(255,77,46,0.28);

  --aqua:        #00c2ff;       /* humidity blue */
  --aqua-dim:    rgba(0,194,255,0.08);
  --aqua-border: rgba(0,194,255,0.28);

  --amber:       #ffb020;       /* warning amber */
  --amber-dim:   rgba(255,176,32,0.08);
  --amber-border:rgba(255,176,32,0.28);

  --violet:      #9d6fff;       /* fase purple */
  --violet-dim:  rgba(157,111,255,0.08);
  --violet-border:rgba(157,111,255,0.28);
}

/* ── Reset & Base ── */
*, *::before, *::after { box-sizing: border-box; }
html, body, [class*="css"] {
  font-family: 'Barlow', sans-serif;
  background: var(--bg);
  color: var(--text-base);
  font-size: 14px;
}
.stApp { background: var(--bg); }
#MainMenu, footer, header { visibility: hidden; }

/* Scanline overlay */
.stApp::before {
  content: '';
  position: fixed; inset: 0; z-index: 0; pointer-events: none;
  background: repeating-linear-gradient(
    0deg,
    transparent,
    transparent 2px,
    rgba(0,0,0,0.08) 2px,
    rgba(0,0,0,0.08) 4px
  );
}

/* ── Typography ── */
h1, h2, h3, h4 {
  font-family: 'Barlow Condensed', sans-serif !important;
  color: var(--text-white) !important;
  letter-spacing: 1px;
}

/* ── Noise texture overlay via pseudo on panels ── */
.panel {
  position: relative;
  background: var(--panel);
  border: 1px solid var(--border);
  border-radius: 4px;
  overflow: hidden;
}
.panel::after {
  content: '';
  position: absolute; inset: 0; pointer-events: none;
  background-image: url("data:image/svg+xml,%3Csvg viewBox='0 0 200 200' xmlns='http://www.w3.org/2000/svg'%3E%3Cfilter id='n'%3E%3CfeTurbulence type='fractalNoise' baseFrequency='0.85' numOctaves='4' stitchTiles='stitch'/%3E%3C/filter%3E%3Crect width='100%25' height='100%25' filter='url(%23n)' opacity='0.04'/%3E%3C/svg%3E");
  opacity: 0.4;
  mix-blend-mode: overlay;
}

/* ── Top accent bar on panels ── */
.panel-heat   { border-top: 2px solid var(--heat); }
.panel-aqua   { border-top: 2px solid var(--aqua); }
.panel-violet { border-top: 2px solid var(--violet); }
.panel-acid   { border-top: 2px solid var(--acid); }
.panel-amber  { border-top: 2px solid var(--amber); }

/* ── Metric Card ── */
.mc {
  padding: 20px 22px 18px;
  min-height: 150px;
  display: flex;
  flex-direction: column;
  justify-content: space-between;
}
.mc-label {
  font-family: 'Azeret Mono', monospace;
  font-size: 0.58rem;
  letter-spacing: 3px;
  text-transform: uppercase;
  color: var(--text-muted);
  margin-bottom: 6px;
  display: flex;
  align-items: center;
  gap: 6px;
}
.mc-label-dot {
  width: 6px; height: 6px;
  border-radius: 50%;
  display: inline-block;
  animation: blink 2s ease-in-out infinite;
}
@keyframes blink {
  0%, 100% { opacity: 1; }
  50%       { opacity: 0.2; }
}
.dot-heat   { background: var(--heat); }
.dot-aqua   { background: var(--aqua); }
.dot-violet { background: var(--violet); }
.dot-acid   { background: var(--acid); }

.mc-value {
  font-family: 'Barlow Condensed', sans-serif;
  font-size: 4.2rem;
  font-weight: 800;
  line-height: 0.9;
  letter-spacing: -1px;
}
.mc-unit {
  font-size: 1.6rem;
  font-weight: 300;
  opacity: 0.55;
  margin-left: 3px;
}
.val-heat   { color: var(--heat); }
.val-aqua   { color: var(--aqua); }
.val-violet { color: var(--violet); }

.mc-meta {
  font-family: 'Azeret Mono', monospace;
  font-size: 0.6rem;
  color: var(--text-dim);
  letter-spacing: 1px;
  margin-top: 10px;
  display: flex;
  gap: 12px;
}
.mc-meta span { color: var(--text-base); }

/* ── Condition Badge ── */
.badge {
  display: inline-flex;
  align-items: center;
  gap: 5px;
  font-family: 'Azeret Mono', monospace;
  font-size: 0.58rem;
  font-weight: 600;
  letter-spacing: 1.8px;
  text-transform: uppercase;
  padding: 4px 10px;
  border-radius: 3px;
  margin-top: 10px;
}
.badge-ok     { background: rgba(0,255,136,0.08);  color: var(--acid);   border: 1px solid var(--acid-border); }
.badge-warn   { background: rgba(255,176,32,0.08); color: var(--amber);  border: 1px solid var(--amber-border); }
.badge-danger { background: rgba(255,77,46,0.08);  color: var(--heat);   border: 1px solid var(--heat-border); }
.badge-info   { background: rgba(157,111,255,0.08);color: var(--violet); border: 1px solid var(--violet-border); }
.badge-live   { background: rgba(0,255,136,0.08);  color: var(--acid);   border: 1px solid var(--acid-border); animation: pulse-border 2s ease-in-out infinite; }
.badge-wait   { background: rgba(255,176,32,0.08); color: var(--amber);  border: 1px solid var(--amber-border); }

@keyframes pulse-border {
  0%, 100% { border-color: var(--acid-border); box-shadow: none; }
  50% { border-color: var(--acid); box-shadow: 0 0 8px var(--acid-glow); }
}

/* ── Page header ── */
.hdr-wrap {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  padding: 0 0 18px;
  border-bottom: 1px solid var(--border);
  margin-bottom: 20px;
}
.hdr-title {
  font-family: 'Barlow Condensed', sans-serif;
  font-size: 2.8rem;
  font-weight: 900;
  letter-spacing: 4px;
  text-transform: uppercase;
  color: var(--text-white);
  line-height: 1;
}
.hdr-sub {
  font-family: 'Azeret Mono', monospace;
  font-size: 0.6rem;
  color: var(--text-muted);
  letter-spacing: 2px;
  margin-top: 6px;
}
.hdr-sub em { color: var(--acid); font-style: normal; }
.hdr-right {
  text-align: right;
  display: flex;
  flex-direction: column;
  align-items: flex-end;
  gap: 8px;
}
.hdr-ts {
  font-family: 'Azeret Mono', monospace;
  font-size: 0.62rem;
  color: var(--text-dim);
  letter-spacing: 1.5px;
}

/* ── Section label ── */
.section-label {
  font-family: 'Azeret Mono', monospace;
  font-size: 0.58rem;
  letter-spacing: 3.5px;
  text-transform: uppercase;
  color: var(--text-muted);
  display: flex;
  align-items: center;
  gap: 10px;
  margin-bottom: 10px;
  margin-top: 22px;
}
.section-label::after {
  content: '';
  flex: 1;
  height: 1px;
  background: var(--border);
}

/* ── Chart panel ── */
.chart-panel {
  padding: 16px 20px 8px;
}
.chart-header {
  font-family: 'Azeret Mono', monospace;
  font-size: 0.6rem;
  letter-spacing: 2.5px;
  text-transform: uppercase;
  color: var(--text-muted);
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 8px;
}
.chart-header-left { display: flex; align-items: center; gap: 8px; }
.chart-range {
  font-size: 0.55rem;
  color: var(--text-dim);
  background: var(--raised);
  border: 1px solid var(--border-dim);
  padding: 2px 8px;
  border-radius: 2px;
}

/* ── Gauge bar ── */
.gauge-wrap { margin-top: 12px; }
.gauge-row  { display: flex; align-items: center; gap: 10px; margin-bottom: 8px; }
.gauge-label { font-family: 'Azeret Mono', monospace; font-size: 0.55rem; color: var(--text-dim); letter-spacing: 1px; width: 80px; }
.gauge-track {
  flex: 1;
  height: 4px;
  background: var(--raised);
  border: 1px solid var(--border-dim);
  border-radius: 2px;
  overflow: hidden;
  position: relative;
}
.gauge-fill {
  height: 100%;
  border-radius: 2px;
  transition: width 0.8s cubic-bezier(.4,0,.2,1);
}
.gauge-fill-heat { background: linear-gradient(90deg, #661500, var(--heat)); }
.gauge-fill-aqua { background: linear-gradient(90deg, #003d66, var(--aqua)); }
.gauge-val { font-family: 'Azeret Mono', monospace; font-size: 0.58rem; color: var(--text-bright); width: 48px; text-align: right; }

/* ── Kontrol panel ── */
.kontrol-panel {
  padding: 18px 22px;
}
.kontrol-label {
  font-family: 'Azeret Mono', monospace;
  font-size: 0.58rem;
  letter-spacing: 3px;
  text-transform: uppercase;
  color: var(--text-muted);
  margin-bottom: 14px;
  display: flex;
  align-items: center;
  gap: 8px;
}
.kontrol-label-icon { color: var(--acid); }

/* ── Notification banners ── */
.notif-overlay {
  position: fixed;
  top: 24px; left: 50%; transform: translateX(-50%);
  z-index: 99999;
  width: min(520px, 90vw);
  pointer-events: none;
  animation: notif-anim 3s ease forwards;
}
.notif-box {
  display: flex; align-items: flex-start; gap: 14px;
  padding: 14px 18px;
  border-radius: 4px;
  backdrop-filter: blur(12px);
  pointer-events: auto;
}
.notif-violet { background: rgba(11,16,23,0.95); border: 1px solid var(--violet-border); box-shadow: 0 4px 24px rgba(157,111,255,0.2), 0 0 0 1px rgba(157,111,255,0.1) inset; }
.notif-aqua   { background: rgba(11,16,23,0.95); border: 1px solid var(--aqua-border);   box-shadow: 0 4px 24px rgba(0,194,255,0.15), 0 0 0 1px rgba(0,194,255,0.08) inset; }
.notif-acid   { background: rgba(11,16,23,0.95); border: 1px solid var(--acid-border);   box-shadow: 0 4px 24px rgba(0,255,136,0.18), 0 0 0 1px rgba(0,255,136,0.08) inset; }
.notif-icon { font-size: 1.4rem; line-height: 1; margin-top: 2px; }
.notif-title {
  font-family: 'Barlow Condensed', sans-serif;
  font-size: 1rem;
  font-weight: 700;
  letter-spacing: 1px;
  color: var(--text-white);
  line-height: 1.1;
}
.notif-body {
  font-family: 'Barlow', sans-serif;
  font-size: 0.8rem;
  color: var(--text-base);
  margin-top: 3px;
  line-height: 1.4;
}
.notif-body b { color: var(--text-bright); }
.notif-chip {
  margin-left: auto;
  font-family: 'Azeret Mono', monospace;
  font-size: 0.58rem;
  color: var(--text-dim);
  background: var(--raised);
  border: 1px solid var(--border);
  padding: 4px 8px;
  border-radius: 3px;
  white-space: nowrap;
  line-height: 1.6;
  align-self: center;
}
@keyframes notif-anim {
  0%   { opacity: 0; transform: translateX(-50%) translateY(-12px); }
  8%   { opacity: 1; transform: translateX(-50%) translateY(0); }
  85%  { opacity: 1; transform: translateX(-50%) translateY(0); }
  100% { opacity: 0; transform: translateX(-50%) translateY(-8px); }
}

/* ── Phase limits table ── */
.limits-table {
  width: 100%;
  font-family: 'Azeret Mono', monospace;
  font-size: 0.62rem;
  border-collapse: collapse;
  margin-top: 8px;
}
.limits-table th {
  font-size: 0.54rem;
  letter-spacing: 2px;
  text-transform: uppercase;
  color: var(--text-dim);
  text-align: left;
  padding: 6px 10px;
  border-bottom: 1px solid var(--border);
}
.limits-table td {
  padding: 8px 10px;
  color: var(--text-base);
  border-bottom: 1px solid var(--border-dim);
  vertical-align: middle;
}
.limits-table tr:hover td { background: var(--raised); }
.limits-table .active-row td { background: var(--acid-dim); color: var(--text-bright); }
.limits-table .active-row td:first-child { color: var(--acid); font-weight: 600; }
.tag-heat   { color: var(--heat);   }
.tag-aqua   { color: var(--aqua);   }
.tag-violet { color: var(--violet); }

/* ── Connection log ── */
.log-box {
  font-family: 'Azeret Mono', monospace;
  font-size: 0.6rem;
  color: var(--text-muted);
  background: var(--void);
  border: 1px solid var(--border-dim);
  border-radius: 3px;
  padding: 10px 14px;
  max-height: 100px;
  overflow-y: auto;
  line-height: 1.8;
}
.log-ok   { color: var(--acid); }
.log-err  { color: var(--heat); }
.log-warn { color: var(--amber); }
.log-info { color: var(--aqua); }

/* ── Footer ── */
.footer-strip {
  font-family: 'Azeret Mono', monospace;
  font-size: 0.58rem;
  color: var(--text-ghost);
  letter-spacing: 1.5px;
  display: flex;
  align-items: center;
  gap: 16px;
  padding: 12px 0 4px;
  border-top: 1px solid var(--border-dim);
  margin-top: 24px;
}
.footer-strip em { color: var(--text-dim); font-style: normal; }

/* ── Streamlit overrides ── */
div[data-testid="stSelectbox"] > div { background: var(--raised) !important; border-color: var(--border) !important; }
div[data-testid="stNumberInput"] input { background: var(--raised) !important; color: var(--text-bright) !important; border-color: var(--border) !important; font-family: 'Azeret Mono', monospace !important; }
div[data-testid="stTextInput"] input { background: var(--raised) !important; color: var(--text-bright) !important; border-color: var(--border) !important; font-family: 'Azeret Mono', monospace !important; }
button[data-testid="baseButton-primary"] { background: var(--acid) !important; color: #000 !important; font-family: 'Barlow Condensed', sans-serif !important; font-weight: 700 !important; letter-spacing: 2px !important; border-radius: 3px !important; border: none !important; }
button[data-testid="baseButton-secondary"] { background: var(--raised) !important; color: var(--text-base) !important; border-color: var(--border) !important; font-family: 'Azeret Mono', monospace !important; font-size: 0.65rem !important; border-radius: 3px !important; }
.stExpander { background: var(--panel) !important; border: 1px solid var(--border) !important; border-radius: 4px !important; }
div[data-testid="stDataFrame"] { background: var(--panel) !important; }
[data-testid="stMetric"] { display: none; }

/* Progress/gauge on temp-in-range */
.range-indicator {
  display: flex;
  align-items: center;
  gap: 6px;
  margin-top: 10px;
}
.range-marker-wrap {
  flex: 1;
  height: 3px;
  background: var(--border-dim);
  border-radius: 2px;
  position: relative;
}
.range-zone {
  position: absolute;
  height: 100%;
  background: rgba(0,255,136,0.3);
  border-radius: 2px;
}
.range-needle {
  position: absolute;
  top: -3px;
  width: 2px;
  height: 9px;
  background: #fff;
  border-radius: 1px;
  transform: translateX(-50%);
  transition: left 0.6s cubic-bezier(.4,0,.2,1);
  box-shadow: 0 0 4px rgba(255,255,255,0.6);
}
.range-bound {
  font-family: 'Azeret Mono', monospace;
  font-size: 0.52rem;
  color: var(--text-dim);
}
</style>
""", unsafe_allow_html=True)


# ════════════════════════════════════════════════════════════════
# Condition helpers
# ════════════════════════════════════════════════════════════════
def temp_condition(t, mn=18.0, mx=26.0):
    if t is None: return "— NO DATA", "badge-warn"
    if t < mn:    return "❄ UNDER RANGE", "badge-warn"
    elif t <= mx: return "✓ OPTIMAL",     "badge-ok"
    else:         return "▲ OVER RANGE",  "badge-danger"

def hum_condition(h, mn=40.0, mx=60.0):
    if h is None: return "— NO DATA",     "badge-warn"
    if h < mn:    return "▼ TOO DRY",     "badge-danger"
    elif h <= mx: return "✓ OPTIMAL",     "badge-ok"
    else:         return "▲ TOO HUMID",   "badge-danger"

def needle_pct(val, lo, hi, pad=0.2):
    """Map val to 0-100 for the range indicator, with padding."""
    if val is None: return 50
    span = hi - lo
    padded_lo = lo - span * pad
    padded_hi = hi + span * pad
    pct = (val - padded_lo) / (padded_hi - padded_lo) * 100
    return max(2, min(98, pct))

def zone_pct(lo, hi, pad=0.2):
    span = hi - lo
    padded_lo = lo - span * pad
    padded_hi = hi + span * pad
    padded_span = padded_hi - padded_lo
    left  = (lo - padded_lo) / padded_span * 100
    width = span / padded_span * 100
    return left, width

def colorize_log(line):
    if "[OK]" in line or "[CONFIRM]" in line: cls = "log-ok"
    elif "[ERR]" in line or "[DISC]" in line: cls = "log-err"
    elif "[WARN]" in line:                    cls = "log-warn"
    else:                                     cls = "log-info"
    return f'<span class="{cls}">{line}</span>'


# ════════════════════════════════════════════════════════════════
# MQTT worker
# ════════════════════════════════════════════════════════════════
_conn_log = deque(maxlen=8)

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
            _conn_log.append(f"[WARN] cache: {e}")

    def _write_atomic(data, path):
        tmp = path + ".tmp"
        with open(tmp, "w") as f:
            json.dump(data, f, ensure_ascii=False)
        os.replace(tmp, path)

    def on_connect(client, userdata, flags, reason_code, properties=None):
        rc = reason_code if isinstance(reason_code, int) else reason_code.value
        if rc == 0:
            _conn_log.append(f"[OK] Connected → {BROKER}:{PORT}")
            client.subscribe(TOPIC_SENSOR)
            client.subscribe(TOPIC_STATUS)
            client.subscribe(TOPIC_STATUS_BATAS)
        else:
            codes = {1:"bad protocol",2:"id rejected",3:"unavailable",4:"bad credentials",5:"not authorized"}
            _conn_log.append(f"[ERR] Connect failed: {codes.get(rc, f'rc={rc}')}")

    def on_message(client, userdata, msg):
        topic   = msg.topic
        payload = msg.payload.decode("utf-8").strip()

        if topic == TOPIC_SENSOR:
            try:
                data = json.loads(payload)
                suhu = data.get("suhu", data.get("temperature", data.get("temp")))
                kelembapan = data.get("kelembapan", data.get("humidity", data.get("hum")))
                if suhu is None or kelembapan is None:
                    _conn_log.append(f"[WARN] Field hilang: {list(data.keys())}")
                    return
                entry = {
                    "timestamp":   datetime.now().strftime("%H:%M:%S"),
                    "temperature": float(suhu),
                    "humidity":    float(kelembapan),
                }
                buffer.append(entry)
                _write_atomic(list(buffer), DATA_FILE)
            except json.JSONDecodeError as e:
                _conn_log.append(f"[ERR] JSON sensor: {e} | {payload[:40]}")
            except Exception as e:
                _conn_log.append(f"[ERR] sensor: {e}")

        elif topic == TOPIC_STATUS:
            try:
                fase_data = {"fase": payload, "timestamp": datetime.now().strftime("%H:%M:%S")}
                try:
                    parsed = json.loads(payload)
                    fase_data = {**fase_data, **parsed}
                except json.JSONDecodeError:
                    pass
                _write_atomic(fase_data, FASE_FILE)
                _conn_log.append(f"[INFO] Fase → {payload[:60]}")
            except Exception as e:
                _conn_log.append(f"[ERR] fase: {e}")

        elif topic == TOPIC_STATUS_BATAS:
            try:
                data = json.loads(payload)
                _write_atomic(data, BATAS_STATUS_FILE)
                _conn_log.append(f"[CONFIRM] Batas {data.get('fase')} updated")
                if data.get("status") == "SUCCESS":
                    _update_limit(data["fase"], data["tempMin"], data["tempMax"], data["humidMin"], data["humidMax"])
            except Exception as e:
                _conn_log.append(f"[ERR] batas status: {e}")

    def on_disconnect(client, userdata, flags, reason_code, properties=None):
        rc = reason_code if isinstance(reason_code, int) else reason_code.value
        _conn_log.append(f"[DISC] rc={rc} — reconnecting…")

    client = mqtt.Client(
        mqtt.CallbackAPIVersion.VERSION2,
        client_id=f"bsf-dash-{int(time.time()*1000)%99999}",
        clean_session=True,
    )
    client.username_pw_set(USERNAME, PASSWORD)
    client.tls_set(cert_reqs=ssl.CERT_REQUIRED, tls_version=ssl.PROTOCOL_TLS_CLIENT)
    client.on_connect    = on_connect
    client.on_message    = on_message
    client.on_disconnect = on_disconnect

    _conn_log.append(f"[INFO] Connecting → {BROKER}:{PORT}")
    while True:
        try:
            client.connect(BROKER, PORT, keepalive=60)
            client.loop_forever()
        except Exception as e:
            _conn_log.append(f"[ERR] {str(e)[:60]} — retry 5s")
            time.sleep(5)

if "mqtt_started" not in st.session_state:
    threading.Thread(target=_mqtt_worker, daemon=True).start()
    st.session_state["mqtt_started"] = True


# ════════════════════════════════════════════════════════════════
# File helpers
# ════════════════════════════════════════════════════════════════
def load_sensor():
    if not os.path.exists(DATA_FILE): return []
    try:
        with open(DATA_FILE) as f: raw = f.read().strip()
        if not raw: return []
        p = json.loads(raw)
        return p if isinstance(p, list) else []
    except: return []

def load_fase():
    if not os.path.exists(FASE_FILE): return {}
    try:
        with open(FASE_FILE) as f: return json.load(f)
    except: return {}

def load_batas_status():
    if not os.path.exists(BATAS_STATUS_FILE): return {}
    try:
        with open(BATAS_STATUS_FILE) as f: return json.load(f)
    except: return {}

def load_all_limits():
    if not os.path.exists(ALL_LIMITS_FILE):
        try:
            with open(ALL_LIMITS_FILE, "w") as f:
                json.dump(DEFAULT_PHASE_LIMITS, f)
        except: pass
        return DEFAULT_PHASE_LIMITS
    try:
        with open(ALL_LIMITS_FILE) as f: return json.load(f)
    except: return DEFAULT_PHASE_LIMITS

def _update_limit(fase_name, t_mn, t_mx, h_mn, h_mx):
    limits = load_all_limits()
    if fase_name in limits:
        limits[fase_name] = {"tempMin": float(t_mn), "tempMax": float(t_mx),
                              "humidMin": float(h_mn), "humidMax": float(h_mx)}
        try:
            with open(ALL_LIMITS_FILE, "w") as f: json.dump(limits, f)
        except: pass


# ════════════════════════════════════════════════════════════════
# Publish helpers
# ════════════════════════════════════════════════════════════════
def _pub_thread(topic, payload_str):
    def _run():
        try:
            c = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2,
                            client_id=f"bsf-pub-{int(time.time()*1000)%99999}",
                            clean_session=True)
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

def publish_limits(payload_dict):
    _pub_thread(TOPIC_BATAS, json.dumps(payload_dict))


# ════════════════════════════════════════════════════════════════
# Render (auto-refresh via @st.fragment)
# ════════════════════════════════════════════════════════════════
@st.fragment(run_every=REFRESH_SEC)
def render_dashboard():
    data_list    = load_sensor()
    fase_info    = load_fase()
    batas_status = load_batas_status()
    all_limits   = load_all_limits()
    has_data     = len(data_list) > 0
    now_str      = datetime.now().strftime("%d %b %Y — %H:%M:%S")
    fmt          = lambda v, d=1: f"{v:.{d}f}" if v is not None else "—"

    # ── Data processing ───────────────────────────────────────────────────────
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

    current_fase = fase_info.get("fase", "—")
    fase_ts      = fase_info.get("timestamp", "")

    # Active limits
    if (batas_status and batas_status.get("status") == "SUCCESS"
            and batas_status.get("fase") == current_fase):
        t_mn = float(batas_status.get("tempMin",  18.0))
        t_mx = float(batas_status.get("tempMax",  26.0))
        h_mn = float(batas_status.get("humidMin", 40.0))
        h_mx = float(batas_status.get("humidMax", 60.0))
    else:
        t_mn = float(fase_info.get("tempMin",  18.0))
        t_mx = float(fase_info.get("tempMax",  26.0))
        h_mn = float(fase_info.get("humidMin", 40.0))
        h_mx = float(fase_info.get("humidMax", 60.0))

    temp_cond, temp_cls = temp_condition(latest_temp, t_mn, t_mx)
    hum_cond,  hum_cls  = hum_condition(latest_hum,  h_mn, h_mx)

    # Range indicators
    t_needle_pct = needle_pct(latest_temp, t_mn, t_mx)
    h_needle_pct = needle_pct(latest_hum,  h_mn, h_mx)
    t_zone_l, t_zone_w = zone_pct(t_mn, t_mx)
    h_zone_l, h_zone_w = zone_pct(h_mn, h_mx)

    # Gauge bar pcts (0-100 based on realistic max)
    t_gauge = min(100, max(0, (latest_temp / 50 * 100))) if latest_temp is not None else 0
    h_gauge = min(100, max(0, latest_hum))               if latest_hum  is not None else 0

    # ── HEADER ───────────────────────────────────────────────────────────────
    c_title, c_status = st.columns([6, 2])
    with c_title:
        st.markdown(f"""
        <div class="hdr-wrap">
          <div>
            <div class="hdr-title">🐛 BSF MAGGOT MONITOR</div>
            <div class="hdr-sub">
              MQTTS · <em>{BROKER}</em> · PORT <em>{PORT}</em> · USER <em>{USERNAME}</em>
            </div>
          </div>
        </div>""", unsafe_allow_html=True)
    with c_status:
        live     = has_data
        b_cls    = "badge-live" if live else "badge-wait"
        b_dot    = "●" if live else "○"
        b_label  = "STREAMING" if live else "WAITING"
        st.markdown(f"""
        <div style="padding-top:6px; text-align:right;">
          <div><span class="badge {b_cls}">{b_dot} {b_label}</span></div>
          <div class="hdr-ts" style="margin-top:10px">{now_str}</div>
          <div class="hdr-ts">{len(data_list)}/{MAX_POINTS} samples · Δ{REFRESH_SEC}s</div>
        </div>""", unsafe_allow_html=True)

    # ── METRIC CARDS ─────────────────────────────────────────────────────────
    st.markdown('<div class="section-label">LIVE READINGS</div>', unsafe_allow_html=True)
    c1, c2, c3 = st.columns(3)

    with c1:
        st.markdown(f"""
        <div class="panel panel-heat">
          <div class="mc">
            <div>
              <div class="mc-label">
                <span class="mc-label-dot dot-heat"></span> SUHU · TEMPERATURE
              </div>
              <div class="mc-value val-heat">{fmt(latest_temp)}<span class="mc-unit">°C</span></div>
            </div>
            <div>
              <div class="mc-meta">
                <span>MIN&nbsp;<span>{fmt(min_temp)}</span></span>
                <span>MAX&nbsp;<span>{fmt(max_temp)}</span></span>
                <span>AVG&nbsp;<span>{fmt(avg_temp)}</span></span>
              </div>
              <div class="gauge-wrap">
                <div class="gauge-row">
                  <div class="gauge-label">LIVE</div>
                  <div class="gauge-track">
                    <div class="gauge-fill gauge-fill-heat" style="width:{t_gauge:.1f}%"></div>
                  </div>
                  <div class="gauge-val">{fmt(latest_temp)} °C</div>
                </div>
              </div>
              <div class="range-indicator">
                <span class="range-bound">{fmt(t_mn)}</span>
                <div class="range-marker-wrap">
                  <div class="range-zone" style="left:{t_zone_l:.1f}%; width:{t_zone_w:.1f}%"></div>
                  <div class="range-needle" style="left:{t_needle_pct:.1f}%"></div>
                </div>
                <span class="range-bound">{fmt(t_mx)}</span>
              </div>
              <div><span class="badge {temp_cls}">{temp_cond}</span></div>
            </div>
          </div>
        </div>""", unsafe_allow_html=True)

    with c2:
        st.markdown(f"""
        <div class="panel panel-aqua">
          <div class="mc">
            <div>
              <div class="mc-label">
                <span class="mc-label-dot dot-aqua"></span> KELEMBAPAN · HUMIDITY
              </div>
              <div class="mc-value val-aqua">{fmt(latest_hum)}<span class="mc-unit">%</span></div>
            </div>
            <div>
              <div class="mc-meta">
                <span>MIN&nbsp;<span>{fmt(min_hum)}</span></span>
                <span>MAX&nbsp;<span>{fmt(max_hum)}</span></span>
                <span>AVG&nbsp;<span>{fmt(avg_hum)}</span></span>
              </div>
              <div class="gauge-wrap">
                <div class="gauge-row">
                  <div class="gauge-label">LIVE</div>
                  <div class="gauge-track">
                    <div class="gauge-fill gauge-fill-aqua" style="width:{h_gauge:.1f}%"></div>
                  </div>
                  <div class="gauge-val">{fmt(latest_hum)} %</div>
                </div>
              </div>
              <div class="range-indicator">
                <span class="range-bound">{fmt(h_mn)}</span>
                <div class="range-marker-wrap">
                  <div class="range-zone" style="left:{h_zone_l:.1f}%; width:{h_zone_w:.1f}%"></div>
                  <div class="range-needle" style="left:{h_needle_pct:.1f}%"></div>
                </div>
                <span class="range-bound">{fmt(h_mx)}</span>
              </div>
              <div><span class="badge {hum_cls}">{hum_cond}</span></div>
            </div>
          </div>
        </div>""", unsafe_allow_html=True)

    with c3:
        st.markdown(f"""
        <div class="panel panel-violet">
          <div class="mc">
            <div>
              <div class="mc-label">
                <span class="mc-label-dot dot-violet"></span> FASE AKTIF · LIFECYCLE
              </div>
              <div class="mc-value val-violet" style="font-size:3rem; word-break:break-word;">{current_fase}</div>
            </div>
            <div>
              <div class="mc-meta">
                <span>TOPIC&nbsp;<span>maggot/status/fase</span></span>
              </div>
              <div class="mc-meta" style="margin-top:4px;">
                <span>T RANGE&nbsp;<span>{fmt(t_mn)}–{fmt(t_mx)} °C</span></span>
              </div>
              <div class="mc-meta">
                <span>H RANGE&nbsp;<span>{fmt(h_mn)}–{fmt(h_mx)} %</span></span>
              </div>
              <div><span class="badge badge-info">READ ONLY · {fase_ts or "—"}</span></div>
            </div>
          </div>
        </div>""", unsafe_allow_html=True)

    # ── CHARTS ────────────────────────────────────────────────────────────────
    st.markdown('<div class="section-label">HISTORICAL DATA</div>', unsafe_allow_html=True)
    cc1, cc2 = st.columns(2)

    with cc1:
        st.markdown(f"""
        <div class="panel panel-heat">
          <div class="chart-panel">
            <div class="chart-header">
              <div class="chart-header-left">
                <span class="mc-label-dot dot-heat" style="animation:blink 2s infinite"></span>
                TEMPERATURE (°C)
              </div>
              <span class="chart-range">RANGE {fmt(t_mn)}–{fmt(t_mx)} °C</span>
            </div>
          </div>
        </div>""", unsafe_allow_html=True)
        if has_data and df is not None and "temperature" in df.columns and df["temperature"].notna().any():
            tc = df[["temperature"]].copy()
            if "timestamp" in df.columns: tc.index = df["timestamp"]
            st.line_chart(tc, color="#ff4d2e", height=220, use_container_width=True)
        else:
            st.info("⏳ Menunggu data suhu dari ESP32…")

    with cc2:
        st.markdown(f"""
        <div class="panel panel-aqua">
          <div class="chart-panel">
            <div class="chart-header">
              <div class="chart-header-left">
                <span class="mc-label-dot dot-aqua" style="animation:blink 2s 0.5s infinite"></span>
                HUMIDITY (%)
              </div>
              <span class="chart-range">RANGE {fmt(h_mn)}–{fmt(h_mx)} %</span>
            </div>
          </div>
        </div>""", unsafe_allow_html=True)
        if has_data and df is not None and "humidity" in df.columns and df["humidity"].notna().any():
            hc = df[["humidity"]].copy()
            if "timestamp" in df.columns: hc.index = df["timestamp"]
            st.line_chart(hc, color="#00c2ff", height=220, use_container_width=True)
        else:
            st.info("⏳ Menunggu data kelembapan dari ESP32…")

    # ── CONTROLS ──────────────────────────────────────────────────────────────
    st.markdown('<div class="section-label">CONTROL PANEL</div>', unsafe_allow_html=True)
    ctrl_col, limits_col = st.columns([1, 2])

    with ctrl_col:
        st.markdown("""
        <div class="panel panel-violet">
          <div class="kontrol-panel">
            <div class="kontrol-label"><span class="kontrol-label-icon">◈</span> GANTI FASE</div>
          </div>
        </div>""", unsafe_allow_html=True)
        fase_sel = st.selectbox(
            "Pilih Fase",
            ["Fase Telur", "Fase Larva", "Fase Pupa", "Fase Lalat"],
            label_visibility="collapsed",
        )
        if st.button("📤 KIRIM FASE", type="primary", use_container_width=True):
            publish_fase(fase_sel)
            st.session_state["notif_fase"] = time.time()
            st.session_state["notif_fase_name"] = fase_sel

    with limits_col:
        st.markdown("""
        <div class="panel panel-amber">
          <div class="kontrol-panel">
            <div class="kontrol-label"><span style="color:var(--amber)">◈</span> KONFIGURASI BATAS PARAMETER</div>
          </div>
        </div>""", unsafe_allow_html=True)
        opt_fase = st.selectbox(
            "Fase untuk dikonfigurasi",
            ["Fase Telur", "Fase Larva", "Fase Pupa", "Fase Lalat"],
            label_visibility="collapsed",
            key="sel_limit_fase",
        )
        cur = all_limits.get(opt_fase, DEFAULT_PHASE_LIMITS[opt_fase])
        with st.form("form_batas"):
            fc1, fc2, fc3, fc4 = st.columns(4)
            with fc1: v_tmin = st.number_input("T-min (°C)", value=cur["tempMin"],  step=0.5)
            with fc2: v_tmax = st.number_input("T-max (°C)", value=cur["tempMax"],  step=0.5)
            with fc3: v_hmin = st.number_input("H-min (%)",  value=cur["humidMin"], step=1.0)
            with fc4: v_hmax = st.number_input("H-max (%)",  value=cur["humidMax"], step=1.0)
            if st.form_submit_button("📤 KIRIM BATAS", use_container_width=True):
                publish_limits({"fase": opt_fase, "tempMin": v_tmin, "tempMax": v_tmax,
                                 "humidMin": v_hmin, "humidMax": v_hmax})
                st.session_state["notif_batas"] = time.time()
                st.session_state["notif_batas_fase"] = opt_fase

    # ── ALL PHASE LIMITS TABLE ────────────────────────────────────────────────
    with st.expander("📊 Tabel Batas Semua Fase", expanded=False):
        rows = ""
        for fname, lim in all_limits.items():
            active = "active-row" if fname == current_fase else ""
            marker = " ◀ AKTIF" if fname == current_fase else ""
            rows += f"""
            <tr class="{active}">
              <td>{fname}{marker}</td>
              <td class="tag-heat">{lim['tempMin']} – {lim['tempMax']} °C</td>
              <td class="tag-aqua">{lim['humidMin']} – {lim['humidMax']} %</td>
            </tr>"""
        st.markdown(f"""
        <div class="panel" style="padding:16px 20px;">
          <table class="limits-table">
            <thead>
              <tr>
                <th>FASE</th>
                <th>SUHU (°C)</th>
                <th>KELEMBAPAN (%)</th>
              </tr>
            </thead>
            <tbody>{rows}</tbody>
          </table>
        </div>""", unsafe_allow_html=True)

    # ── CONNECTION LOG ────────────────────────────────────────────────────────
    with st.expander("🔌 Connection Log", expanded=False):
        lines = list(_conn_log)[::-1] if _conn_log else ["(belum ada log)"]
        colored = "<br>".join(colorize_log(l) for l in lines)
        st.markdown(f'<div class="log-box">{colored}</div>', unsafe_allow_html=True)

    # ── RAW DATA ──────────────────────────────────────────────────────────────
    if has_data and df is not None:
        with st.expander("🗃️ Raw Data (10 terbaru)", expanded=False):
            show_cols = [c for c in ["timestamp", "temperature", "humidity"] if c in df.columns]
            st.dataframe(
                df[show_cols].tail(10).iloc[::-1].reset_index(drop=True),
                use_container_width=True, hide_index=True,
            )

    # ── NOTIFICATIONS ─────────────────────────────────────────────────────────
    now = time.time()

    if "notif_fase" in st.session_state and now - st.session_state["notif_fase"] < 3.0:
        name = st.session_state.get("notif_fase_name", "")
        st.markdown(f"""
        <div class="notif-overlay">
          <div class="notif-box notif-violet">
            <div class="notif-icon">📤</div>
            <div>
              <div class="notif-title">INSTRUKSI TERKIRIM</div>
              <div class="notif-body">Mengirim perintah ganti fase ke <b>{name}</b> via MQTTS</div>
            </div>
            <div class="notif-chip">{TOPIC_KONTROL}<br>QoS 1</div>
          </div>
        </div>""", unsafe_allow_html=True)

    if "notif_batas" in st.session_state and now - st.session_state["notif_batas"] < 3.0:
        name = st.session_state.get("notif_batas_fase", "")
        st.markdown(f"""
        <div class="notif-overlay">
          <div class="notif-box notif-aqua">
            <div class="notif-icon">⚙️</div>
            <div>
              <div class="notif-title">KONFIGURASI TERKIRIM</div>
              <div class="notif-body">Batas parameter baru untuk <b>{name}</b> dikirim ke broker</div>
            </div>
            <div class="notif-chip">{TOPIC_BATAS}<br>QoS 1</div>
          </div>
        </div>""", unsafe_allow_html=True)

    if batas_status and batas_status.get("status") == "SUCCESS":
        ck = f"{batas_status.get('fase')}-{batas_status.get('tempMin')}-{batas_status.get('humidMin')}"
        if st.session_state.get("_confirm_key") != ck:
            st.session_state["_confirm_key"] = ck
            st.session_state["notif_confirm"] = time.time()
            st.session_state.pop("notif_batas", None)

    if "notif_confirm" in st.session_state and now - st.session_state["notif_confirm"] < 3.5:
        st.markdown(f"""
        <div class="notif-overlay">
          <div class="notif-box notif-acid">
            <div class="notif-icon">✅</div>
            <div>
              <div class="notif-title">KONFIRMASI ESP32</div>
              <div class="notif-body">Batas <b>{batas_status.get('fase')}</b> berhasil diperbarui di perangkat</div>
            </div>
            <div class="notif-chip">
              T {batas_status.get('tempMin')}–{batas_status.get('tempMax')} °C<br>
              H {batas_status.get('humidMin')}–{batas_status.get('humidMax')} %
            </div>
          </div>
        </div>""", unsafe_allow_html=True)

    # ── FOOTER ────────────────────────────────────────────────────────────────
    col_fl, col_fr = st.columns([4, 1])
    with col_fl:
        st.markdown(f"""
        <div class="footer-strip">
          <span>🔒 MQTTS</span>
          <em>{BROKER}:{PORT}</em>
          <span>·</span>
          <em>sensor → {TOPIC_SENSOR}</em>
          <span>·</span>
          <em>fase → {TOPIC_STATUS}</em>
          <span>·</span>
          <em>Δ {REFRESH_SEC}s</em>
        </div>""", unsafe_allow_html=True)
    with col_fr:
        bc, cc = st.columns(2)
        with bc:
            if st.button("🔄", help="Refresh manual", use_container_width=True):
                st.rerun()
        with cc:
            if st.button("🗑️", help="Hapus semua data", use_container_width=True):
                for f in (DATA_FILE, FASE_FILE, BATAS_STATUS_FILE):
                    if os.path.exists(f): os.remove(f)
                st.rerun()


render_dashboard()

# ══════════════════════════════════════════════════════════════════════════════
# JSON FORMAT — maggot/sensor/data:
#   {"suhu": 28.5, "kelembapan": 65.2}       ← format BE (prioritas)
#   {"temperature": 28.5, "humidity": 65.2}  ← fallback
#
# maggot/status/fase: plain text atau JSON
#   "Fase Larva"
#   {"fase": "Fase Larva", "tempMin": 27, "tempMax": 30, ...}
#
# pip install streamlit paho-mqtt pandas
# streamlit run dashboardd.py
# ══════════════════════════════════════════════════════════════════════════════
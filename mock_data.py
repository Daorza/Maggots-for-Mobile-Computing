"""
mock_data.py — Injector data palsu untuk preview dashboard
Jalankan di terminal TERPISAH dari dashboard:

    python mock_data.py

Lalu di terminal lain:
    streamlit run dashboard.py

Data akan langsung muncul di dashboard tanpa ESP32/broker.
"""

import json, time, math, random, os
from datetime import datetime
from collections import deque
from pathlib import Path

# ── Path — otomatis pakai folder yang sama dengan script ini ──────────────────
BASE_DIR  = Path(__file__).parent          # folder tempat file ini berada
DATA_FILE        = str(BASE_DIR / "maggot_sensor_data.json")
FASE_FILE        = str(BASE_DIR / "maggot_fase.json")
BATAS_STATUS_FILE= str(BASE_DIR / "maggot_status_batas.json")
ALL_LIMITS_FILE  = str(BASE_DIR / "maggot_all_limits.json")

MAX_POINTS = 100

PHASE_LIMITS = {
    "Fase Telur": {"tempMin": 28.0, "tempMax": 35.0, "humidMin": 60.0, "humidMax": 80.0},
    "Fase Larva": {"tempMin": 27.0, "tempMax": 30.0, "humidMin": 60.0, "humidMax": 80.0},
    "Fase Pupa":  {"tempMin": 27.0, "tempMax": 30.0, "humidMin":  0.0, "humidMax": 40.0},
    "Fase Lalat": {"tempMin": 27.5, "tempMax": 37.5, "humidMin": 60.0, "humidMax": 70.0},
}

def write(data, path):
    """Tulis JSON secara atomik (aman dari partial-read)."""
    tmp = path + ".tmp"
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False)
    # os.replace bekerja di Windows & Linux/Mac
    os.replace(tmp, path)

def main():
    buffer = deque(maxlen=MAX_POINTS)
    active_fase = "Fase Larva"
    tick = 0

    # Tulis data awal
    limits = PHASE_LIMITS[active_fase]
    write({"fase": active_fase, "timestamp": datetime.now().strftime("%H:%M:%S"), **limits}, FASE_FILE)
    write(PHASE_LIMITS, ALL_LIMITS_FILE)

    print("=" * 55)
    print("  MAGGOT MOCK DATA INJECTOR")
    print(f"  Folder  : {BASE_DIR}")
    print(f"  Sensor  : {DATA_FILE}")
    print(f"  Fase    : {FASE_FILE}")
    print(f"  Fase aktif awal: {active_fase}")
    print("=" * 55)
    print("[MOCK] Tekan Ctrl+C untuk berhenti\n")

    # 4 skenario bergantian tiap 20 detik — biar semua badge bisa diuji
    scenarios = [
        {"label": "Normal",        "t_base": 28.5, "h_base": 68.0},
        {"label": "Suhu tinggi",   "t_base": 31.5, "h_base": 65.0},   # OVER
        {"label": "Terlalu kering","t_base": 28.0, "h_base": 35.0},   # TOO DRY
        {"label": "Kembali normal","t_base": 27.5, "h_base": 72.0},
    ]
    scenario_idx   = 0
    scenario_timer = 0

    while True:
        if scenario_timer >= 20:
            scenario_idx   = (scenario_idx + 1) % len(scenarios)
            scenario_timer = 0
            print(f"\n[MOCK] >>> Skenario berganti → {scenarios[scenario_idx]['label']}\n")

        sc = scenarios[scenario_idx]

        # Noise sinusoidal + gaussian agar terlihat realistis
        t_noise = math.sin(tick * 0.3) * 0.8 + random.gauss(0, 0.15)
        h_noise = math.cos(tick * 0.2) * 1.5 + random.gauss(0, 0.30)

        suhu       = round(sc["t_base"] + t_noise, 2)
        kelembapan = round(sc["h_base"] + h_noise, 2)

        entry = {
            "timestamp":   datetime.now().strftime("%H:%M:%S"),
            "temperature": suhu,
            "humidity":    kelembapan,
        }
        buffer.append(entry)
        write(list(buffer), DATA_FILE)

        print(f"[{datetime.now().strftime('%H:%M:%S')}] #{tick:04d}  "
              f"T={suhu:6.2f} °C   H={kelembapan:6.2f} %   ({sc['label']})")

        tick           += 1
        scenario_timer += 2
        time.sleep(2)

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n[MOCK] Berhenti. File mock tetap ada untuk di-inspect.")
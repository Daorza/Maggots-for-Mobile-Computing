# Smart Maggot IoT Dashboard

Smart Maggot adalah platform *dashboard* IoT cerdas (berbasis *web*) yang dirancang khusus untuk memonitor, mengontrol, dan menganalisis budidaya Maggot BSF (Black Soldier Fly). Sistem ini terintegrasi dengan perangkat keras (seperti ESP32/NodeMCU) via protokol MQTT, dilengkapi dengan fitur analitik cerdas yang digerakkan oleh AI.

![Smart Maggot Dashboard](https://via.placeholder.com/800x400.png?text=Smart+Maggot+Dashboard)

## 🌟 Fitur Utama

- **Real-time Monitoring**: Memantau suhu dan kelembapan kandang budidaya secara *real-time* via MQTT.
- **Fase Otomatis & Manual**: Penentuan otomatis ambang batas (suhu & kelembapan) berdasarkan umur maggot (Telur, Larva, Prepupa, Pupa, Lalat Dewasa). Mendukung pergantian fase secara manual.
- **Peringatan & Notifikasi**: Sistem *alert* otomatis jika suhu atau kelembapan keluar dari batas aman.
- **Pencatatan Data (Log)**: Form input untuk mencatat pemberian pakan dan berat panen harian.
- **AI Analysis (Groq/Llama3)**: Memberikan analisis, kesimpulan kondisi kandang, serta rekomendasi *actionable* kepada peternak berdasarkan data sensor dan pakan terbaru.
- **Laporan & Ekspor**: Rekapitulasi grafik pertumbuhan dan sensor yang dapat di-filter (Harian, Mingguan, Bulanan) dan diunduh dalam format `.csv`.
- **Sistem Autentikasi**: Login aman menggunakan JWT (JSON Web Tokens).

## 🛠️ Teknologi yang Digunakan

**Backend (Python):**
- [FastAPI](https://fastapi.tiangolo.com/) - *Framework web API berkinerja tinggi*
- [SQLite](https://www.sqlite.org/index.html) - *Database relasional yang ringan dan persisten*
- [Paho MQTT](https://pypi.org/project/paho-mqtt/) - *Klien untuk koneksi dan komunikasi ke Broker MQTT Cloud*
- [Groq AI (Llama 3)](https://groq.com/) - *LLM untuk fitur AI Analysis yang sangat cepat*

**Frontend (React/TypeScript):**
- [Vite](https://vitejs.dev/) - *Build tool & dev server yang sangat cepat*
- [React.js](https://react.dev/) - *Library UI*
- [Tailwind CSS](https://tailwindcss.com/) - *Utility-first CSS framework untuk styling*
- [Recharts](https://recharts.org/) - *Library pembuat grafik dinamis*
- [Lucide React](https://lucide.dev/) - *Ikon vektor yang modern*

## ⚙️ Persyaratan Sistem (Prerequisites)

Pastikan Anda sudah menginstal perangkat lunak berikut di komputer Anda:
- **Python 3.9+**
- **Node.js 18+** (beserta `npm`)
- Akun / API Key dari [Groq Cloud](https://console.groq.com/)
- *Broker* MQTT (seperti Mosquitto, EMQX, HiveMQ) yang bisa diakses

## 🚀 Panduan Instalasi & Menjalankan Aplikasi

Aplikasi ini terbagi menjadi dua bagian: **Backend** (API & MQTT Worker) dan **Frontend** (UI).

### 1. Setup Backend (FastAPI)

1. **Buka Terminal/Command Prompt** di dalam folder proyek utama (`Maggots-for-Mobile-Computing`).
2. **Buat dan Aktifkan Virtual Environment (Venv)**:
   ```bash
   # Windows
   python -m venv venv
   venv\Scripts\activate
   
   # Linux/Mac
   python3 -m venv venv
   source venv/bin/activate
   ```
3. **Instal Dependencies**:
   ```bash
   pip install -r requirements.txt
   ```
4. **Konfigurasi Environment**:
   Ubah nama file `.env.example` menjadi `.env` dan isikan kredensial MQTT serta API Key Groq Anda:
   ```env
   MQTT_BROKER=namabroker.com
   MQTT_PORT=8883
   MQTT_USERNAME=user_anda
   MQTT_PASSWORD=password_anda
   
   GROQ_API_KEY=gsk_xxxxxxxxxxxx
   GROQ_MODEL=llama-3.3-70b-versatile
   
   SECRET_KEY=kunci_rahasia_untuk_jwt_disini
   ```
5. **Jalankan Seed Database** (Hanya untuk percobaan awal / membuat akun dummy):
   ```bash
   python seed.py
   ```
   *(Akan membuat akun default: Username `admin` Password `admin`)*
6. **Jalankan Server Backend**:
   ```bash
   uvicorn main:app --port 8000 --reload
   ```

### 2. Setup Frontend (React/Vite)

1. Buka **Terminal/Command Prompt BARU** (biarkan terminal Backend tetap berjalan).
2. Pindah ke direktori `frontend`:
   ```bash
   cd frontend
   ```
3. **Instal Dependencies Node.js**:
   ```bash
   npm install
   ```
4. **Jalankan Server Frontend (Development)**:
   ```bash
   npm run dev
   ```
5. Akses aplikasi web melalui browser Anda, biasanya di **`http://localhost:5173`**.

## 🔌 Dokumentasi Topik MQTT

Perangkat keras (ESP32/NodeMCU) harus diprogram untuk berkomunikasi melalui topik-topik berikut:

- **Subscribe ke**: `maggot/kontrol/fase` (Untuk menerima instruksi perubahan fase paksa dari Web).
- **Subscribe ke**: `maggot/kontrol/batas` (Untuk menerima instruksi ambang batas custom terbaru dari Web).
- **Publish ke**: `maggot/sensor/data` (Kirim data suhu & kelembapan setiap 1-5 detik).
  - Format Payload: `{"suhu": 29.5, "kelembapan": 70.0}`
- **Publish ke**: `maggot/status/fase` (Broadcast status saat ini - opsional, web utamanya menggunakan database).

## 🔒 Keamanan

- Kredensial *broker* disembunyikan menggunakan variabel lingkungan (`.env`).
- Jangan pernah mem- *commit* file `.env` atau `maggot_users.db` ke dalam *repository* Git publik.
- Rute API diproteksi menggunakan **JWT Bearer Authentication**.

---
*Dikembangkan untuk Tugas Akhir / Proyek Mobile Computing.*

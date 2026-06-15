# Panduan Presentasi Proyek Smart Maggot

Dokumen ini dibuat untuk membantu menjelaskan proyek **Smart Maggot IoT Dashboard** dengan bahasa yang mudah dipahami saat presentasi. Fokusnya bukan hanya user flow, tetapi juga arsitektur, frontend, backend, database, AI, data flow, serta kemungkinan pertanyaan dosen.

---

## A. Project Summary

**Smart Maggot** adalah aplikasi web untuk memantau dan menganalisis budidaya maggot BSF atau Black Soldier Fly. Sistem ini membantu peternak/operator mengetahui kondisi kandang secara lebih rapi dan berbasis data.

Masalah yang diselesaikan:

- Peternak sulit memantau suhu dan kelembapan kandang secara terus-menerus.
- Data pakan dan berat maggot sering dicatat manual tanpa analisis.
- Kondisi kandang yang tidak ideal bisa terlambat diketahui.
- Peternak membutuhkan rekomendasi praktis berdasarkan data.

User utama:

- Peternak maggot.
- Operator kandang.
- Mahasiswa atau peneliti budidaya BSF.
- Pengelola produksi maggot skala kecil atau edukasi.

Fitur utama:

- Login dan register user.
- Dashboard kondisi kandang.
- Monitoring suhu dan kelembapan.
- Integrasi sensor IoT melalui MQTT.
- Input data pakan dan berat maggot.
- Alert otomatis jika kondisi tidak normal.
- Laporan pertumbuhan dan estimasi nilai produksi.
- AI Analysis menggunakan Groq Llama 3.3.
- Halaman edukasi tentang maggot BSF.

Alur singkat:

User login -> aplikasi membuka koneksi IoT -> sensor mengirim suhu dan kelembapan lewat MQTT -> backend menyimpan data ke SQLite -> sistem mengecek threshold -> dashboard menampilkan status dan alert -> user mencatat pakan dan berat -> laporan dan AI memakai data tersebut untuk analisis.

---

## B. Architecture Overview

Project ini terdiri dari empat bagian besar:

| Bagian | Fungsi |
|---|---|
| Frontend React | Menampilkan dashboard, form, grafik, laporan, dan chat AI |
| Backend FastAPI | Menangani API, login, database, laporan, dan AI request |
| MQTT Worker | Menerima data suhu dan kelembapan dari perangkat IoT |
| SQLite Database | Menyimpan user, sensor, alert, pakan, berat, fase, dan chat AI |

Penjelasan sederhana:

Frontend adalah tampilan yang digunakan user. Backend adalah otak aplikasi yang menerima permintaan dari frontend. MQTT worker adalah jembatan antara perangkat sensor dan backend. Database adalah tempat semua data disimpan. AI membaca ringkasan data dari database lalu memberi rekomendasi.

---

## C. Folder Structure Explanation

Struktur penting proyek:

```text
Maggots-for-Mobile-Computing/
├── api/
│   └── routers/
│       ├── auth.py
│       ├── dashboard.py
│       ├── input.py
│       ├── ai.py
│       ├── alerts.py
│       └── reports.py
├── frontend/
│   ├── src/
│   │   ├── App.tsx
│   │   ├── api.ts
│   │   ├── components/
│   │   └── pages/
├── auth.py
├── config.py
├── data_manager.py
├── db.py
├── main.py
├── mqtt_worker.py
├── maggot_users.db
├── requirements.txt
└── README.md
```

Penjelasan folder dan file:

| File/Folder | Fungsi |
|---|---|
| `api/routers` | Berisi endpoint backend per fitur |
| `frontend/src/pages` | Berisi halaman UI seperti Dashboard, Monitoring, Login, AI |
| `frontend/src/components` | Berisi komponen layout dan sidebar |
| `frontend/src/api.ts` | Konfigurasi Axios untuk komunikasi ke backend |
| `main.py` | Entry point backend FastAPI |
| `mqtt_worker.py` | Menghubungkan backend ke broker MQTT |
| `db.py` | Membuat tabel database SQLite |
| `data_manager.py` | Helper database, fase otomatis, threshold, sanitasi |
| `config.py` | Konfigurasi MQTT, Groq, database, dan prompt AI |
| `auth.py` | Fungsi register, login, hash password |
| `maggot_users.db` | Database SQLite lokal |
| `README.md` | Dokumentasi instalasi dan penggunaan |

Pembagian layer:

- Frontend: `frontend/src`
- Backend: `main.py`, `api/routers`
- IoT: `mqtt_worker.py`
- Database: `maggot_users.db`, `db.py`
- AI: `api/routers/ai.py`, konfigurasi Groq di `config.py`
- Config: `.env`, `.env.example`, `config.py`
- Asset: `frontend/src/assets`, `frontend/public`

---

## D. Frontend Explanation

Frontend menggunakan:

- React
- TypeScript
- Vite
- Tailwind CSS
- React Router
- Axios
- Recharts
- Lucide React
- React Markdown

Routing utama ada di `frontend/src/App.tsx`.

Route aplikasi:

| Path | Halaman | Fungsi |
|---|---|---|
| `/login` | Login | Login dan register |
| `/connect` | Connect | Simulasi koneksi ke MQTT broker |
| `/` | Dashboard | Ringkasan kondisi kandang |
| `/monitoring` | Monitoring | Grafik suhu dan kelembapan |
| `/input` | Input Data | Input pakan dan berat maggot |
| `/ai` | AI Analysis | Chat AI rekomendasi budidaya |
| `/laporan` | Laporan | Ringkasan produksi dan export CSV |
| `/edukasi` | Edukasi | Materi edukasi BSF |

Cara frontend berkomunikasi dengan backend:

- File `frontend/src/api.ts` membuat Axios client.
- Base URL backend adalah `http://localhost:8000/api`.
- Jika token JWT ada di `localStorage`, token otomatis dikirim di header `Authorization`.

State management:

- Tidak memakai Redux atau Zustand.
- State disimpan dengan `useState`, `useEffect`, dan `useMemo`.
- Token dan nama user disimpan di `localStorage`.

UI flow:

1. User membuka aplikasi.
2. Jika belum login, diarahkan ke `/login`.
3. Setelah login berhasil, token disimpan.
4. User masuk ke halaman `/connect`.
5. Setelah simulasi koneksi, user masuk ke Dashboard.
6. User bisa melihat sensor, alert, input data, laporan, dan bertanya ke AI.

---

## E. Backend Explanation

Backend menggunakan **FastAPI**.

File utama backend adalah `main.py`. File ini:

- Membuat instance FastAPI.
- Mengaktifkan CORS agar frontend React bisa mengakses API.
- Menjalankan MQTT worker saat aplikasi startup.
- Memasang semua router API.

Router backend:

| File | Fungsi |
|---|---|
| `api/routers/auth.py` | Login, register, JWT auth |
| `api/routers/dashboard.py` | Data dashboard, monitoring, status MQTT, setting fase |
| `api/routers/input.py` | Input pakan dan berat maggot |
| `api/routers/alerts.py` | Ambil dan tandai alert |
| `api/routers/reports.py` | Ringkasan laporan |
| `api/routers/ai.py` | AI analysis dan chat history |

Endpoint penting:

| Endpoint | Method | Fungsi | Digunakan oleh |
|---|---|---|---|
| `/api/auth/login` | POST | Login dan return JWT | Login page |
| `/api/auth/register` | POST | Membuat akun baru | Login page |
| `/api/dashboard/metrics` | GET | Mengambil suhu, kelembapan, fase, produksi | Dashboard |
| `/api/dashboard/monitoring` | GET | Mengambil data sensor untuk grafik | Dashboard, Monitoring |
| `/api/dashboard/mqtt-config` | GET | Mengambil broker dan port MQTT | Connect |
| `/api/dashboard/status` | GET | Mengambil status MQTT dan threshold aktif | Dashboard |
| `/api/dashboard/settings` | POST | Mengubah fase otomatis/manual | Dashboard |
| `/api/dashboard/mqtt-reconnect` | POST | Trigger reconnect MQTT | Dashboard |
| `/api/alerts/unread` | GET | Mengambil alert belum dibaca | Dashboard |
| `/api/alerts/mark-read` | POST | Menandai alert sebagai dibaca | Dashboard |
| `/api/input/pangan` | POST | Menyimpan data pakan | Input Data |
| `/api/input/berat` | POST | Menyimpan berat maggot | Input Data |
| `/api/input/history` | GET | Mengambil 5 input terakhir | Input Data |
| `/api/reports/summary` | GET | Mengambil laporan periodik | Laporan |
| `/api/ai/analyze` | POST | Mengirim prompt ke AI | AI Analysis |
| `/api/ai/chats` | GET | Mengambil daftar chat AI | AI Analysis |
| `/api/ai/chats/{id}` | GET | Mengambil pesan chat tertentu | AI Analysis |
| `/api/ai/chats/{id}` | DELETE | Menghapus chat | AI Analysis |

Authentication:

- User login menggunakan email dan password.
- Password di-hash menggunakan SHA256 dengan salt.
- Jika login berhasil, backend membuat JWT.
- Frontend menyimpan token di `localStorage`.
- Endpoint yang dilindungi membaca token dari header `Authorization`.

Validasi dan keamanan:

- Request body divalidasi oleh Pydantic model.
- Input teks disanitasi di `data_manager.py`.
- Ada pengecekan prompt injection sederhana untuk input AI.
- Password tidak disimpan mentah, tetapi dalam bentuk hash.

Catatan keterbatasan:

- Secret key JWT masih hardcoded untuk local development.
- Beberapa endpoint dashboard/report/alert belum semuanya wajib token.
- Belum ada role admin/operator.

---

## F. Database Explanation

Database yang digunakan adalah **SQLite**. File database adalah `maggot_users.db`.

Project ini tidak menggunakan ORM seperti SQLAlchemy. Query database ditulis langsung menggunakan `sqlite3`.

Tabel utama:

| Tabel | Fungsi |
|---|---|
| `users` | Menyimpan akun user |
| `sensor_logs` | Menyimpan data suhu dan kelembapan |
| `alerts` | Menyimpan peringatan kondisi tidak normal |
| `cultivation_settings` | Menyimpan setting fase budidaya |
| `feed_logs` | Menyimpan catatan pakan |
| `weight_logs` | Menyimpan catatan berat maggot |
| `phase_thresholds` | Menyimpan batas suhu/kelembapan per fase |
| `ai_chats` | Menyimpan sesi chat AI |
| `ai_chat_messages` | Menyimpan pesan chat user dan AI |

Field penting:

| Tabel | Field penting |
|---|---|
| `users` | `name`, `email`, `salt`, `password_hash` |
| `sensor_logs` | `temperature`, `humidity`, `phase`, `created_at` |
| `alerts` | `type`, `severity`, `message`, `value`, `phase`, `is_read` |
| `feed_logs` | `date`, `feed_type`, `feed_weight_kg`, `notes` |
| `weight_logs` | `date`, `maggot_weight_kg`, `notes` |
| `phase_thresholds` | `phase`, `temperature_min`, `temperature_max`, `humidity_min`, `humidity_max` |
| `ai_chats` | `user_id`, `title`, `created_at` |
| `ai_chat_messages` | `chat_id`, `role`, `content` |

Data flow database:

Input user atau sensor masuk ke backend -> backend melakukan validasi -> data disimpan ke SQLite -> saat frontend membutuhkan data, backend membaca SQLite -> hasil dikirim sebagai JSON -> frontend menampilkan di UI.

---

## G. AI/ML Explanation

Fitur AI menggunakan **Groq API** dengan model **Llama 3.3 70B Versatile**.

AI di project ini bukan model yang dilatih sendiri. AI adalah external service berbasis LLM. Backend mengambil ringkasan data kandang dari database, lalu mengirimkannya sebagai konteks ke model Llama.

Input AI:

- Pertanyaan user.
- Riwayat chat.
- Ringkasan total pakan.
- Ringkasan berat maggot.
- Rata-rata suhu dan kelembapan.
- Jumlah alert.
- Perbandingan minggu ini dan minggu lalu.

Output AI:

- Analisis kondisi kandang.
- Insight tren.
- Rekomendasi tindakan.
- Jawaban dalam Bahasa Indonesia.

AI pipeline:

User bertanya di halaman AI -> frontend mengirim prompt ke backend -> backend mengambil ringkasan data dari SQLite -> backend membuat system prompt khusus maggot BSF -> backend memanggil Groq Llama 3.3 -> jawaban AI disimpan ke database -> frontend menampilkan jawaban.

Kalimat presentasi:

“AI pada sistem ini berperan sebagai analis data budidaya. AI tidak membaca sensor secara langsung, tetapi membaca ringkasan data yang sudah dikumpulkan sistem, lalu memberi rekomendasi praktis kepada peternak.”

---

## H. Complete Data Flow

### 1. Flow Sensor IoT

ESP32 membaca suhu dan kelembapan -> ESP32 publish JSON ke topic MQTT `maggot/sensor/data` -> `mqtt_worker.py` menerima pesan -> backend mengambil fase aktif dan threshold -> data masuk ke `sensor_logs` -> jika melewati batas, alert masuk ke `alerts` -> dashboard mengambil data lewat API -> UI menampilkan grafik dan status.

### 2. Flow Login

User input email dan password -> `Login.tsx` kirim POST `/api/auth/login` -> backend cek user di database -> password diverifikasi -> backend membuat JWT -> frontend menyimpan token -> user masuk aplikasi.

### 3. Flow Input Pakan

User isi jenis pakan, berat, tanggal, catatan -> `InputData.tsx` kirim POST `/api/input/pangan` -> backend validasi dan sanitasi teks -> data masuk ke `feed_logs` -> frontend mengambil history -> UI menampilkan 5 input terakhir.

### 4. Flow Input Berat Maggot

User isi berat dan tanggal -> frontend kirim POST `/api/input/berat` -> backend validasi berat tidak negatif -> data masuk ke `weight_logs` -> laporan dan AI dapat memakai data berat tersebut.

### 5. Flow Laporan

User memilih periode laporan -> `Laporan.tsx` kirim GET `/api/reports/summary` -> backend menghitung total pakan, berat awal, berat akhir, kenaikan berat, rata-rata sensor, total alert -> frontend menampilkan kartu metrik dan grafik -> user bisa download CSV.

### 6. Flow AI

User mengetik pertanyaan -> `AIAnalysis.tsx` kirim POST `/api/ai/analyze` -> backend mengambil ringkasan operasional dari database -> backend kirim prompt ke Groq -> AI mengembalikan rekomendasi -> backend menyimpan pesan ke database -> frontend menampilkan chat.

---

## I. Feature-by-Feature Breakdown

### 1. Authentication

Fungsi:

User bisa register dan login.

Frontend:

- `frontend/src/pages/Login.tsx`

Backend:

- `api/routers/auth.py`
- `auth.py`

Database:

- `users`

Flow:

User login -> frontend kirim email/password -> backend verifikasi hash password -> JWT dibuat -> token disimpan di localStorage.

Pertanyaan dosen:

“Bagaimana keamanan password?”

Jawaban:

“Password tidak disimpan mentah. Password digabung dengan salt, lalu di-hash menggunakan SHA256.”

### 2. Dashboard

Fungsi:

Menampilkan kondisi utama kandang: suhu, kelembapan, berat, produksi, alert, status MQTT, dan fase.

Frontend:

- `frontend/src/pages/Dashboard.tsx`

Backend:

- `api/routers/dashboard.py`
- `api/routers/alerts.py`

Database:

- `sensor_logs`
- `alerts`
- `weight_logs`
- `phase_thresholds`
- `cultivation_settings`

Flow:

Dashboard polling API setiap 5 detik -> backend membaca data terbaru -> response dikirim -> UI update.

Pertanyaan dosen:

“Apakah data dashboard real-time?”

Jawaban:

“Data sensor masuk real-time melalui MQTT. Di UI, data diperbarui dengan polling API setiap beberapa detik.”

### 3. Monitoring Sensor

Fungsi:

Menampilkan grafik detail suhu dan kelembapan.

Frontend:

- `frontend/src/pages/Monitoring.tsx`

Backend:

- `api/routers/dashboard.py`

Database:

- `sensor_logs`

Flow:

User membuka Monitoring -> frontend request data sensor dengan limit -> backend membaca data sensor terakhir -> frontend menampilkan grafik Recharts.

Pertanyaan dosen:

“Kenapa memakai grafik?”

Jawaban:

“Grafik memudahkan user melihat tren, bukan hanya angka terakhir.”

### 4. Input Data Pakan dan Berat

Fungsi:

Mencatat pakan organik dan berat maggot secara manual.

Frontend:

- `frontend/src/pages/InputData.tsx`

Backend:

- `api/routers/input.py`

Database:

- `feed_logs`
- `weight_logs`

Flow:

User isi form -> frontend kirim POST -> backend validasi -> data disimpan -> history input terbaru ditampilkan.

Pertanyaan dosen:

“Kenapa pakan dan berat masih manual?”

Jawaban:

“Karena jenis pakan dan berat panen biasanya dicatat operator. Sensor otomatis hanya untuk suhu dan kelembapan.”

### 5. Alert Otomatis

Fungsi:

Memberi peringatan jika suhu atau kelembapan keluar dari batas aman.

Backend:

- `mqtt_worker.py`
- `api/routers/alerts.py`

Database:

- `alerts`
- `phase_thresholds`
- `sensor_logs`

Flow:

Sensor masuk -> backend cek threshold fase aktif -> jika nilai terlalu rendah atau tinggi, alert dibuat -> dashboard menampilkan notifikasi.

Pertanyaan dosen:

“Bagaimana sistem menentukan kondisi bahaya?”

Jawaban:

“Nilai sensor dibandingkan dengan batas minimum dan maksimum pada fase aktif. Jika melewati batas, dibuat alert warning atau danger.”

### 6. Fase Budidaya

Fungsi:

Menentukan fase maggot dan threshold yang sesuai.

Backend:

- `data_manager.py`
- `api/routers/dashboard.py`

Database:

- `cultivation_settings`
- `phase_thresholds`

Flow:

Jika mode otomatis aktif, fase dihitung berdasarkan umur budidaya dari tanggal mulai. Jika manual aktif, user memilih fase sendiri di dashboard.

Pertanyaan dosen:

“Fase otomatis dihitung dari apa?”

Jawaban:

“Dari selisih tanggal hari ini dengan tanggal mulai budidaya.”

### 7. AI Analysis

Fungsi:

Memberikan rekomendasi berbasis data kandang.

Frontend:

- `frontend/src/pages/AIAnalysis.tsx`

Backend:

- `api/routers/ai.py`

Database:

- `ai_chats`
- `ai_chat_messages`
- `feed_logs`
- `weight_logs`
- `sensor_logs`
- `alerts`

AI:

- Groq Llama 3.3

Flow:

User bertanya -> backend mengambil ringkasan data -> prompt dikirim ke Groq -> jawaban AI disimpan -> frontend menampilkan chat.

Pertanyaan dosen:

“Apakah AI ini model buatan sendiri?”

Jawaban:

“Tidak. Model AI yang digunakan adalah Llama 3.3 melalui Groq API. Project ini fokus pada integrasi data budidaya dengan AI analysis.”

### 8. Laporan

Fungsi:

Menampilkan rekap produksi dan memungkinkan export CSV.

Frontend:

- `frontend/src/pages/Laporan.tsx`

Backend:

- `api/routers/reports.py`

Database:

- `feed_logs`
- `weight_logs`
- `sensor_logs`
- `alerts`

Flow:

User pilih periode -> backend hitung metrik -> frontend menampilkan kartu dan grafik -> user bisa download CSV.

Pertanyaan dosen:

“Estimasi nilai produksi dihitung bagaimana?”

Jawaban:

“Kenaikan berat maggot dikalikan asumsi harga Rp7.000 per kg.”

---

## J. Important Files to Understand

| File | Yang perlu dipahami |
|---|---|
| `main.py` | Entry point FastAPI, router, CORS, startup MQTT |
| `mqtt_worker.py` | Menerima data sensor dan membuat alert |
| `data_manager.py` | Hitung fase otomatis dan ambang batas aktif |
| `db.py` | Definisi tabel database |
| `api/routers/auth.py` | Login, register, JWT |
| `api/routers/dashboard.py` | Data dashboard, monitoring, status MQTT |
| `api/routers/input.py` | Input pakan dan berat |
| `api/routers/ai.py` | Integrasi Groq dan riwayat chat |
| `api/routers/reports.py` | Perhitungan laporan |
| `frontend/src/App.tsx` | Routing frontend |
| `frontend/src/api.ts` | Axios dan token authorization |
| `frontend/src/pages/Dashboard.tsx` | UI dashboard utama |
| `frontend/src/pages/AIAnalysis.tsx` | UI chat AI |

---

## K. Technical Stack Table

| Layer | Technology Used | Purpose |
|---|---|---|
| Frontend | React | Membuat user interface |
| Frontend Language | TypeScript | Type safety pada frontend |
| Build Tool | Vite | Menjalankan dan build frontend |
| Styling | Tailwind CSS | Styling UI |
| Routing | React Router | Navigasi halaman |
| HTTP Client | Axios | Request API ke backend |
| Chart | Recharts | Grafik suhu, kelembapan, dan berat |
| Icons | Lucide React | Icon UI |
| Backend | FastAPI | Menangani REST API |
| Database | SQLite | Menyimpan data lokal |
| Query System | sqlite3 | Query langsung ke SQLite |
| Authentication | JWT | Login dan proteksi endpoint |
| IoT Protocol | MQTT | Komunikasi sensor ESP32 dengan backend |
| MQTT Client | Paho MQTT | Subscribe dan publish MQTT di Python |
| AI | Groq Llama 3.3 | Analisis data dan rekomendasi |
| Config | dotenv | Membaca environment variable |

---

## L. Presentation Script

### Script 5-7 Menit

Selamat pagi/siang. Pada presentasi ini saya akan menjelaskan project Smart Maggot IoT Dashboard.

Smart Maggot adalah aplikasi web untuk membantu monitoring budidaya maggot BSF. Masalah yang kami angkat adalah proses budidaya maggot membutuhkan kondisi kandang yang stabil, terutama suhu dan kelembapan. Jika kondisi kandang tidak sesuai, pertumbuhan maggot bisa terganggu. Selain itu, pencatatan pakan dan berat maggot biasanya masih manual dan belum dianalisis dengan baik.

Solusi yang kami buat adalah dashboard berbasis web yang menggabungkan IoT, database, laporan, dan AI. Dari sisi IoT, sensor seperti ESP32 mengirim data suhu dan kelembapan melalui protokol MQTT. Backend menggunakan FastAPI menerima data tersebut melalui MQTT worker, lalu menyimpannya ke database SQLite.

Setelah data sensor masuk, sistem mengecek apakah suhu dan kelembapan masih berada dalam batas aman sesuai fase budidaya. Jika keluar dari batas, sistem akan membuat alert otomatis. Alert ini bisa dilihat oleh user di dashboard.

Dari sisi frontend, aplikasi dibuat menggunakan React dan TypeScript. User bisa login, masuk ke dashboard, melihat suhu dan kelembapan terbaru, melihat grafik monitoring, mencatat pakan dan berat maggot, melihat laporan, serta menggunakan AI Analysis.

Fitur AI menggunakan Groq API dengan model Llama 3.3. AI tidak membaca sensor secara langsung. Backend mengambil ringkasan data dari database, seperti total pakan, data berat maggot, rata-rata suhu dan kelembapan, serta jumlah alert. Ringkasan ini dikirim sebagai konteks ke AI, lalu AI memberikan rekomendasi dalam Bahasa Indonesia.

Secara keseluruhan, project ini membantu peternak mengambil keputusan berdasarkan data. Tidak hanya melihat angka sensor, tetapi juga mendapatkan alert, laporan, dan rekomendasi tindakan.

### Script 10-15 Menit

Selamat pagi/siang. Project yang saya presentasikan adalah Smart Maggot IoT Dashboard, yaitu sistem monitoring budidaya maggot BSF berbasis web, IoT, dan AI.

Latar belakang project ini adalah budidaya maggot BSF sangat bergantung pada kondisi lingkungan. Suhu dan kelembapan yang tidak sesuai dapat mempengaruhi pertumbuhan maggot. Selain itu, pencatatan pakan dan berat maggot sering dilakukan manual, sehingga sulit melihat tren produksi dan mengambil keputusan berbasis data.

Tujuan project ini adalah membuat sistem yang dapat memantau kondisi kandang, mencatat data produksi, memberi alert otomatis, membuat laporan, dan memberikan rekomendasi melalui AI.

Arsitektur sistem terdiri dari frontend, backend, database, MQTT worker, dan AI service. Frontend dibuat menggunakan React, TypeScript, Vite, dan Tailwind CSS. Backend dibuat menggunakan FastAPI. Database menggunakan SQLite. Untuk komunikasi sensor, sistem menggunakan MQTT. Untuk AI, sistem menggunakan Groq Llama 3.3.

Alur pertama adalah login. User melakukan login melalui halaman React. Frontend mengirim email dan password ke backend. Backend memverifikasi user, lalu membuat JWT. Token ini disimpan di localStorage dan digunakan untuk request berikutnya.

Alur kedua adalah monitoring IoT. Sensor ESP32 membaca suhu dan kelembapan, lalu mengirim data dalam format JSON ke topic MQTT. Backend memiliki MQTT worker yang subscribe ke topic tersebut. Saat data diterima, backend menyimpan suhu, kelembapan, fase aktif, dan waktu pencatatan ke tabel sensor_logs.

Setelah menyimpan data sensor, backend mengecek threshold. Threshold berbeda untuk setiap fase budidaya, misalnya Telur, Larva, Prepupa, Pupa, dan Lalat Dewasa. Jika suhu atau kelembapan keluar dari batas, sistem membuat alert di tabel alerts.

Di frontend, halaman Dashboard mengambil data dari endpoint dashboard. Dashboard menampilkan suhu terakhir, kelembapan terakhir, berat maggot, estimasi nilai produksi, status MQTT, fase aktif, threshold aktif, grafik sensor, dan notifikasi alert.

Halaman Monitoring fokus pada grafik suhu dan kelembapan. User bisa memilih jumlah titik data yang ditampilkan, misalnya 50, 100, 300, atau 500 data terakhir.

Selanjutnya ada fitur Input Data. User dapat mencatat jenis pakan, berat pakan, tanggal, dan catatan. User juga dapat mencatat berat maggot. Data ini masuk ke tabel feed_logs dan weight_logs. Data tersebut nantinya dipakai untuk laporan dan AI analysis.

Fitur Laporan mengambil data berdasarkan periode: harian, mingguan, bulanan, tahunan, atau custom. Backend menghitung total pakan, berat awal, berat akhir, penambahan berat, estimasi nilai produksi, rata-rata suhu, rata-rata kelembapan, dan jumlah alert. Frontend menampilkan metrik dan grafik, serta menyediakan export CSV.

Fitur AI Analysis menggunakan Groq Llama 3.3. Saat user bertanya, backend tidak langsung mengirim pertanyaan kosong ke AI. Backend terlebih dahulu mengambil ringkasan data operasional dari database. Ringkasan ini berisi total pakan, rekor berat maggot, rata-rata sensor, suhu ekstrem, jumlah alert, dan perbandingan data minggu ini dengan minggu lalu. Setelah itu backend membentuk system prompt agar AI menjawab sebagai asisten budidaya maggot BSF. Jawaban AI disimpan ke database sebagai riwayat chat.

Kelebihan project ini adalah sistem sudah menggabungkan monitoring IoT, dashboard visual, pencatatan produksi, alert otomatis, laporan, dan AI recommendation dalam satu aplikasi. Keterbatasannya adalah deployment masih lokal, sebagian endpoint belum sepenuhnya diproteksi token, dan UI masih menggunakan polling, belum WebSocket.

Untuk pengembangan berikutnya, sistem bisa ditingkatkan dengan deployment cloud, role user, WebSocket real-time, export PDF, kontrol aktuator otomatis seperti kipas atau humidifier, serta model prediksi panen.

Kesimpulannya, Smart Maggot bukan hanya dashboard biasa. Sistem ini membantu peternak memantau kondisi kandang, mencatat produksi, mendapat peringatan, melihat laporan, dan menerima rekomendasi berbasis AI.

---

## M. Possible Lecturer Questions and Answers

**Q: Project ini menyelesaikan masalah apa?**  
A: Project ini membantu monitoring budidaya maggot BSF agar kondisi suhu, kelembapan, pakan, dan berat produksi bisa dipantau dan dianalisis lebih mudah.

**Q: Siapa user aplikasi ini?**  
A: User utamanya adalah peternak maggot, operator kandang, mahasiswa peneliti, atau pengelola produksi BSF.

**Q: Backend menggunakan apa?**  
A: Backend menggunakan FastAPI karena ringan, cepat, dan cocok untuk REST API.

**Q: Frontend menggunakan apa?**  
A: Frontend menggunakan React dengan TypeScript, Vite, Tailwind CSS, Recharts, dan Axios.

**Q: Database menggunakan apa?**  
A: Database menggunakan SQLite karena ringan dan cocok untuk prototype atau project lokal.

**Q: Apakah memakai ORM?**  
A: Tidak. Project ini memakai query langsung menggunakan sqlite3.

**Q: Bagaimana sensor mengirim data?**  
A: Sensor ESP32 publish data suhu dan kelembapan ke broker MQTT, lalu backend subscribe dan menyimpan data tersebut.

**Q: Apa format data sensor?**  
A: Contohnya JSON seperti `{"suhu": 29.5, "kelembapan": 70.0}`.

**Q: Bagaimana alert dibuat?**  
A: Setelah data sensor masuk, backend membandingkan nilai suhu dan kelembapan dengan threshold fase aktif. Jika keluar batas, alert dibuat.

**Q: Bagaimana fase budidaya ditentukan?**  
A: Fase bisa otomatis berdasarkan umur budidaya dari tanggal mulai, atau manual dipilih user.

**Q: Apakah AI dilatih sendiri?**  
A: Tidak. AI memakai external LLM Groq Llama 3.3. Project ini fokus pada integrasi data kandang dengan AI analysis.

**Q: Apa input untuk AI?**  
A: Input AI adalah pertanyaan user dan ringkasan data operasional seperti pakan, berat maggot, sensor, alert, dan perbandingan mingguan.

**Q: Apa output AI?**  
A: Output AI berupa analisis kondisi kandang dan rekomendasi tindakan dalam Bahasa Indonesia.

**Q: Apakah AI bisa menjawab semua hal?**  
A: Sistem memberi guardrail agar AI fokus pada maggot BSF, IoT, dan data kandang.

**Q: Bagaimana login diamankan?**  
A: Password disimpan dalam bentuk hash dengan salt, lalu sesi user menggunakan JWT.

**Q: Apa kelemahan project ini?**  
A: Masih local deployment, beberapa endpoint belum wajib token, JWT secret masih local dev, dan real-time UI masih polling.

**Q: Apa pengembangan berikutnya?**  
A: Deploy cloud, WebSocket real-time, role user, export PDF, kontrol aktuator otomatis, dan prediksi panen.

---

## N. Final Summary for Me to Memorize

Smart Maggot adalah dashboard IoT dan AI untuk budidaya maggot BSF. Sensor mengirim suhu dan kelembapan lewat MQTT. Backend FastAPI menyimpan data ke SQLite dan membuat alert jika kondisi keluar dari batas aman. Frontend React menampilkan dashboard, grafik monitoring, input pakan dan berat, laporan produksi, edukasi, dan AI Analysis. AI menggunakan Groq Llama 3.3 untuk membaca ringkasan data kandang dan memberi rekomendasi. Intinya, project ini membantu peternak memantau kandang, mencatat produksi, dan mengambil keputusan berbasis data.

---

## Simple Analogy

Bayangkan sistem ini seperti asisten kandang digital.

Sensor adalah mata dan telinga yang terus memantau suhu dan kelembapan. Backend adalah otak yang menyimpan dan mengecek data. Database adalah buku catatan. Frontend adalah papan kontrol yang dilihat user. AI adalah konsultan yang membaca buku catatan lalu memberi saran.

---

## Short Closing Statement

Dengan Smart Maggot, proses budidaya maggot menjadi lebih terukur karena data sensor, pencatatan produksi, alert, laporan, dan AI recommendation digabungkan dalam satu sistem yang mudah digunakan.

---

## Catatan Reviewer

Ada beberapa hal yang bisa disebut sebagai keterbatasan teknis:

- `run.ps1` masih mengarah ke versi Streamlit lama dan file `dashboardd.py` tidak ada.
- `auth.py` masih memiliki sisa UI Streamlit lama, sedangkan aplikasi utama sekarang memakai React.
- Beberapa teks memiliki encoding rusak seperti `Â°C`.
- Secret JWT masih hardcoded untuk local development.
- Beberapa endpoint belum sepenuhnya dilindungi token.

Kalimat aman untuk menjelaskan:

“Project ini saat ini masih tahap prototype lokal. Struktur utamanya sudah berjalan dengan React, FastAPI, SQLite, MQTT, dan Groq AI. Beberapa bagian lama dari versi sebelumnya masih ada dan bisa dibersihkan pada pengembangan berikutnya.”

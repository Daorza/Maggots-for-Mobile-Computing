import sqlite3
import random
from datetime import datetime, timedelta
import math

DB_FILE = "maggot_users.db"

def seed_database():
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()

    print("Memulai proses seeding database...")

    # 1. Pastikan ada user (opsional, tapi kita ambil user pertama atau buat dummy)
    cursor.execute("SELECT id FROM users LIMIT 1")
    user_row = cursor.fetchone()
    if user_row:
        user_id = user_row[0]
    else:
        cursor.execute("INSERT INTO users (username, password_hash) VALUES (?, ?)", ("admin", "dummy_hash"))
        user_id = cursor.lastrowid
        print("   - Membuat user dummy (admin)")

    # 2. Hapus data lama agar bersih
    cursor.execute("DELETE FROM sensor_logs")
    cursor.execute("DELETE FROM feed_logs")
    cursor.execute("DELETE FROM weight_logs")
    cursor.execute("DELETE FROM alerts")
    print("   - Menghapus data log lama")

    # 3. Parameter Seeding
    now = datetime.utcnow()
    days_to_seed = 30
    start_date = now - timedelta(days=days_to_seed)
    
    # 4. (Dihapus) Tidak men-seed sensor_logs dan alerts agar murni menggunakan data real-time MQTT.
    # Data lama sudah dihapus di langkah 2.

    # 5. Seed Feed Logs (2 kali sehari)
    print("   - Menghasilkan data pakan...")
    feed_data = []
    feed_types = ["Sisa Sayuran", "Limbah Buah", "Ampas Tahu", "Sisa Nasi"]
    
    for day in range(days_to_seed):
        current_day = start_date + timedelta(days=day)
        
        # Pakan pagi
        feed_data.append((
            user_id,
            current_day.strftime("%Y-%m-%d"),
            random.choice(feed_types),
            round(random.uniform(2.0, 5.0), 1),
            "Pemberian rutin pagi"
        ))
        
        # Pakan sore
        feed_data.append((
            user_id,
            current_day.strftime("%Y-%m-%d"),
            random.choice(feed_types),
            round(random.uniform(2.0, 4.0), 1),
            "Pemberian rutin sore"
        ))

    cursor.executemany("""
        INSERT INTO feed_logs (user_id, date, feed_type, feed_weight_kg, notes)
        VALUES (?, ?, ?, ?, ?)
    """, feed_data)
    print(f"     [OK] Berhasil insert {len(feed_data)} entri pakan")

    # 6. Seed Weight Logs (Setiap 3 hari sekali)
    print("   - Menghasilkan kurva pertumbuhan maggot...")
    weight_data = []
    current_weight = 0.05 # Mulai dari 50 gram (fase telur/larva awal)
    
    for day in range(0, days_to_seed, 3):
        current_day = start_date + timedelta(days=day)
        
        # Pertumbuhan eksponensial di awal, melambat di akhir
        growth = random.uniform(0.5, 1.5) if day < 15 else random.uniform(0.1, 0.4)
        current_weight += growth
        
        weight_data.append((
            user_id,
            current_day.strftime("%Y-%m-%d"),
            round(current_weight, 2),
            f"Pengecekan rutin hari ke-{day}"
        ))

    cursor.executemany("""
        INSERT INTO weight_logs (user_id, date, maggot_weight_kg, notes)
        VALUES (?, ?, ?, ?)
    """, weight_data)
    print(f"     [OK] Berhasil insert {len(weight_data)} entri berat maggot")

    # Commit dan Selesai
    conn.commit()
    conn.close()
    print("Seeding database selesai! Silakan muat ulang halaman dashboard Anda.")

if __name__ == "__main__":
    seed_database()

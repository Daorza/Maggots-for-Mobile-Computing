import sqlite3
import os
from config import AUTH_DB_FILE

def get_db_connection():
    conn = sqlite3.connect(AUTH_DB_FILE, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_db_connection()
    cursor = conn.cursor()

    # 1. sensor_logs
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS sensor_logs (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        temperature REAL NOT NULL,
        humidity REAL NOT NULL,
        phase TEXT,
        created_at DATETIME DEFAULT CURRENT_TIMESTAMP
    )
    """)

    # 2. alerts
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS alerts (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER,
        type TEXT NOT NULL,
        severity TEXT NOT NULL,
        message TEXT NOT NULL,
        value REAL,
        min_threshold REAL,
        max_threshold REAL,
        phase TEXT,
        is_read INTEGER DEFAULT 0,
        created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY(user_id) REFERENCES users(id)
    )
    """)

    # 3. cultivation_settings
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS cultivation_settings (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER,
        cultivation_start_date DATETIME,
        current_phase TEXT,
        phase_override_enabled INTEGER DEFAULT 0,
        manual_phase TEXT,
        updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY(user_id) REFERENCES users(id)
    )
    """)

    # 4. feed_logs
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS feed_logs (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER,
        date TEXT NOT NULL,
        feed_type TEXT,
        feed_weight_kg REAL NOT NULL,
        notes TEXT,
        created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY(user_id) REFERENCES users(id)
    )
    """)

    # 5. weight_logs
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS weight_logs (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER,
        date TEXT NOT NULL,
        maggot_weight_kg REAL NOT NULL,
        notes TEXT,
        created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY(user_id) REFERENCES users(id)
    )
    """)

    # 6. phase_thresholds
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS phase_thresholds (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        phase TEXT UNIQUE NOT NULL,
        temperature_min REAL NOT NULL,
        temperature_max REAL NOT NULL,
        humidity_min REAL NOT NULL,
        humidity_max REAL NOT NULL,
        created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
        updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
    )
    """)

    # Seed phase_thresholds
    default_thresholds = [
        ("Telur", 27.0, 30.0, 60.0, 80.0),
        ("Larva", 27.0, 32.0, 60.0, 75.0),
        ("Prepupa", 25.0, 30.0, 50.0, 70.0),
        ("Pupa", 25.0, 30.0, 50.0, 70.0),
        ("Lalat Dewasa", 27.0, 32.0, 50.0, 70.0),
    ]
    
    for th in default_thresholds:
        cursor.execute("""
        INSERT OR IGNORE INTO phase_thresholds 
        (phase, temperature_min, temperature_max, humidity_min, humidity_max)
        VALUES (?, ?, ?, ?, ?)
        """, th)

    # 7. ai_chats
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS ai_chats (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER,
        title TEXT NOT NULL,
        created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY(user_id) REFERENCES users(id)
    )
    """)

    # 8. ai_chat_messages
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS ai_chat_messages (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        chat_id INTEGER NOT NULL,
        role TEXT NOT NULL,
        content TEXT NOT NULL,
        created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY(chat_id) REFERENCES ai_chats(id) ON DELETE CASCADE
    )
    """)

    conn.commit()
    conn.close()

if __name__ == "__main__":
    init_db()
    print("Database schema successfully initialized.")

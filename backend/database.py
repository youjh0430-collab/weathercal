"""
Role: SQLite DB 연결 및 테이블 생성
Key Features: users, schedules, weather_cache, activities 테이블 관리
Dependencies: sqlite3 (Python 내장)
"""
import sqlite3
import os

DB_PATH = os.path.join(os.path.dirname(__file__), "weathercal.db")


def get_connection():
    """DB 연결 반환"""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA foreign_keys=ON")
    return conn


def init_db():
    """테이블 생성 — 앱 시작 시 1회 호출"""
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            provider TEXT NOT NULL,
            provider_id TEXT NOT NULL,
            name TEXT NOT NULL,
            profile_image TEXT,
            created_at TEXT DEFAULT (datetime('now', 'localtime')),
            UNIQUE (provider, provider_id)
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS schedules (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            title TEXT NOT NULL,
            date TEXT NOT NULL,
            time TEXT,
            category TEXT DEFAULT 'indoor',
            memo TEXT,
            created_at TEXT DEFAULT (datetime('now', 'localtime')),
            FOREIGN KEY (user_id) REFERENCES users(id)
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS weather_cache (
            date TEXT NOT NULL,
            station TEXT NOT NULL DEFAULT '서울',
            temperature REAL,
            temp_min REAL,
            temp_max REAL,
            condition TEXT,
            humidity REAL,
            wind_speed REAL,
            icon TEXT,
            fetched_at TEXT DEFAULT (datetime('now', 'localtime')),
            PRIMARY KEY (date, station)
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS activities (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            category TEXT NOT NULL,
            conditions TEXT NOT NULL,
            tags TEXT,
            is_active INTEGER DEFAULT 1
        )
    """)

    # 기존 schedules 테이블에 user_id 컬럼이 없으면 추가
    columns = [row[1] for row in cursor.execute("PRAGMA table_info(schedules)").fetchall()]
    if "user_id" not in columns:
        cursor.execute("ALTER TABLE schedules ADD COLUMN user_id INTEGER")

    conn.commit()
    conn.close()

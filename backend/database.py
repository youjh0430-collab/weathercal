"""
Role: SQLite DB 연결 및 테이블 생성
Key Features: schedules, weather_cache, activities 테이블 관리
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
    return conn


def init_db():
    """테이블 생성 — 앱 시작 시 1회 호출"""
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS schedules (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL,
            date TEXT NOT NULL,
            time TEXT,
            category TEXT DEFAULT 'indoor',
            memo TEXT,
            created_at TEXT DEFAULT (datetime('now', 'localtime'))
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS weather_cache (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            date TEXT NOT NULL UNIQUE,
            temperature REAL,
            condition TEXT,
            humidity INTEGER,
            wind_speed REAL,
            icon TEXT,
            fetched_at TEXT DEFAULT (datetime('now', 'localtime'))
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

    conn.commit()
    conn.close()

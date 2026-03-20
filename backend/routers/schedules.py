"""
Role: 일정 CRUD API 엔드포인트
Key Features: 월별 조회, 등록, 수정, 삭제
Dependencies: database, models
"""
from fastapi import APIRouter, HTTPException
from database import get_connection
from models import ScheduleCreate, ScheduleResponse

router = APIRouter(prefix="/api/schedules", tags=["일정"])


@router.get("")
def get_schedules(month: str):
    """월별 일정 조회 — month: '2026-03' 형식"""
    conn = get_connection()
    rows = conn.execute(
        "SELECT * FROM schedules WHERE date LIKE ? ORDER BY date, time",
        (f"{month}%",)
    ).fetchall()
    conn.close()
    return [dict(row) for row in rows]


@router.post("", status_code=201)
def create_schedule(data: ScheduleCreate):
    """일정 등록"""
    if not data.title.strip():
        raise HTTPException(status_code=400, detail="일정 제목을 입력해주세요")
    if not data.date.strip():
        raise HTTPException(status_code=400, detail="날짜를 입력해주세요")

    conn = get_connection()
    cursor = conn.execute(
        """INSERT INTO schedules (title, date, time, category, memo)
           VALUES (?, ?, ?, ?, ?)""",
        (data.title.strip(), data.date, data.time, data.category, data.memo)
    )
    schedule_id = cursor.lastrowid
    conn.commit()

    row = conn.execute("SELECT * FROM schedules WHERE id = ?", (schedule_id,)).fetchone()
    conn.close()
    return dict(row)


@router.put("/{schedule_id}")
def update_schedule(schedule_id: int, data: ScheduleCreate):
    """일정 수정"""
    conn = get_connection()
    existing = conn.execute("SELECT * FROM schedules WHERE id = ?", (schedule_id,)).fetchone()
    if not existing:
        conn.close()
        raise HTTPException(status_code=404, detail="일정을 찾을 수 없습니다")

    conn.execute(
        """UPDATE schedules SET title=?, date=?, time=?, category=?, memo=?
           WHERE id=?""",
        (data.title.strip(), data.date, data.time, data.category, data.memo, schedule_id)
    )
    conn.commit()

    row = conn.execute("SELECT * FROM schedules WHERE id = ?", (schedule_id,)).fetchone()
    conn.close()
    return dict(row)


@router.delete("/{schedule_id}")
def delete_schedule(schedule_id: int):
    """일정 삭제"""
    conn = get_connection()
    existing = conn.execute("SELECT * FROM schedules WHERE id = ?", (schedule_id,)).fetchone()
    if not existing:
        conn.close()
        raise HTTPException(status_code=404, detail="일정을 찾을 수 없습니다")

    conn.execute("DELETE FROM schedules WHERE id = ?", (schedule_id,))
    conn.commit()
    conn.close()
    return {"message": "일정이 삭제되었습니다"}

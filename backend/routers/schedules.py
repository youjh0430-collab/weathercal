"""
Role: 일정 CRUD API 엔드포인트 — 사용자별 일정 관리
Key Features: 월별 조회, 등록, 수정, 삭제, 로그인 사용자 필터링
Dependencies: database, models, routers.auth
"""
from fastapi import APIRouter, HTTPException, Request
from database import get_connection
from models import ScheduleCreate, ScheduleResponse
from routers.auth import get_current_user

router = APIRouter(prefix="/api/schedules", tags=["일정"])


def _require_login(request: Request) -> int:
    """로그인 필수 — user_id 반환"""
    user = get_current_user(request)
    if not user:
        raise HTTPException(status_code=401, detail="로그인이 필요합니다")
    return user["id"]


@router.get("")
def get_schedules(month: str, request: Request):
    """월별 일정 조회 — 로그인 사용자의 일정만"""
    user_id = _require_login(request)
    conn = get_connection()
    rows = conn.execute(
        "SELECT * FROM schedules WHERE user_id = ? AND date LIKE ? ORDER BY date, time",
        (user_id, f"{month}%")
    ).fetchall()
    conn.close()
    return [dict(row) for row in rows]


@router.post("", status_code=201)
def create_schedule(data: ScheduleCreate, request: Request):
    """일정 등록"""
    user_id = _require_login(request)

    if not data.title.strip():
        raise HTTPException(status_code=400, detail="일정 제목을 입력해주세요")
    if not data.date.strip():
        raise HTTPException(status_code=400, detail="날짜를 입력해주세요")

    conn = get_connection()
    cursor = conn.execute(
        """INSERT INTO schedules (user_id, title, date, time, category, memo)
           VALUES (?, ?, ?, ?, ?, ?)""",
        (user_id, data.title.strip(), data.date, data.time, data.category, data.memo)
    )
    schedule_id = cursor.lastrowid
    conn.commit()

    row = conn.execute("SELECT * FROM schedules WHERE id = ?", (schedule_id,)).fetchone()
    conn.close()
    return dict(row)


@router.put("/{schedule_id}")
def update_schedule(schedule_id: int, data: ScheduleCreate, request: Request):
    """일정 수정 — 본인 일정만"""
    user_id = _require_login(request)
    conn = get_connection()
    existing = conn.execute(
        "SELECT * FROM schedules WHERE id = ? AND user_id = ?", (schedule_id, user_id)
    ).fetchone()
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
def delete_schedule(schedule_id: int, request: Request):
    """일정 삭제 — 본인 일정만"""
    user_id = _require_login(request)
    conn = get_connection()
    existing = conn.execute(
        "SELECT * FROM schedules WHERE id = ? AND user_id = ?", (schedule_id, user_id)
    ).fetchone()
    if not existing:
        conn.close()
        raise HTTPException(status_code=404, detail="일정을 찾을 수 없습니다")

    conn.execute("DELETE FROM schedules WHERE id = ?", (schedule_id,))
    conn.commit()
    conn.close()
    return {"message": "일정이 삭제되었습니다"}

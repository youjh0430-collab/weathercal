"""
Role: FastAPI 앱 생성, 라우터 등록, 정적 파일 서빙
Key Features: 앱 시작 시 DB 초기화, CORS 설정, 보안 헤더, StaticFiles 마운트
Dependencies: fastapi, uvicorn, routers, database
"""
from fastapi import FastAPI, Request
from fastapi.staticfiles import StaticFiles
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from starlette.middleware.base import BaseHTTPMiddleware
from contextlib import asynccontextmanager
import os
import logging
import traceback

from database import init_db
from routers import auth, schedules, weather, briefing

logger = logging.getLogger(__name__)

# 허용 도메인 — 환경변수로 관리
ALLOWED_ORIGINS = os.getenv(
    "ALLOWED_ORIGINS",
    "http://localhost:8000,http://127.0.0.1:8000"
).split(",")


@asynccontextmanager
async def lifespan(app: FastAPI):
    """앱 시작 시 DB 초기화"""
    init_db()
    yield


app = FastAPI(title="WeatherCal", lifespan=lifespan)


@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """전역 예외 처리 — 서버 로그에만 상세 기록, 클라이언트에는 최소 정보만 반환"""
    logger.error(f"Unhandled Exception: {exc}")
    logger.error(traceback.format_exc())
    return JSONResponse(
        status_code=500,
        content={"error": "서버에서 오류가 발생했습니다. 잠시 후 다시 시도해주세요."}
    )


# 보안 헤더 미들웨어 — XSS, 클릭재킹, MIME 스니핑 방지
class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request, call_next):
        response = await call_next(request)
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["X-XSS-Protection"] = "1; mode=block"
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
        return response

app.add_middleware(SecurityHeadersMiddleware)

app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_methods=["GET", "POST", "PUT", "DELETE"],
    allow_headers=["Content-Type"],
    allow_credentials=True,
)

app.include_router(auth.router)
app.include_router(schedules.router)
app.include_router(weather.router)
app.include_router(briefing.router)

frontend_path = os.path.join(os.path.dirname(__file__), "..", "frontend")
if os.path.exists(frontend_path):
    app.mount("/", StaticFiles(directory=frontend_path, html=True), name="frontend")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)

"""
Role: FastAPI 앱 생성, 라우터 등록, 정적 파일 서빙
Key Features: 앱 시작 시 DB 초기화, CORS 설정, StaticFiles 마운트
Dependencies: fastapi, uvicorn, routers, database
"""
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
import os

from database import init_db
from routers import auth, schedules, weather, briefing


@asynccontextmanager
async def lifespan(app: FastAPI):
    """앱 시작 시 DB 초기화"""
    init_db()
    yield


app = FastAPI(title="WeatherCal", lifespan=lifespan)

from fastapi import Request
from fastapi.responses import JSONResponse
import traceback

@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    print(f"Unhandled Exception: {exc}")
    print(traceback.format_exc())
    return JSONResponse(
        status_code=500,
        content={
            "error": "Internal Server Error",
            "detail": str(exc),
            "traceback": traceback.format_exc()
        }
    )

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
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

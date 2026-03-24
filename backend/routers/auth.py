"""
Role: Google/카카오 소셜 로그인 OAuth 처리
Key Features: OAuth 리다이렉트, 콜백 처리, 세션 쿠키 발급, 로그아웃
Dependencies: httpx, itsdangerous, database
"""
import os
import httpx
from urllib.parse import urlencode
from fastapi import APIRouter, Request, Response, HTTPException
from fastapi.responses import RedirectResponse
from itsdangerous import URLSafeSerializer
from database import get_connection

router = APIRouter(prefix="/api/auth", tags=["인증"])

GOOGLE_CLIENT_ID = os.getenv("GOOGLE_CLIENT_ID")
GOOGLE_CLIENT_SECRET = os.getenv("GOOGLE_CLIENT_SECRET")
KAKAO_CLIENT_ID = os.getenv("KAKAO_CLIENT_ID")

# 세션 서명용 시크릿 — 환경변수 없으면 기본값 사용
SESSION_SECRET = os.getenv("SESSION_SECRET", "weathercal-session-secret-key")
serializer = URLSafeSerializer(SESSION_SECRET)

COOKIE_NAME = "session"


def _get_base_url(request: Request) -> str:
    """요청에서 base URL 추출 — Render 프록시 환경 대응"""
    proto = request.headers.get("x-forwarded-proto", "http")
    host = request.headers.get("x-forwarded-host") or request.headers.get("host", "localhost:8000")
    return f"{proto}://{host}"


def get_current_user(request: Request) -> dict | None:
    """쿠키에서 현재 로그인 사용자 정보 추출"""
    token = request.cookies.get(COOKIE_NAME)
    if not token:
        return None
    try:
        user_id = serializer.loads(token)
        conn = get_connection()
        row = conn.execute("SELECT * FROM users WHERE id = ?", (user_id,)).fetchone()
        conn.close()
        if row:
            return {"id": row["id"], "name": row["name"], "provider": row["provider"], "profile_image": row["profile_image"]}
    except Exception:
        pass
    return None


def _set_session_cookie(response: Response, user_id: int):
    """세션 쿠키 설정"""
    token = serializer.dumps(user_id)
    response.set_cookie(
        COOKIE_NAME, token,
        httponly=True,
        secure=True,
        samesite="lax",
        max_age=60 * 60 * 24 * 30,  # 30일
    )


def _upsert_user(provider: str, provider_id: str, name: str, profile_image: str = None) -> int:
    """사용자 조회 또는 생성 — user id 반환"""
    conn = get_connection()
    row = conn.execute(
        "SELECT id FROM users WHERE provider = ? AND provider_id = ?",
        (provider, provider_id)
    ).fetchone()

    if row:
        user_id = row["id"]
        conn.execute(
            "UPDATE users SET name = ?, profile_image = ? WHERE id = ?",
            (name, profile_image, user_id)
        )
    else:
        cursor = conn.execute(
            "INSERT INTO users (provider, provider_id, name, profile_image) VALUES (?, ?, ?, ?)",
            (provider, provider_id, name, profile_image)
        )
        user_id = cursor.lastrowid

    conn.commit()
    conn.close()
    return user_id


# === 현재 사용자 정보 API ===

@router.get("/me")
def get_me(request: Request):
    """로그인 상태 확인"""
    user = get_current_user(request)
    if not user:
        return {"logged_in": False}
    return {"logged_in": True, **user}


# === Google OAuth ===

@router.get("/google/login")
def google_login(request: Request):
    """Google 로그인 페이지로 리다이렉트"""
    base_url = _get_base_url(request)
    params = {
        "client_id": GOOGLE_CLIENT_ID,
        "redirect_uri": f"{base_url}/api/auth/google/callback",
        "response_type": "code",
        "scope": "openid email profile",
    }
    return RedirectResponse(f"https://accounts.google.com/o/oauth2/v2/auth?{urlencode(params)}")


@router.get("/google/callback")
async def google_callback(request: Request, code: str):
    """Google OAuth 콜백 — 토큰 교환 + 사용자 정보 조회"""
    base_url = _get_base_url(request)

    # 인가 코드로 액세스 토큰 교환
    async with httpx.AsyncClient() as client:
        token_res = await client.post("https://oauth2.googleapis.com/token", data={
            "code": code,
            "client_id": GOOGLE_CLIENT_ID,
            "client_secret": GOOGLE_CLIENT_SECRET,
            "redirect_uri": f"{base_url}/api/auth/google/callback",
            "grant_type": "authorization_code",
        })

    if token_res.status_code != 200:
        raise HTTPException(400, "Google 로그인에 실패했습니다")

    access_token = token_res.json().get("access_token")

    # 사용자 정보 조회
    async with httpx.AsyncClient() as client:
        user_res = await client.get(
            "https://www.googleapis.com/oauth2/v2/userinfo",
            headers={"Authorization": f"Bearer {access_token}"}
        )

    if user_res.status_code != 200:
        raise HTTPException(400, "사용자 정보 조회에 실패했습니다")

    user_info = user_res.json()
    user_id = _upsert_user(
        provider="google",
        provider_id=str(user_info["id"]),
        name=user_info.get("name", "사용자"),
        profile_image=user_info.get("picture"),
    )

    response = RedirectResponse("/")
    _set_session_cookie(response, user_id)
    return response


# === 카카오 OAuth ===

@router.get("/kakao/login")
def kakao_login(request: Request):
    """카카오 로그인 페이지로 리다이렉트"""
    base_url = _get_base_url(request)
    params = {
        "client_id": KAKAO_CLIENT_ID,
        "redirect_uri": f"{base_url}/api/auth/kakao/callback",
        "response_type": "code",
    }
    return RedirectResponse(f"https://kauth.kakao.com/oauth/authorize?{urlencode(params)}")


@router.get("/kakao/callback")
async def kakao_callback(request: Request, code: str):
    """카카오 OAuth 콜백 — 토큰 교환 + 사용자 정보 조회"""
    base_url = _get_base_url(request)

    # 인가 코드로 액세스 토큰 교환
    async with httpx.AsyncClient() as client:
        token_res = await client.post("https://kauth.kakao.com/oauth/token", data={
            "grant_type": "authorization_code",
            "client_id": KAKAO_CLIENT_ID,
            "redirect_uri": f"{base_url}/api/auth/kakao/callback",
            "code": code,
        })

    if token_res.status_code != 200:
        raise HTTPException(400, "카카오 로그인에 실패했습니다")

    access_token = token_res.json().get("access_token")

    # 사용자 정보 조회
    async with httpx.AsyncClient() as client:
        user_res = await client.get(
            "https://kapi.kakao.com/v2/user/me",
            headers={"Authorization": f"Bearer {access_token}"}
        )

    if user_res.status_code != 200:
        raise HTTPException(400, "사용자 정보 조회에 실패했습니다")

    user_info = user_res.json()
    kakao_id = str(user_info["id"])
    profile = user_info.get("kakao_account", {}).get("profile", {})
    name = profile.get("nickname", "사용자")
    profile_image = profile.get("profile_image_url")

    user_id = _upsert_user(
        provider="kakao",
        provider_id=kakao_id,
        name=name,
        profile_image=profile_image,
    )

    response = RedirectResponse("/")
    _set_session_cookie(response, user_id)
    return response


# === 로그아웃 ===

@router.get("/logout")
def logout():
    """로그아웃 — 세션 쿠키 삭제"""
    response = RedirectResponse("/")
    response.delete_cookie(COOKIE_NAME)
    return response

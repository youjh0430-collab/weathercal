/**
 * Role: 서버 API 호출 래퍼 + 인증 상태 관리
 * Key Features: fetch 기반 CRUD, 지역 파라미터, 로그인 체크, 401 리다이렉트
 * Dependencies: 없음
 */

const API_BASE = '/api';

function getStation() {
    return document.getElementById('station-select').value;
}

/** 응답 처리 — 401이면 로그인 페이지로 이동 */
async function handleResponse(res) {
    if (res.status === 401) {
        window.location.href = '/login.html';
        throw new Error('로그인이 필요합니다');
    }
    return res;
}

const api = {
    /** 로그인 상태 확인 */
    async getMe() {
        const res = await fetch(`${API_BASE}/auth/me`);
        return res.json();
    },

    async getSchedules(month) {
        const res = await handleResponse(await fetch(`${API_BASE}/schedules?month=${month}`));
        return res.json();
    },

    async createSchedule(data) {
        const res = await handleResponse(await fetch(`${API_BASE}/schedules`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(data)
        }));
        if (!res.ok) {
            const err = await res.json();
            throw new Error(err.detail || '일정 저장에 실패했습니다');
        }
        return res.json();
    },

    async updateSchedule(id, data) {
        const res = await handleResponse(await fetch(`${API_BASE}/schedules/${id}`, {
            method: 'PUT',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(data)
        }));
        if (!res.ok) {
            const err = await res.json();
            throw new Error(err.detail || '일정 수정에 실패했습니다');
        }
        return res.json();
    },

    async deleteSchedule(id) {
        const res = await handleResponse(await fetch(`${API_BASE}/schedules/${id}`, {
            method: 'DELETE'
        }));
        if (!res.ok) {
            const err = await res.json();
            throw new Error(err.detail || '일정 삭제에 실패했습니다');
        }
        return res.json();
    },

    async getWeather(month) {
        const station = getStation();
        const res = await fetch(`${API_BASE}/weather?month=${month}&station=${encodeURIComponent(station)}`);
        return res.json();
    },

    async getBriefing(date) {
        const station = getStation();
        const res = await fetch(`${API_BASE}/briefing/${date}?station=${encodeURIComponent(station)}`);
        return res.json();
    }
};

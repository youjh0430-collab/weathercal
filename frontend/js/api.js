/**
 * Role: 서버 API 호출 래퍼
 * Key Features: fetch 기반 GET/POST/PUT/DELETE
 * Dependencies: 없음
 */

const API_BASE = '/api';

const api = {
    async getSchedules(month) {
        const res = await fetch(`${API_BASE}/schedules?month=${month}`);
        return res.json();
    },

    async createSchedule(data) {
        const res = await fetch(`${API_BASE}/schedules`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(data)
        });
        if (!res.ok) {
            const err = await res.json();
            throw new Error(err.detail || '일정 저장에 실패했습니다');
        }
        return res.json();
    },

    async updateSchedule(id, data) {
        const res = await fetch(`${API_BASE}/schedules/${id}`, {
            method: 'PUT',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(data)
        });
        if (!res.ok) {
            const err = await res.json();
            throw new Error(err.detail || '일정 수정에 실패했습니다');
        }
        return res.json();
    },

    async deleteSchedule(id) {
        const res = await fetch(`${API_BASE}/schedules/${id}`, {
            method: 'DELETE'
        });
        if (!res.ok) {
            const err = await res.json();
            throw new Error(err.detail || '일정 삭제에 실패했습니다');
        }
        return res.json();
    },

    async getWeather(month) {
        const res = await fetch(`${API_BASE}/weather?month=${month}`);
        return res.json();
    },

    async getBriefing(date) {
        const res = await fetch(`${API_BASE}/briefing/${date}`);
        return res.json();
    }
};
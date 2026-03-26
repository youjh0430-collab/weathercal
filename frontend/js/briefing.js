/**
 * Role: 날짜 클릭 시 바텀시트 브리핑 카드 렌더링
 * Key Features: 날씨 상세, 일정 목록(경고 포함), 활동 추천, 오버레이
 * Dependencies: api.js
 */

// 날씨 상태별 그라데이션 — 브리핑 날씨 카드 배경에 적용
const WEATHER_GRADIENTS = {
    'sunny':        'linear-gradient(135deg, #f6d365 0%, #fda085 100%)',
    'partly_cloudy':'linear-gradient(135deg, #89b4e0 0%, #c4b5d0 100%)',
    'cloudy':       'linear-gradient(135deg, #9eaab7 0%, #bec8d1 100%)',
    'rain':         'linear-gradient(135deg, #2c3e50 0%, #4ca1af 100%)',
    'snow':         'linear-gradient(135deg, #e6e9f0 0%, #c3cfe2 100%)',
    'sleet':        'linear-gradient(135deg, #536976 0%, #7d96a1 100%)',
};

// 눈·흐림 등 밝은 배경에서 텍스트 가독성 확보
const WEATHER_DARK_TEXT = ['snow', 'cloudy'];

let currentBriefingDate = null;

// HTML 특수문자 이스케이프 — XSS 방지용
function escapeHtml(str) {
    if (!str) return '';
    const map = { '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#039;' };
    return String(str).replace(/[&<>"']/g, c => map[c]);
}

function closeBriefing() {
    document.getElementById('briefing-panel').classList.add('hidden');
    document.getElementById('briefing-overlay').classList.add('hidden');
}

async function openBriefing(dateStr) {
    currentBriefingDate = dateStr;
    const panel = document.getElementById('briefing-panel');
    const overlay = document.getElementById('briefing-overlay');
    const content = document.getElementById('briefing-content');

    const dateObj = new Date(dateStr + 'T00:00:00');
    const dayNames = ['일', '월', '화', '수', '목', '금', '토'];
    document.getElementById('briefing-date').textContent =
        `📅 ${dateObj.getMonth() + 1}월 ${dateObj.getDate()}일 (${dayNames[dateObj.getDay()]})`;

    const briefing = await api.getBriefing(dateStr);

    let html = '';

    if (briefing.weather) {
        const w = briefing.weather;
        const icon = WEATHER_ICONS[w.icon] || '🌡';
        const gradient = WEATHER_GRADIENTS[w.icon] || 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)';
        const textColor = WEATHER_DARK_TEXT.includes(w.icon) ? '#333' : '#fff';
        html += `
            <div class="card weather-card" style="background: ${gradient}; color: ${textColor};">
                <div class="card-icon">${icon}</div>
                <div class="card-body">
                    <div class="weather-main">${w.condition} ${w.temp_min != null && w.temp_max != null ? `${w.temp_min}° / ${w.temp_max}°` : `${w.temperature}°C`}</div>
                    <div class="weather-detail">${[w.humidity != null ? `습도 ${w.humidity}%` : '', w.wind_speed != null ? `풍속 ${w.wind_speed}m/s` : ''].filter(Boolean).join(' | ') || ''}</div>
                </div>
            </div>
        `;
    } else {
        html += `<div class="card no-data">날씨 정보가 없습니다</div>`;
    }

    if (briefing.schedules.length > 0) {
        briefing.schedules.forEach(s => {
            const timeStr = s.time ? s.time : '종일';
            const warningHtml = s.warnings.length > 0
                ? s.warnings.map(w => `<div class="warning">${w}</div>`).join('')
                : '<div class="no-warning">날씨 좋음! 👍</div>';

            html += `
                <div class="card schedule-card">
                    <div class="schedule-header">
                        <span class="schedule-time">📌 ${escapeHtml(timeStr)}</span>
                        <span class="schedule-title">${escapeHtml(s.title)}</span>
                        <span class="schedule-category ${s.category}">${s.category === 'outdoor' ? '야외' : '실내'}</span>
                    </div>
                    ${warningHtml}
                    <div class="schedule-actions">
                        <button class="btn-small" onclick="editSchedule(${parseInt(s.id)})">수정</button>
                        <button class="btn-small btn-danger" onclick="deleteScheduleAndRefresh(${parseInt(s.id)})">삭제</button>
                    </div>
                </div>
            `;
        });
    }

    if (briefing.recommendations.length > 0) {
        html += `
            <div class="card recommend-card">
                <div class="card-title">💡 이런 건 어때요?</div>
                <ul class="recommend-list">
                    ${briefing.recommendations.map(r => `<li>${r}</li>`).join('')}
                </ul>
            </div>
        `;
    }

    content.innerHTML = html;
    panel.classList.remove('hidden');
    overlay.classList.remove('hidden');
}

document.addEventListener('DOMContentLoaded', () => {
    document.getElementById('close-briefing').addEventListener('click', closeBriefing);
    document.getElementById('briefing-overlay').addEventListener('click', closeBriefing);

    document.getElementById('add-schedule-date-btn').addEventListener('click', () => {
        if (currentBriefingDate) {
            openScheduleModal(null, currentBriefingDate);
        }
    });
});

async function deleteScheduleAndRefresh(id) {
    if (!confirm('이 일정을 삭제하시겠습니까?')) return;
    try {
        await api.deleteSchedule(id);
        await renderCalendar();
        if (currentBriefingDate) {
            await openBriefing(currentBriefingDate);
        }
    } catch (e) {
        alert(e.message);
    }
}

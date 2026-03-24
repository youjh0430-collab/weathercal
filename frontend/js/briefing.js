/**
 * Role: 날짜 클릭 시 바텀시트 브리핑 카드 렌더링
 * Key Features: 날씨 상세, 일정 목록(경고 포함), 활동 추천, 오버레이
 * Dependencies: api.js
 */

let currentBriefingDate = null;

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
        html += `
            <div class="card weather-card">
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
                        <span class="schedule-time">📌 ${timeStr}</span>
                        <span class="schedule-title">${s.title}</span>
                        <span class="schedule-category ${s.category}">${s.category === 'outdoor' ? '야외' : '실내'}</span>
                    </div>
                    ${warningHtml}
                    <div class="schedule-actions">
                        <button class="btn-small" onclick="editSchedule(${s.id})">수정</button>
                        <button class="btn-small btn-danger" onclick="deleteScheduleAndRefresh(${s.id})">삭제</button>
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

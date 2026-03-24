/**
 * Role: 월간 캘린더 + 다가오는 일정 카드 + 오늘 날씨 카드 렌더링
 * Key Features: 월 이동, 날씨 아이콘, 일정 미리보기, 다가오는 일정 횡스크롤, 오늘 날씨 대형 카드
 * Dependencies: api.js
 */

const WEATHER_ICONS = {
    'sunny': '☀️',
    'partly_cloudy': '⛅',
    'cloudy': '☁️',
    'rain': '🌧',
    'snow': '🌨',
    'sleet': '🌧',
};

// 오늘 날씨 카드용 — 아이폰 날씨앱 스타일 테마 클래스
const TODAY_WEATHER_THEMES = {
    'sunny':        'theme-sunny',
    'partly_cloudy': 'theme-partly-cloudy',
    'cloudy':       'theme-cloudy',
    'rain':         'theme-rain',
    'snow':         'theme-snow',
    'sleet':        'theme-sleet',
};

let currentYear, currentMonth;
let weatherData = {};
let scheduleData = {};

document.addEventListener('DOMContentLoaded', () => {
    const now = new Date();
    currentYear = now.getFullYear();
    currentMonth = now.getMonth() + 1;

    document.getElementById('prev-month').addEventListener('click', () => changeMonth(-1));
    document.getElementById('next-month').addEventListener('click', () => changeMonth(1));
    document.getElementById('station-select').addEventListener('change', () => renderCalendar());

    renderCalendar();
});

function changeMonth(delta) {
    currentMonth += delta;
    if (currentMonth > 12) { currentMonth = 1; currentYear++; }
    if (currentMonth < 1) { currentMonth = 12; currentYear--; }
    renderCalendar();
}

async function renderCalendar() {
    const monthStr = `${currentYear}-${String(currentMonth).padStart(2, '0')}`;
    document.getElementById('current-year').textContent = `${currentYear}년`;
    document.getElementById('current-month').textContent = `${currentMonth}월`;

    try {
        const [weatherList, scheduleList] = await Promise.all([
            api.getWeather(monthStr),
            api.getSchedules(monthStr)
        ]);

        weatherData = {};
        weatherList.forEach(w => { weatherData[w.date] = w; });

        scheduleData = {};
        scheduleList.forEach(s => {
            if (!scheduleData[s.date]) scheduleData[s.date] = [];
            scheduleData[s.date].push(s);
        });
    } catch (e) {
        console.error('데이터 로드 실패:', e);
    }

    renderDays();
    renderUpcoming();
    renderTodayWeather();
}

function renderDays() {
    const grid = document.getElementById('calendar-grid');
    grid.querySelectorAll('.day-cell').forEach(el => el.remove());

    const firstDay = new Date(currentYear, currentMonth - 1, 1);
    const lastDay = new Date(currentYear, currentMonth, 0);

    // 일요일 시작 (0=일, 1=월, ..., 6=토)
    let startDay = firstDay.getDay();

    const today = new Date();
    today.setHours(0, 0, 0, 0);

    for (let i = 0; i < startDay; i++) {
        const empty = document.createElement('div');
        empty.className = 'day-cell empty';
        grid.appendChild(empty);
    }

    for (let d = 1; d <= lastDay.getDate(); d++) {
        const dateStr = `${currentYear}-${String(currentMonth).padStart(2, '0')}-${String(d).padStart(2, '0')}`;
        const cellDate = new Date(currentYear, currentMonth - 1, d);

        const cell = document.createElement('div');
        cell.className = 'day-cell';
        cell.dataset.date = dateStr;

        if (cellDate.getTime() === today.getTime()) {
            cell.classList.add('today');
        }

        const topRow = document.createElement('div');
        topRow.className = 'day-top';

        const dateNum = document.createElement('span');
        dateNum.className = 'date-number';
        dateNum.textContent = d;
        topRow.appendChild(dateNum);

        const weather = weatherData[dateStr];
        if (weather && weather.icon) {
            const iconSpan = document.createElement('span');
            iconSpan.className = 'weather-icon';
            iconSpan.textContent = WEATHER_ICONS[weather.icon] || '';
            if (weather.is_past) {
                iconSpan.classList.add('past');
            }
            topRow.appendChild(iconSpan);
        }

        cell.appendChild(topRow);

        // 일정 미리보기 (최대 2개)
        if (scheduleData[dateStr] && scheduleData[dateStr].length > 0) {
            const maxShow = 2;
            const schedules = scheduleData[dateStr];

            schedules.slice(0, maxShow).forEach(s => {
                const item = document.createElement('div');
                item.className = 'schedule-preview';
                item.textContent = s.title;
                cell.appendChild(item);
            });

            if (schedules.length > maxShow) {
                const more = document.createElement('div');
                more.className = 'schedule-more';
                more.textContent = `+${schedules.length - maxShow}개`;
                cell.appendChild(more);
            }
        }

        cell.addEventListener('click', () => {
            document.querySelectorAll('.day-cell.selected').forEach(el => el.classList.remove('selected'));
            cell.classList.add('selected');
            openBriefing(dateStr);
        });

        grid.appendChild(cell);
    }
}

/** 다가오는 일정 — 오늘 이후 7일 내 일정을 가로 스크롤 카드로 표시 */
function renderUpcoming() {
    const container = document.getElementById('upcoming-cards');
    const today = new Date();
    today.setHours(0, 0, 0, 0);

    // 오늘~7일 후 일정 수집
    const upcoming = [];
    for (let i = 0; i < 7; i++) {
        const d = new Date(today);
        d.setDate(d.getDate() + i);
        const dateStr = d.toISOString().split('T')[0];
        const daySchedules = scheduleData[dateStr];
        if (daySchedules) {
            daySchedules.forEach(s => {
                upcoming.push({ ...s, _date: d, _dateStr: dateStr, _offset: i });
            });
        }
    }

    if (upcoming.length === 0) {
        container.innerHTML = '<div class="upcoming-empty">다가오는 일정이 없습니다</div>';
        return;
    }

    const dayNames = ['일', '월', '화', '수', '목', '금', '토'];
    let html = '';

    upcoming.forEach(s => {
        // 뱃지 텍스트
        let badge, badgeClass;
        if (s._offset === 0) {
            badge = '오늘';
            badgeClass = 'upcoming-badge today';
        } else if (s._offset === 1) {
            badge = '내일';
            badgeClass = 'upcoming-badge';
        } else {
            const m = s._date.getMonth() + 1;
            const dd = s._date.getDate();
            const dow = dayNames[s._date.getDay()];
            badge = `${m}/${dd} (${dow})`;
            badgeClass = 'upcoming-badge';
        }

        // 날씨 정보
        const w = weatherData[s._dateStr];
        const weatherText = w ? `${WEATHER_ICONS[w.icon] || ''} ${w.condition}` : '';

        const timeText = s.time || '종일';

        html += `
            <div class="upcoming-card" onclick="openBriefing('${s._dateStr}')">
                <span class="${badgeClass}">${badge}</span>
                <span class="upcoming-weather">${weatherText}</span>
                <div class="upcoming-title">${s.title}</div>
                <div class="upcoming-time">🕐 ${timeText}</div>
            </div>
        `;
    });

    container.innerHTML = html;
}

/** 오늘 날씨 대형 카드 렌더링 */
function renderTodayWeather() {
    const today = new Date().toISOString().split('T')[0];
    const w = weatherData[today];
    const card = document.getElementById('today-weather-card');

    if (!w) {
        card.style.display = 'none';
        return;
    }
    card.style.display = 'block';

    // 날씨 테마 적용 — CSS 클래스 기반 (아이폰 날씨앱 스타일)
    const themeClass = TODAY_WEATHER_THEMES[w.icon] || 'theme-sunny';
    card.className = card.className.replace(/\btheme-\S+/g, '').trim();
    card.classList.add(themeClass);

    const icon = WEATHER_ICONS[w.icon] || '🌡';
    document.getElementById('today-weather-icon').textContent = icon;

    // 온도 표시 — 최저/최고
    const tempEl = document.getElementById('today-temp');
    if (w.temp_min != null && w.temp_max != null) {
        tempEl.innerHTML = `${w.temp_min}°<span class="temp-separator"> / </span>${w.temp_max}`;
    } else if (w.temperature != null) {
        tempEl.textContent = w.temperature;
    } else {
        tempEl.textContent = '--';
    }

    document.getElementById('today-condition').textContent = w.condition || '';

    // 하단 상세 정보
    const details = document.getElementById('today-details');
    let detailHtml = '';

    if (w.humidity != null) {
        detailHtml += `
            <div class="today-detail-item">
                <span class="today-detail-label">습도</span>
                <span class="today-detail-value">${w.humidity}%</span>
            </div>`;
    }
    if (w.wind_speed != null) {
        detailHtml += `
            <div class="today-detail-item">
                <span class="today-detail-label">풍속</span>
                <span class="today-detail-value">${w.wind_speed}m/s</span>
            </div>`;
    }
    if (w.temp_min != null && w.temp_max != null) {
        detailHtml += `
            <div class="today-detail-item">
                <span class="today-detail-label">일교차</span>
                <span class="today-detail-value">${(w.temp_max - w.temp_min).toFixed(0)}°</span>
            </div>`;
    }

    details.innerHTML = detailHtml;
}

window.renderCalendar = renderCalendar;

/**
 * Role: 월간 캘린더 렌더링 + 날짜 클릭 이벤트
 * Key Features: 월 이동, 날씨 아이콘 표시 (과거=회색, 미래=컬러), 일정 유무 표시
 * Dependencies: api.js
 */

const WEATHER_ICONS = {
    '01d': '☀️', '01n': '🌙',
    '02d': '🌤', '02n': '☁️',
    '03d': '⛅', '03n': '⛅',
    '04d': '☁️', '04n': '☁️',
    '09d': '🌧', '09n': '🌧',
    '10d': '🌦', '10n': '🌧',
    '11d': '⛈', '11n': '⛈',
    '13d': '🌨', '13n': '🌨',
    '50d': '🌫', '50n': '🌫'
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
    document.getElementById('current-month').textContent = `${currentYear}년 ${currentMonth}월`;

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
}

function renderDays() {
    const grid = document.getElementById('calendar-grid');
    grid.querySelectorAll('.day-cell').forEach(el => el.remove());

    const firstDay = new Date(currentYear, currentMonth - 1, 1);
    const lastDay = new Date(currentYear, currentMonth, 0);

    let startDay = firstDay.getDay() - 1;
    if (startDay < 0) startDay = 6;

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

        const dateNum = document.createElement('span');
        dateNum.className = 'date-number';
        dateNum.textContent = d;
        cell.appendChild(dateNum);

        const weather = weatherData[dateStr];
        if (weather && weather.icon) {
            const iconSpan = document.createElement('span');
            iconSpan.className = 'weather-icon';
            iconSpan.textContent = WEATHER_ICONS[weather.icon] || '';

            if (weather.is_past) {
                iconSpan.classList.add('past');
            }
            cell.appendChild(iconSpan);
        }

        if (scheduleData[dateStr] && scheduleData[dateStr].length > 0) {
            const dot = document.createElement('span');
            dot.className = 'schedule-dot';
            dot.textContent = '•';
            cell.appendChild(dot);
        }

        cell.addEventListener('click', () => openBriefing(dateStr));

        grid.appendChild(cell);
    }
}

window.renderCalendar = renderCalendar;
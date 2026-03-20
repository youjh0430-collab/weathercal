/**
 * Role: 일정 추가/수정 모달 + 키워드 자동 분류
 * Key Features: 모달 열기/닫기, 제목 입력 시 자동 분류, CRUD 연동
 * Dependencies: api.js
 */

const OUTDOOR_KW = [
    '등산', '산책', '러닝', '조깅', '마라톤', '자전거', '라이딩', '축구', '야구',
    '농구', '테니스', '배드민턴', '골프', '서핑', '스키', '보드', '인라인', '족구',
    '게이트볼', '피크닉', '캠핑', '글램핑', '낚시', '바베큐', '드라이브', '꽃구경',
    '단풍', '벚꽃', '눈썰매', '놀이공원', '워터파크', '한강', '공원', '둘레길',
    '야경', '별보기', '해돋이', '해넘이', '시장', '플리마켓', '야시장', '푸드트럭',
    '전통시장', '수산시장', '포장마차', '루프탑', '야외테라스', '길거리음식',
    '김장', '고구마캐기', '감따기', '매실담기', '텃밭',
    '빨래', '이불빨래', '세차', '베란다청소', '화분물주기',
    '출장', '현장답사', '야외촬영'
];

const INDOOR_KW = [
    '헬스', '필라테스', '요가', '크로스핏', '볼링', '당구', '탁구', '스쿼시',
    '영화', '독서', '카페', '전시', '미술관', '박물관', '공연', '뮤지컬', '콘서트',
    '연극', '노래방', '방탈출', '보드게임', '만화카페', '찜질방', '스파',
    '코인노래방', '멀티방', 'PC방',
    '쇼핑', '백화점', '마트', '아울렛', '다이소', '쇼핑몰',
    '맛집', '브런치', '회식', '저녁약속', '점심약속', '술약속', '고깃집',
    '치맥', '소맥', '포차', '이자카야', '와인바',
    '두쫀쿠', '달고나커피', '탕후루', '약과', '송편', '떡만들기',
    '수정과', '식혜', '김치담기',
    '대청소', '요리', '베이킹', '넷플릭스', '집콕', '재택', '옷장정리', '냉장고파먹기',
    '회의', '스터디', '학원', '과외', '면접', '재택근무', '독서실', '토익'
];

let editingScheduleId = null;

function classifyTitle(title) {
    for (const kw of OUTDOOR_KW) {
        if (title.includes(kw)) return 'outdoor';
    }
    for (const kw of INDOOR_KW) {
        if (title.includes(kw)) return 'indoor';
    }
    return 'indoor';
}

function openScheduleModal(scheduleId = null, defaultDate = null) {
    editingScheduleId = scheduleId;
    const modal = document.getElementById('schedule-modal');
    const form = document.getElementById('schedule-form');
    const title = document.getElementById('modal-title');

    form.reset();

    if (scheduleId) {
        title.textContent = '📝 일정 수정';
        for (const dateKey in scheduleData) {
            const found = scheduleData[dateKey].find(s => s.id === scheduleId);
            if (found) {
                document.getElementById('input-title').value = found.title;
                document.getElementById('input-date').value = found.date;
                document.getElementById('input-time').value = found.time || '';
                document.querySelector(`input[name="category"][value="${found.category}"]`).checked = true;
                document.getElementById('input-memo').value = found.memo || '';
                break;
            }
        }
    } else {
        title.textContent = '📝 일정 추가';
        if (defaultDate) {
            document.getElementById('input-date').value = defaultDate;
        }
    }

    modal.classList.remove('hidden');
}

function editSchedule(id) {
    openScheduleModal(id);
}

document.addEventListener('DOMContentLoaded', () => {
    const modal = document.getElementById('schedule-modal');
    const form = document.getElementById('schedule-form');
    const titleInput = document.getElementById('input-title');

    titleInput.addEventListener('input', (e) => {
        const category = classifyTitle(e.target.value);
        document.querySelector(`input[name="category"][value="${category}"]`).checked = true;
    });

    document.getElementById('close-modal').addEventListener('click', () => {
        modal.classList.add('hidden');
    });
    document.getElementById('cancel-btn').addEventListener('click', () => {
        modal.classList.add('hidden');
    });

    document.getElementById('add-schedule-btn').addEventListener('click', () => {
        openScheduleModal();
    });

    form.addEventListener('submit', async (e) => {
        e.preventDefault();

        const data = {
            title: document.getElementById('input-title').value.trim(),
            date: document.getElementById('input-date').value,
            time: document.getElementById('input-time').value || null,
            category: document.querySelector('input[name="category"]:checked').value,
            memo: document.getElementById('input-memo').value.trim() || null
        };

        if (!data.title) {
            alert('일정 제목을 입력해주세요');
            return;
        }

        try {
            if (editingScheduleId) {
                await api.updateSchedule(editingScheduleId, data);
            } else {
                await api.createSchedule(data);
            }

            modal.classList.add('hidden');
            await renderCalendar();

            if (currentBriefingDate) {
                await openBriefing(currentBriefingDate);
            }
        } catch (e) {
            alert(e.message);
        }
    });
});
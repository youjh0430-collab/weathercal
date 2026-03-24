/**
 * Role: Service Worker — PWA 오프라인 캐싱 + 앱 설치 지원
 * Key Features: 정적 파일 캐싱, 네트워크 우선 전략
 */

const CACHE_NAME = 'weathercal-v1';
const STATIC_ASSETS = [
    '/',
    '/css/style.css',
    '/js/api.js',
    '/js/calendar.js',
    '/js/briefing.js',
    '/js/schedule.js',
    '/manifest.json'
];

// 설치 — 정적 파일 캐싱
self.addEventListener('install', (event) => {
    event.waitUntil(
        caches.open(CACHE_NAME).then((cache) => cache.addAll(STATIC_ASSETS))
    );
    self.skipWaiting();
});

// 활성화 — 이전 캐시 삭제
self.addEventListener('activate', (event) => {
    event.waitUntil(
        caches.keys().then((keys) =>
            Promise.all(keys.filter((k) => k !== CACHE_NAME).map((k) => caches.delete(k)))
        )
    );
    self.clients.claim();
});

// 요청 처리 — API는 네트워크 우선, 정적 파일은 캐시 우선
self.addEventListener('fetch', (event) => {
    const url = new URL(event.request.url);

    // API 요청은 항상 네트워크 우선
    if (url.pathname.startsWith('/api/')) {
        event.respondWith(
            fetch(event.request).catch(() => caches.match(event.request))
        );
        return;
    }

    // 정적 파일은 캐시 우선, 없으면 네트워크
    event.respondWith(
        caches.match(event.request).then((cached) => cached || fetch(event.request))
    );
});

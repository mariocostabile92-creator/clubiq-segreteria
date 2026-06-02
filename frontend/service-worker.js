/*
  ClubIQ Segreteria - Service Worker
  V1.1
  Static cache + network-first API safe strategy
*/

const CACHE_NAME = "clubiq-segreteria-v1-1";

const APP_ASSETS = [
    "/",
    "/index.html",
    "/dashboard.html",
    "/css/base.css",
    "/css/layout.css",
    "/css/components.css",
    "/css/dashboard.css",
    "/css/mobile.css",
    "/js/api.js",
    "/js/auth.js",
    "/js/dashboard.js",
    "/js/pwa.js",
    "/manifest.json"
];

self.addEventListener("install", event => {
    self.skipWaiting();

    event.waitUntil(
        caches.open(CACHE_NAME).then(cache => cache.addAll(APP_ASSETS))
    );
});

self.addEventListener("activate", event => {
    event.waitUntil(
        caches.keys().then(keys => {
            return Promise.all(
                keys
                    .filter(key => key !== CACHE_NAME)
                    .map(key => caches.delete(key))
            );
        }).then(() => self.clients.claim())
    );
});

self.addEventListener("fetch", event => {
    const request = event.request;
    const url = new URL(request.url);

    if(request.method !== "GET"){
        return;
    }

    // Non cacheare le API del backend: devono sempre essere dati freschi.
    if(url.origin === "http://127.0.0.1:8000" || url.origin === "http://localhost:8000"){
        event.respondWith(fetch(request));
        return;
    }

    // HTML: prova rete, fallback cache.
    if(request.headers.get("accept")?.includes("text/html")){
        event.respondWith(
            fetch(request)
                .then(response => {
                    const copy = response.clone();
                    caches.open(CACHE_NAME).then(cache => cache.put(request, copy));
                    return response;
                })
                .catch(() => caches.match(request).then(cached => cached || caches.match("/index.html")))
        );
        return;
    }

    // Asset statici: cache first.
    event.respondWith(
        caches.match(request).then(cached => {
            if(cached) return cached;

            return fetch(request).then(response => {
                const copy = response.clone();
                caches.open(CACHE_NAME).then(cache => cache.put(request, copy));
                return response;
            });
        })
    );
});
import { version } from '$app/env';
import { assets, immutable } from '$app/manifest';
import { asset } from '$app/paths';
import { self } from '$app/service-worker';

const CACHE = `devflow-${version}`;
const ASSETS = ['/', ...immutable.map((item) => item.path), ...assets.map((item) => asset(item.path))];
const OFFLINE_URL = '/';

self.addEventListener('install', (event) => {
	event.waitUntil(
		caches.open(CACHE).then((cache) => cache.addAll(ASSETS)).then(() => self.skipWaiting())
	);
});

self.addEventListener('activate', (event) => {
	event.waitUntil(
		caches
			.keys()
			.then((keys) => Promise.all(keys.filter((key) => key !== CACHE).map((key) => caches.delete(key))))
			.then(() => self.clients.claim())
	);
});

self.addEventListener('fetch', (event) => {
	const { request } = event;
	if (request.method !== 'GET') return;

	const url = new URL(request.url);
	if (url.origin !== self.location.origin) return;
	// Never cache API traffic: developer memory must always be fresh.
	if (url.pathname.startsWith('/api/')) return;

	if (request.mode === 'navigate') {
		event.respondWith(
			fetch(request).catch(() => caches.match(OFFLINE_URL).then((response) => response ?? Response.error()))
		);
		return;
	}

	if (ASSETS.includes(url.pathname)) {
		event.respondWith(caches.match(request).then((cached) => cached ?? fetch(request)));
	}
});

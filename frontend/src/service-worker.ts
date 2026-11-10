import { version } from '$app/env';
import { assets, immutable } from '$app/manifest';
import { asset } from '$app/paths';
import { self } from '$app/service-worker';

const CACHE = `devflow-${version}`;
const RUNTIME = `${CACHE}-runtime`;
const APP_SHELL = '/';
const ASSETS = [
	APP_SHELL,
	...immutable.map((item) => item.path),
	...assets.map((item) => asset(item.path))
];

self.addEventListener('install', (event) => {
	event.waitUntil(
		caches
			.open(CACHE)
			.then((cache) => cache.addAll(ASSETS))
			.then(() => self.skipWaiting())
	);
});

self.addEventListener('activate', (event) => {
	event.waitUntil(
		caches
			.keys()
			.then((keys) =>
				Promise.all(
					keys
						.filter((key) => key !== CACHE && key !== RUNTIME)
						.map((key) => caches.delete(key))
				)
			)
			.then(() => self.clients.claim())
	);
});

self.addEventListener('fetch', (event) => {
	const { request } = event;
	if (request.method !== 'GET') return;

	const url = new URL(request.url);
	if (url.origin !== self.location.origin) return;

	// Developer memory is private and always fresh: never cache API traffic.
	if (url.pathname.startsWith('/api/')) return;

	// Navigations: network first, then the cached app shell for offline starts.
	if (request.mode === 'navigate') {
		event.respondWith(
			fetch(request)
				.then((response) => {
					const copy = response.clone();
					caches.open(RUNTIME).then((cache) => cache.put(request, copy));
					return response;
				})
				.catch(async () => {
					return (
						(await caches.match(request)) ??
						(await caches.match(APP_SHELL)) ??
						Response.error()
					);
				})
		);
		return;
	}

	// Hashed build output and static assets: cache first, refresh in background.
	if (ASSETS.includes(url.pathname) || url.pathname.startsWith('/_app/')) {
		event.respondWith(
			caches.match(request).then((cached) => {
				const network = fetch(request)
					.then((response) => {
						if (response.ok) {
							const copy = response.clone();
							caches.open(CACHE).then((cache) => cache.put(request, copy));
						}
						return response;
					})
					.catch(() => cached ?? Response.error());
				return cached ?? network;
			})
		);
	}
});

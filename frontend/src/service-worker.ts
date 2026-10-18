import { version } from '$app/env';
import { assets, immutable } from '$app/manifest';
import { asset, resolve } from '$app/paths';

const CACHE = `omnisapiens-${version}`;
const SHELL = resolve('/');
/** El build, `static/` y el shell; el juego igual necesita red para hablar con la API. */
const FILES = [
	...immutable.map(({ path }) => asset(path)),
	...assets.map(({ path }) => asset(path)),
	SHELL
];

const sw = self as unknown as ServiceWorkerGlobalScope;

sw.addEventListener('install', (event) => {
	event.waitUntil(
		(async () => {
			const cache = await caches.open(CACHE);
			await cache.addAll(FILES);
			await sw.skipWaiting();
		})()
	);
});

sw.addEventListener('activate', (event) => {
	event.waitUntil(
		(async () => {
			const keys = await caches.keys();
			await Promise.all(keys.filter((key) => key !== CACHE).map((key) => caches.delete(key)));
			await sw.clients.claim();
		})()
	);
});

sw.addEventListener('fetch', (event) => {
	const request = event.request;
	if (request.method !== 'GET') return;

	const url = new URL(request.url);
	if (url.origin !== sw.location.origin) return;

	// Navegar siempre busca la versión viva; sin red queda el app shell.
	if (request.mode === 'navigate') {
		event.respondWith(
			(async () => {
				try {
					return await fetch(request);
				} catch {
					return (await caches.match(SHELL)) ?? Response.error();
				}
			})()
		);
		return;
	}

	if (FILES.includes(url.pathname)) {
		event.respondWith((async () => (await caches.match(request)) ?? fetch(request))());
	}
});

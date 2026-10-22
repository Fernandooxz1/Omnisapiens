<script lang="ts">
	import { onMount } from 'svelte';
	import { page } from '$app/state';
	import '../app.css';
	import ConnectionBanner from '#lib/components/ConnectionBanner.svelte';
	import TabBar from '#lib/components/TabBar.svelte';
	import Toast from '#lib/components/Toast.svelte';
	import { t } from '#lib/i18n';
	import { unlockSound } from '#lib/sound.svelte';
	import type { LayoutProps } from './$types';

	let { children }: LayoutProps = $props();

	const path = $derived(page.url.pathname.replace(/\/+$/, '') || '/');
	const segments = $derived(path.split('/').filter(Boolean));
	const inGames = $derived(segments[0] === 'juegos');
	/** Hub y catálogo comparten el ancho ancho; la partida usa el suyo. */
	const gameCatalog = $derived(inGames && segments.length <= 2);
	const gameCase = $derived(inGames && segments.length > 2);
	const showTabBar = $derived(path === '/' || path === '/ranking' || gameCatalog);

	onMount(() => {
		if (import.meta.env.PROD && 'serviceWorker' in navigator) {
			navigator.serviceWorker.register('/service-worker.js').catch(() => {
				/* sin service worker la app sigue funcionando, solo no se instala */
			});
		}
	});
</script>

<svelte:head>
	<title>{t('app.title')}</title>
	<meta name="description" content={t('app.description')} />
</svelte:head>

<svelte:window onpointerdown={unlockSound} onkeydown={unlockSound} />

<main
	class="shell"
	class:shell--wide={gameCatalog}
	class:shell--play={gameCase}
	class:shell--tabbar={showTabBar}
>
	{@render children()}
</main>

{#if showTabBar}<TabBar />{/if}
<ConnectionBanner />
<Toast />

<script lang="ts">
	import { onMount } from 'svelte';
	import '../app.css';
	import ConnectionBanner from '#lib/components/ConnectionBanner.svelte';
	import Toast from '#lib/components/Toast.svelte';
	import { t } from '#lib/i18n';
	import { unlockSound } from '#lib/sound.svelte';
	import type { LayoutProps } from './$types';

	let { children }: LayoutProps = $props();

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

<main class="shell">
	{@render children()}
</main>

<ConnectionBanner />
<Toast />

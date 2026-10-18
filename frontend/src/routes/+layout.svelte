<script lang="ts">
	import '../app.css';
	import { t } from '#lib/i18n';
	import type { LayoutProps } from './$types';

	let { children }: LayoutProps = $props();
</script>

<svelte:head>
	<title>{t('app.title')}</title>
	<meta name="description" content={t('app.description')} />
</svelte:head>

<main class="shell">
	{@render children()}
</main>

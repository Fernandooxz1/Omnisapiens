<script lang="ts">
	import { goto } from '$app/navigation';
	import { page } from '$app/state';
	import Button from '#lib/components/Button.svelte';
	import { t } from '#lib/i18n';

	const missing = $derived(page.status === 404);
	const title = $derived(missing ? t('error.not_found') : t('error.title'));
	const hint = $derived(missing ? t('error.not_found_hint') : t('error.hint'));
</script>

<svelte:head>
	<title>{title} · {t('app.title')}</title>
</svelte:head>

<section class="failure">
	<span class="failure__status">{page.status}</span>
	<h1 class="page-title">{title}</h1>
	<p class="muted">{hint}</p>
	<Button variant="slate" title={t('common.back')} onclick={() => goto('/')} />
</section>

<style>
	.failure {
		display: flex;
		flex: 1;
		flex-direction: column;
		align-items: center;
		justify-content: center;
		gap: var(--s-3);
		text-align: center;
	}

	.failure__status {
		padding: 3px 10px;
		border-radius: var(--r-full);
		background: var(--well-bg);
		box-shadow: inset 0 3px 0 rgb(0 0 0 / 0.4);
		color: var(--red-ink);
		font-family: var(--font-display);
		font-size: 0.8rem;
		font-weight: 700;
		letter-spacing: 0.1em;
	}
</style>

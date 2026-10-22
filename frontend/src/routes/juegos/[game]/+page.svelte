<script lang="ts">
	import { page } from '$app/state';
	import Icon from '#lib/components/Icon.svelte';
	import { findGame } from '#lib/games/catalog';
	import { t } from '#lib/i18n';

	const game = $derived(findGame(page.params.game ?? ''));
</script>

<svelte:head>
	<title>{game ? t(game.titleKey) : t('games.unknown_title')} · {t('app.title')}</title>
</svelte:head>

<section class="catalog">
	<a class="catalog__back" href="/juegos">
		<span class="catalog__back-icon"><Icon name="arrow" size={18} /></span>
		{t('games.back_hub')}
	</a>

	<header class="catalog__head">
		{#if game}
			<span class="catalog__icon"><Icon name={game.icon} size={30} /></span>
		{/if}
		<h1 class="page-title">{game ? t(game.titleKey) : t('games.unknown_title')}</h1>
		<p class="catalog__hint">
			{game ? t(game.blurbKey) : t('games.unknown_hint')}
		</p>
	</header>

	{#if game}
		<div class="catalog__soon">
			<h2 class="catalog__soon-title">{t('games.catalog_soon')}</h2>
			<p class="catalog__soon-hint">{t('games.catalog_soon_hint')}</p>
		</div>
	{/if}
</section>

<style>
	.catalog {
		display: flex;
		flex: 1;
		flex-direction: column;
		gap: var(--s-5);
	}

	.catalog__back {
		display: inline-flex;
		align-self: flex-start;
		align-items: center;
		gap: var(--s-2);
		min-height: 44px;
		color: var(--ink-3);
		font-size: 0.9rem;
		font-weight: 700;
		text-decoration: none;
	}

	.catalog__back:hover {
		color: var(--ink);
	}

	.catalog__back-icon {
		display: inline-flex;
		transform: rotate(180deg);
	}

	.catalog__head {
		display: flex;
		flex-direction: column;
		gap: var(--s-2);
	}

	.catalog__icon {
		display: inline-flex;
		color: var(--accent);
	}

	.catalog__hint {
		max-width: 46ch;
		color: var(--ink-3);
	}

	.catalog__soon {
		display: flex;
		flex-direction: column;
		gap: var(--s-2);
		padding: var(--s-5);
		border-radius: var(--r-lg);
		background: var(--well-bg);
		box-shadow: inset 0 4px 0 rgb(0 0 0 / 0.35);
	}

	.catalog__soon-title {
		font-family: var(--font-display);
		font-size: 1.15rem;
	}

	.catalog__soon-hint {
		color: var(--ink-3);
		font-size: 0.92rem;
	}
</style>

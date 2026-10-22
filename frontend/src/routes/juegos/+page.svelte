<script lang="ts">
	import GameCard from '#lib/games/components/GameCard.svelte';
	import { games, orderGames } from '#lib/games/catalog';
	import { countSolved } from '#lib/games/progress.svelte';
	import { t } from '#lib/i18n';

	const catalog = orderGames(games);
</script>

<svelte:head>
	<title>{t('games.title')} · {t('app.title')}</title>
</svelte:head>

<section class="hub">
	<header class="hub__intro">
		<h1 class="page-title">{t('games.title')}</h1>
		<p class="hub__hint">{t('games.hint')}</p>
	</header>

	{#if catalog.length > 0}
		<ul class="hub__grid">
			{#each catalog as game (game.id)}
				<li>
					<GameCard {game} solved={countSolved(game.id)} total={game.caseCount} />
				</li>
			{/each}
		</ul>
	{:else}
		<p class="hub__empty">{t('games.empty')}</p>
	{/if}
</section>

<style>
	.hub {
		display: flex;
		flex: 1;
		flex-direction: column;
		gap: var(--s-5);
	}

	.hub__intro {
		display: flex;
		flex-direction: column;
		gap: var(--s-2);
	}

	.hub__hint {
		max-width: 46ch;
		color: var(--ink-3);
	}

	.hub__grid {
		display: grid;
		grid-template-columns: repeat(auto-fill, minmax(260px, 320px));
		gap: var(--s-4);
		margin: 0;
		padding: 0;
		list-style: none;
	}

	.hub__empty {
		color: var(--ink-3);
	}
</style>

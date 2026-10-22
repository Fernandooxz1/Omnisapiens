<script lang="ts">
	import Icon from '#lib/components/Icon.svelte';
	import { games, orderGames } from '#lib/games/catalog';
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
					<a class="game-card game-card--{game.accent}" href={game.route}>
						<span class="game-card__icon"><Icon name={game.icon} size={28} /></span>
						<span class="game-card__body">
							<span class="game-card__title">{t(game.titleKey)}</span>
							<span class="game-card__blurb">{t(game.blurbKey)}</span>
							<span class="game-card__meta">
								{t('games.case_count', { n: game.caseCount })}
							</span>
						</span>
						<span class="game-card__go"><Icon name="arrow" size={18} /></span>
					</a>
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

	.game-card {
		--game-accent: var(--accent);
		display: flex;
		align-items: flex-start;
		gap: var(--s-3);
		height: 100%;
		padding: var(--s-4);
		border-radius: var(--r-lg);
		background: var(--panel-bg);
		box-shadow: 0 6px 0 var(--panel-edge);
		color: var(--ink);
		text-decoration: none;
		transition:
			transform 0.07s ease,
			box-shadow 0.07s ease,
			filter 0.15s ease;
	}

	.game-card:hover {
		filter: brightness(1.05);
		transform: translateY(-2px);
		box-shadow: 0 8px 0 var(--panel-edge);
	}

	.game-card:active {
		transform: translateY(3px);
		box-shadow: 0 3px 0 var(--panel-edge);
	}

	.game-card--green {
		--game-accent: var(--green);
	}

	.game-card--blue {
		--game-accent: var(--blue);
	}

	.game-card--yellow {
		--game-accent: var(--yellow);
	}

	.game-card--orange {
		--game-accent: var(--orange);
	}

	.game-card--red {
		--game-accent: var(--red);
	}

	.game-card--purple {
		--game-accent: var(--purple);
	}

	.game-card__icon {
		display: grid;
		flex: none;
		place-items: center;
		width: 56px;
		height: 56px;
		border-radius: var(--r-md);
		background: var(--well-bg);
		box-shadow: inset 0 3px 0 rgb(0 0 0 / 0.4);
		color: var(--game-accent);
	}

	.game-card__body {
		display: flex;
		flex: 1;
		flex-direction: column;
		gap: var(--s-1);
		min-width: 0;
	}

	.game-card__title {
		font-family: var(--font-display);
		font-size: 1.35rem;
		font-weight: 700;
		line-height: 1.1;
	}

	.game-card__blurb {
		color: var(--ink-2);
		font-size: 0.9rem;
		line-height: 1.35;
	}

	.game-card__meta {
		margin-top: var(--s-1);
		color: var(--ink-3);
		font-size: 0.78rem;
		font-weight: 700;
		letter-spacing: 0.04em;
		text-transform: uppercase;
	}

	.game-card__go {
		display: inline-flex;
		flex: none;
		margin-top: var(--s-1);
		color: var(--game-accent);
	}
</style>

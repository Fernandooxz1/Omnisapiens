<script lang="ts">
	import Icon from '#lib/components/Icon.svelte';
	import { t } from '#lib/i18n';
	import type { GameMeta } from '../types';

	interface Props {
		game: GameMeta;
		solved: number;
		total: number;
	}

	let { game, solved, total }: Props = $props();

	const percent = $derived(total > 0 ? Math.round((solved / total) * 100) : 0);
</script>

<a class="card card--{game.accent}" href={game.route}>
	<span class="card__icon"><Icon name={game.icon} size={28} /></span>

	<span class="card__body">
		<span class="card__title">{t(game.titleKey)}</span>
		<span class="card__blurb">{t(game.blurbKey)}</span>
		<span class="card__meta">{t('games.case_count', { n: total })}</span>

		<span class="card__progress">
			<span class="card__bar" aria-hidden="true">
				<span class="card__fill" style:width="{percent}%"></span>
			</span>
			<span class="card__solved">{t('games.progress_summary', { solved, total })}</span>
		</span>
	</span>

	<span class="card__go"><Icon name="arrow" size={18} /></span>
</a>

<style>
	.card {
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

	.card:hover {
		filter: brightness(1.05);
		transform: translateY(-2px);
		box-shadow: 0 8px 0 var(--panel-edge);
	}

	.card:active {
		transform: translateY(3px);
		box-shadow: 0 3px 0 var(--panel-edge);
	}

	.card--green {
		--game-accent: var(--green);
	}

	.card--blue {
		--game-accent: var(--blue);
	}

	.card--yellow {
		--game-accent: var(--yellow);
	}

	.card--orange {
		--game-accent: var(--orange);
	}

	.card--red {
		--game-accent: var(--red);
	}

	.card--purple {
		--game-accent: var(--purple);
	}

	.card__icon {
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

	.card__body {
		display: flex;
		flex: 1;
		flex-direction: column;
		gap: var(--s-1);
		min-width: 0;
	}

	.card__title {
		font-family: var(--font-display);
		font-size: 1.35rem;
		font-weight: 700;
		line-height: 1.1;
	}

	.card__blurb {
		color: var(--ink-2);
		font-size: 0.9rem;
		line-height: 1.35;
	}

	.card__meta {
		margin-top: var(--s-1);
		color: var(--ink-3);
		font-size: 0.78rem;
		font-weight: 700;
		letter-spacing: 0.04em;
		text-transform: uppercase;
	}

	.card__progress {
		display: flex;
		flex-direction: column;
		align-items: flex-start;
		gap: 3px;
		margin-top: var(--s-1);
	}

	.card__bar {
		width: 100%;
		height: 8px;
		border-radius: var(--r-full);
		background: var(--well-bg);
		box-shadow: inset 0 2px 0 rgb(0 0 0 / 0.4);
		overflow: hidden;
	}

	.card__fill {
		display: block;
		height: 100%;
		border-radius: var(--r-full);
		background: var(--game-accent);
	}

	.card__solved {
		flex: none;
		color: var(--ink-3);
		font-size: 0.75rem;
		font-weight: 600;
		white-space: nowrap;
	}

	.card__go {
		display: inline-flex;
		flex: none;
		margin-top: var(--s-1);
		color: var(--game-accent);
	}
</style>

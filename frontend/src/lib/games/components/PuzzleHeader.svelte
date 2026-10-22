<script lang="ts">
	import type { Snippet } from 'svelte';
	import Icon from '#lib/components/Icon.svelte';
	import { t } from '#lib/i18n';
	import { DIFFICULTY_LABEL } from '../difficulty';
	import type { DifficultyKey } from '../types';

	interface Props {
		href: string;
		/** Texto ya traducido: la partida vuelve al catálogo, no al inicio. */
		backLabel: string;
		title: string;
		difficulty: DifficultyKey;
		/** El cronómetro lo dibuja la pantalla de partida. */
		timer?: Snippet;
	}

	let { href, backLabel, title, difficulty, timer }: Props = $props();
</script>

<header class="puzzle-head">
	<div class="puzzle-head__top">
		<a class="puzzle-head__back" {href}>
			<span class="puzzle-head__arrow"><Icon name="arrow" size={18} /></span>
			{backLabel}
		</a>

		{#if timer}
			<div class="puzzle-head__timer">{@render timer()}</div>
		{/if}
	</div>

	<div class="puzzle-head__title-row">
		<span class="puzzle-head__icon" aria-hidden="true"><Icon name="case" size={22} /></span>
		<h1 class="puzzle-head__title">{title}</h1>
		<span class="puzzle-head__difficulty" data-difficulty={difficulty}>
			{t(DIFFICULTY_LABEL[difficulty])}
		</span>
	</div>
</header>

<style>
	.puzzle-head {
		display: flex;
		flex-direction: column;
		gap: var(--s-3);
	}

	.puzzle-head__top {
		display: flex;
		align-items: center;
		justify-content: space-between;
		gap: var(--s-3);
		min-height: 44px;
	}

	.puzzle-head__back {
		display: inline-flex;
		align-items: center;
		gap: var(--s-2);
		min-height: 44px;
		color: var(--ink-3);
		font-size: 0.9rem;
		font-weight: 700;
		text-decoration: none;
	}

	.puzzle-head__back:hover {
		color: var(--ink);
	}

	.puzzle-head__arrow {
		display: inline-flex;
		transform: rotate(180deg);
	}

	.puzzle-head__timer {
		display: inline-flex;
	}

	.puzzle-head__title-row {
		display: flex;
		flex-wrap: wrap;
		align-items: center;
		gap: var(--s-2);
	}

	.puzzle-head__icon {
		display: inline-flex;
		color: var(--ink-3);
	}

	.puzzle-head__title {
		font-size: clamp(1.6rem, 6vw, 2.35rem);
		color: var(--ink);
		text-shadow: 0 4px 0 var(--card-edge);
	}

	.puzzle-head__difficulty {
		align-self: center;
		padding: 4px 12px;
		border-radius: var(--r-full);
		background: var(--diff, var(--panel-bg));
		box-shadow: 0 3px 0 var(--diff-edge, var(--panel-edge));
		color: var(--diff-ink, var(--ink));
		font-family: var(--font-ui);
		font-size: 0.72rem;
		font-weight: 800;
		letter-spacing: 0.05em;
		text-transform: uppercase;
	}
</style>

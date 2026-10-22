<script lang="ts">
	import { t } from '#lib/i18n';
	import { DIFFICULTIES, DIFFICULTY_LABEL, type DifficultyFilter } from '../difficulty';
	import type { DifficultyKey } from '../types';

	interface Props {
		counts: Record<DifficultyKey, number>;
		total: number;
		selected: DifficultyFilter;
		onselect: (value: DifficultyFilter) => void;
	}

	let { counts, total, selected, onselect }: Props = $props();
</script>

<div class="chips" role="group" aria-label={t('games.filter_label')}>
	<button
		type="button"
		class="chip"
		class:is-active={selected === 'all'}
		aria-pressed={selected === 'all'}
		onclick={() => onselect('all')}
	>
		<span class="chip__label">{t('games.filter_all')}</span>
		<span class="chip__count">{total}</span>
	</button>

	{#each DIFFICULTIES as difficulty (difficulty)}
		<button
			type="button"
			class="chip"
			class:is-active={selected === difficulty}
			aria-pressed={selected === difficulty}
			data-difficulty={difficulty}
			disabled={counts[difficulty] === 0}
			onclick={() => onselect(difficulty)}
		>
			<span class="chip__dot" aria-hidden="true"></span>
			<span class="chip__label">{t(DIFFICULTY_LABEL[difficulty])}</span>
			<span class="chip__count">{counts[difficulty]}</span>
		</button>
	{/each}
</div>

<style>
	.chips {
		display: flex;
		gap: var(--s-2);
		padding-bottom: var(--s-1);
		overflow-x: auto;
		scrollbar-width: none;
	}

	.chips::-webkit-scrollbar {
		display: none;
	}

	.chip {
		display: inline-flex;
		flex: none;
		align-items: center;
		gap: var(--s-2);
		min-height: 44px;
		padding: 0 var(--s-3);
		border: 0;
		border-radius: var(--r-full);
		background: var(--panel-bg);
		box-shadow: 0 3px 0 var(--panel-edge);
		color: var(--ink-2);
		font-family: var(--font-ui);
		font-size: 0.82rem;
		font-weight: 700;
		cursor: pointer;
		transition:
			background 0.1s ease,
			color 0.1s ease,
			box-shadow 0.1s ease;
	}

	.chip:hover:not(:disabled) {
		color: var(--ink);
		filter: brightness(1.06);
	}

	.chip:disabled {
		cursor: not-allowed;
		opacity: 0.45;
	}

	.chip.is-active {
		background: var(--well-bg);
		box-shadow:
			inset 0 0 0 2px var(--accent),
			0 3px 0 var(--panel-edge);
		color: var(--ink);
	}

	.chip__dot {
		width: 9px;
		height: 9px;
		border-radius: 50%;
		background: var(--diff, var(--ink-3));
		box-shadow: 0 1.5px 0 var(--diff-edge, transparent);
	}

	.chip__count {
		display: inline-grid;
		place-items: center;
		min-width: 22px;
		height: 22px;
		padding: 0 6px;
		border-radius: var(--r-full);
		background: rgb(0 0 0 / 0.25);
		font-size: 0.72rem;
		font-variant-numeric: tabular-nums;
	}

	.chip__label {
		white-space: nowrap;
	}
</style>

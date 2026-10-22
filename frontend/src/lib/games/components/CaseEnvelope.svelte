<script lang="ts">
	import { t, type MessageKey } from '#lib/i18n';
	import { DIFFICULTY_LABEL } from '../difficulty';
	import { getCaseProgress } from '../progress.svelte';
	import type { CasePreview } from '../types';

	interface Props {
		preview: CasePreview;
		href: string;
	}

	let { preview, href }: Props = $props();

	type EnvelopeState = 'new' | 'in_progress' | 'continue' | 'solved';

	const STATE_LABEL: Record<EnvelopeState, MessageKey> = {
		new: 'games.state.new',
		in_progress: 'games.state.in_progress',
		continue: 'games.state.continue',
		solved: 'games.state.solved'
	};

	/** La mini-vista no puede revelar sospechosos: solo regiones y víctima. */
	const MINI = 5;

	const meta = $derived(preview.meta);
	const progress = $derived(getCaseProgress(meta.id));
	const state = $derived<EnvelopeState>(
		progress?.solved
			? 'solved'
			: progress?.resume
				? 'continue'
				: progress?.lastPlayedAt
					? 'in_progress'
					: 'new'
	);

	const difficulty = $derived(t(DIFFICULTY_LABEL[meta.difficulty]));
	const sizeLabel = $derived(`${meta.size}×${meta.size}`);
	const stateLabel = $derived(t(STATE_LABEL[state]));

	const bestTime = $derived(
		progress?.solved && progress.bestMs !== null ? formatMs(progress.bestMs) : null
	);

	const label = $derived(
		t('games.case_label', {
			n: meta.number,
			title: meta.title,
			difficulty,
			size: sizeLabel,
			state: stateLabel
		})
	);

	const mini = $derived.by(() => {
		const cells: { tone: number; victim: boolean }[] = [];
		const step = meta.size / MINI;
		const victimRow = Math.floor((preview.victim.row * MINI) / meta.size);
		const victimCol = Math.floor((preview.victim.col * MINI) / meta.size);

		for (let row = 0; row < MINI; row += 1) {
			for (let col = 0; col < MINI; col += 1) {
				const sourceRow = Math.min(meta.size - 1, Math.floor((row + 0.5) * step));
				const sourceCol = Math.min(meta.size - 1, Math.floor((col + 0.5) * step));

				cells.push({
					tone: preview.regions[sourceRow][sourceCol] % 6,
					victim: row === victimRow && col === victimCol
				});
			}
		}

		return cells;
	});

	function formatMs(ms: number): string {
		const seconds = Math.max(0, Math.round(ms / 1000));
		return `${Math.floor(seconds / 60)}:${String(seconds % 60).padStart(2, '0')}`;
	}
</script>

<a class="envelope" {href} aria-label={label}>
	<span class="envelope__flap" aria-hidden="true">
		<svg viewBox="0 0 100 40" preserveAspectRatio="none">
			<path d="M0 0h100L50 40Z" vector-effect="non-scaling-stroke" />
		</svg>
	</span>

	<span class="envelope__seal" data-difficulty={meta.difficulty} aria-hidden="true">
		{meta.number}
	</span>

	<span class="envelope__preview" aria-hidden="true">
		{#each mini as cell, index (index)}
			<span
				class="mini__cell mini__cell--{cell.tone}"
				class:mini__cell--victim={cell.victim}
			></span>
		{/each}
	</span>

	<span class="envelope__label">
		<span class="envelope__title">{meta.title}</span>
		<span class="envelope__meta">{difficulty} · {sizeLabel}</span>
		<span class="envelope__state" class:is-solved={state === 'solved'} class:is-continue={state === 'continue'}>
			<span class="envelope__state-text">{stateLabel}</span>
			{#if bestTime}
				<span class="envelope__best">{t('games.best_time', { time: bestTime })}</span>
			{/if}
		</span>
	</span>
</a>

<style>
	.envelope {
		position: relative;
		display: flex;
		flex-direction: column;
		gap: var(--s-3);
		height: 100%;
		padding: 36px var(--s-4) var(--s-4);
		border-radius: var(--r-lg);
		background: var(--panel-bg);
		box-shadow: 0 6px 0 var(--panel-edge);
		color: var(--ink);
		text-decoration: none;
		transition:
			transform 0.1s ease,
			box-shadow 0.1s ease,
			filter 0.15s ease;
	}

	.envelope:hover,
	.envelope:focus-visible {
		filter: brightness(1.04);
		transform: translateY(-2px);
		box-shadow: 0 8px 0 var(--panel-edge);
	}

	.envelope:active {
		transform: translateY(2px);
		box-shadow: 0 4px 0 var(--panel-edge);
	}

	.envelope__flap {
		position: absolute;
		inset: 0 0 auto;
		height: 40px;
		border-radius: var(--r-lg) var(--r-lg) 0 0;
		overflow: hidden;
	}

	.envelope__flap svg {
		display: block;
		width: 100%;
		height: 100%;
	}

	.envelope__flap path {
		fill: color-mix(in srgb, var(--panel-bg) 55%, var(--panel-edge));
		stroke: var(--panel-edge);
		stroke-width: 2.5px;
		stroke-linejoin: round;
	}

	.envelope__seal {
		position: absolute;
		top: 26px;
		right: var(--s-3);
		display: grid;
		place-items: center;
		width: 38px;
		height: 38px;
		border-radius: 50%;
		background: var(--diff);
		box-shadow: 0 3px 0 var(--diff-edge);
		color: var(--diff-ink);
		font-family: var(--font-display);
		font-size: 0.95rem;
		font-weight: 700;
		transform: rotate(-6deg);
		transition: transform 0.18s ease;
	}

	.envelope:hover .envelope__seal,
	.envelope:focus-visible .envelope__seal {
		transform: rotate(0deg);
	}

	.envelope__preview {
		display: grid;
		grid-template-columns: repeat(5, 1fr);
		gap: 2px;
		width: 72px;
		padding: 4px;
		border-radius: var(--r-sm);
		aspect-ratio: 1;
		background: var(--well-bg);
		box-shadow: inset 0 2px 0 rgb(0 0 0 / 0.35);
	}

	.mini__cell {
		position: relative;
		border: 1.5px solid color-mix(in srgb, var(--cell-tone) 62%, var(--well-bg));
		border-radius: 2px;
		background: color-mix(in srgb, var(--cell-tone) 14%, transparent);
	}

	.mini__cell--0 {
		--cell-tone: var(--blue);
	}

	.mini__cell--1 {
		--cell-tone: var(--green);
	}

	.mini__cell--2 {
		--cell-tone: var(--yellow);
	}

	.mini__cell--3 {
		--cell-tone: var(--orange);
	}

	.mini__cell--4 {
		--cell-tone: var(--pink);
	}

	.mini__cell--5 {
		--cell-tone: var(--purple);
	}

	.mini__cell--victim::after {
		content: '';
		position: absolute;
		inset: 26%;
		border-radius: 50%;
		background: var(--red);
		box-shadow: 0 0 0 1.5px var(--well-bg);
	}

	.envelope__label {
		display: flex;
		flex: 1;
		flex-direction: column;
		gap: 3px;
		min-width: 0;
	}

	.envelope__title {
		font-family: var(--font-display);
		font-size: 1.05rem;
		font-weight: 700;
		line-height: 1.15;
	}

	.envelope__meta {
		color: var(--ink-3);
		font-size: 0.72rem;
		font-weight: 700;
		letter-spacing: 0.05em;
		text-transform: uppercase;
	}

	.envelope__state {
		display: flex;
		flex-wrap: wrap;
		align-items: center;
		gap: var(--s-2);
		margin-top: auto;
		padding-top: var(--s-2);
		color: var(--ink-2);
		font-size: 0.78rem;
		font-weight: 600;
	}

	.envelope__state.is-solved {
		color: var(--green);
	}

	.envelope__state.is-continue {
		color: var(--accent);
	}

	.envelope__best {
		color: var(--ink-3);
		font-size: 0.72rem;
		font-weight: 500;
	}
</style>

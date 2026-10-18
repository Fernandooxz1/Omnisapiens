<script lang="ts">
	import { onMount } from 'svelte';
	import { goto } from '$app/navigation';
	import { NETWORK_ERROR } from '#lib/api/client';
	import type { ApiError } from '#lib/api/client';
	import { session } from '#lib/api/session.svelte';
	import type { ArcadeRun } from '#lib/arcade/live.svelte';
	import { createArcadeRun } from '#lib/arcade/live.svelte';
	import AnswerTile, { type TileState } from '#lib/components/AnswerTile.svelte';
	import Button from '#lib/components/Button.svelte';
	import LifeStrip from '#lib/components/LifeStrip.svelte';
	import QuestionCard from '#lib/components/QuestionCard.svelte';
	import TimerBadge from '#lib/components/TimerBadge.svelte';
	import { categoryKey } from '#lib/categories';
	import { t, type MessageKey } from '#lib/i18n';

	let run = $state<ArcadeRun | null>(null);
	let blocked = $state<MessageKey | null>(null);
	let now = $state(Date.now());

	const phase = $derived(run?.phase ?? 'connecting');
	const question = $derived(run?.question ?? null);
	const result = $derived(run?.result ?? null);
	const end = $derived(run?.end ?? null);
	const picked = $derived(run?.picked ?? null);
	const problem = $derived(blocked ?? failureKey(run?.failure ?? null));

	/** Segundos del `ends_at` del servidor: el cliente no calcula tiempo propio. */
	const seconds = $derived(
		question ? Math.max(0, Math.ceil((question.endsAt - now) / 1000)) : 0
	);
	const alert = $derived(phase === 'question' && seconds <= 5);
	const timeLeft = $derived(
		question ? Math.min(100, Math.round((seconds / question.seconds) * 100)) : 0
	);

	onMount(() => {
		let live: ArcadeRun | null = null;

		(async () => {
			await session.restore();

			if (!session.token) {
				blocked = 'arcade.error_auth';
				return;
			}

			live = createArcadeRun(session.token);
			run = live;
		})();

		// Irse de la pantalla abandona la corrida: el servidor la invalida.
		return () => live?.close();
	});

	$effect(() => {
		const id = setInterval(() => (now = Date.now()), 250);
		return () => clearInterval(id);
	});

	function failureKey(error: ApiError | null): MessageKey | null {
		if (!error) return null;
		if (error.code === NETWORK_ERROR) return 'arcade.error_offline';

		switch (error.code) {
			case 'AUTH_REQUIRED':
				return 'arcade.error_auth';
			case 'RATE_LIMITED':
				return 'arcade.error_limited';
			default:
				return 'arcade.error_generic';
		}
	}

	function noticeKey(value: string): MessageKey {
		switch (value) {
			case 'NO_QUESTIONS':
				return 'arcade.error_no_questions';
			case 'RUN_NOT_STARTED':
				return 'arcade.error_start';
			default:
				return 'arcade.error_generic';
		}
	}

	function tileState(index: number): TileState {
		if (phase === 'reveal') {
			if (index === result?.correctIndex) return 'correct';
			if (index === picked) return 'wrong';
			return 'dim';
		}
		if (phase !== 'question' && index === picked) return 'selected';
		return 'idle';
	}

	function delta(points: number): string {
		return t('arcade.points', { n: points });
	}

	function rank(value: number | null): string {
		return value === null ? t('arcade.no_rank') : t('arcade.rank', { n: value });
	}
</script>

{#if problem}
	<section class="arcade arcade--center">
		<h1 class="page-title">{t('arcade.title')}</h1>
		<p class="muted">{t(problem)}</p>
		<Button variant="slate" title={t('common.back')} onclick={() => goto('/')} />
	</section>
{:else if phase === 'over' && end}
	<section class="arcade-end">
		<header class="brand">
			<h1 class="wordmark">
				{t('home.wordmark_omni')}<span class="wordmark__accent">{t('home.wordmark_sapiens')}</span>
			</h1>
		</header>

		<h1 class="page-title">{t('arcade.end_title')}</h1>

		<div class="end-score">
			<span class="end-score__label">{t('arcade.end_score')}</span>
			<span class="end-score__value">{end.score}</span>
			{#if end.isNewBest}
				<span class="end-score__best">{t('arcade.end_new_best')}</span>
			{/if}
		</div>

		<dl class="end-stats">
			<div>
				<dt>{t('arcade.end_correct')}</dt>
				<dd>{end.correctCount}</dd>
			</div>
			<div>
				<dt>{t('arcade.end_streak')}</dt>
				<dd>{end.longestStreak}</dd>
			</div>
			<div>
				<dt>{t('arcade.end_difficulty')}</dt>
				<dd>{end.maxDifficulty}</dd>
			</div>
		</dl>

		<div class="end-ranks">
			<div>
				<span>{t('arcade.end_global')}</span>
				<strong>{rank(end.rankGlobal)}</strong>
			</div>
			<div>
				<span>{t('arcade.end_week')}</span>
				<strong>{rank(end.rankWeekly)}</strong>
			</div>
		</div>

		{#if end.personalBest !== null && !end.isNewBest}
			<p class="end-best">{t('arcade.end_best', { n: end.personalBest })}</p>
		{/if}

		<div class="modes">
			<Button variant="green" title={t('arcade.again')} onclick={() => run?.again()} />
			<Button variant="slate" title={t('common.back')} onclick={() => goto('/')} />
		</div>
	</section>
{:else if question && run}
	<section class="arcade">
		<header class="brand">
			<h1 class="wordmark">
				{t('home.wordmark_omni')}<span class="wordmark__accent">{t('home.wordmark_sapiens')}</span>
			</h1>
		</header>

		<div class="hud">
			<div class="stat">
				<span class="stat__label">{t('arcade.score')}</span>
				<span class="stat__value">{run.score}</span>
			</div>
			<div class="stat">
				<span class="stat__label">{t('arcade.streak')}</span>
				<span class="stat__value">x{run.streak}</span>
			</div>
			<LifeStrip lives={run.lives} />
		</div>

		<div class="match__top">
			<span class="arcade__round">{t('arcade.round', { n: question.round + 1 })}</span>
			<TimerBadge {seconds} {alert} idle={phase !== 'question'} />
		</div>

		<div class="time-bar" aria-hidden="true">
			<span
				class="time-bar__fill"
				class:is-warn={seconds <= 8 && seconds > 4}
				class:is-alert={seconds <= 4}
				style="width: {timeLeft}%"
			></span>
		</div>

		<QuestionCard
			category={question.category}
			categoryLabel={t(categoryKey(question.category))}
			prompt={question.prompt}
			badge={phase === 'question' ? t('play.answer_badge') : undefined}
		/>

		<div class="match__tiles">
			{#each question.options as option, index (index)}
				<AnswerTile
					keycap={String(index + 1)}
					label={option}
					state={tileState(index)}
					disabled={phase !== 'question'}
					onclick={() => run?.answer(index)}
				/>
			{/each}
		</div>

		<div class="match__foot" aria-live="polite">
			{#if run.status === 'reconnecting'}
				<p class="muted">{t('play.reconnecting')}</p>
			{:else if run.notice}
				<p class="muted">{t(noticeKey(run.notice))}</p>
			{:else if phase === 'question'}
				<p class="muted">{t('arcade.hint')}</p>
			{:else if phase === 'answered'}
				<p class="muted">{t('arcade.waiting')}</p>
			{:else if phase === 'reveal' && result}
				<p class="arcade__result" class:is-won={result.you.correct} class:is-lost={!result.you.correct}>
					<span>{result.you.correct ? t('arcade.correct') : t('arcade.wrong')}</span>
					<span class="arcade__points">{delta(result.you.points)}</span>
				</p>
			{/if}
		</div>
	</section>
{:else}
	<section class="arcade arcade--center">
		<header class="brand">
			<h1 class="wordmark">
				{t('home.wordmark_omni')}<span class="wordmark__accent">{t('home.wordmark_sapiens')}</span>
			</h1>
		</header>
		<p class="muted">{t('arcade.loading')}</p>
		{#if run?.notice}
			<p class="arcade__result is-lost">{t(noticeKey(run.notice))}</p>
		{/if}
	</section>
{/if}

<style>
	.arcade {
		display: flex;
		flex: 1;
		flex-direction: column;
		gap: var(--s-3);
		height: calc(100dvh - var(--shell-pad-top) - var(--shell-pad-bottom));
		min-height: min-content;
	}

	.arcade--center {
		align-items: center;
		justify-content: center;
		text-align: center;
	}

	.arcade .match__tiles {
		flex: 1 1 calc(48px * 4 + var(--s-3) * 3);
		max-height: calc(62px * 4 + var(--s-3) * 3);
	}

	.arcade .match__foot {
		margin-top: 0;
	}

	.hud {
		display: flex;
		align-items: center;
		justify-content: space-between;
		gap: var(--s-3);
		padding: 0 var(--s-1);
	}

	.stat {
		display: flex;
		flex-direction: column;
		gap: 1px;
	}

	.stat__label {
		color: var(--ink-3);
		font-size: 0.68rem;
		font-weight: 700;
		letter-spacing: 0.08em;
		text-transform: uppercase;
	}

	.stat__value {
		color: var(--ink);
		font-family: var(--font-display);
		font-size: 1.35rem;
		font-weight: 700;
		line-height: 1;
	}

	.arcade__round {
		color: var(--ink-3);
		font-size: 0.8rem;
		font-weight: 700;
		letter-spacing: 0.08em;
		text-transform: uppercase;
	}

	.arcade__result {
		display: flex;
		align-items: center;
		gap: var(--s-2);
		font-family: var(--font-display);
		font-size: 1.1rem;
		font-weight: 700;
	}

	.arcade__result.is-won {
		color: #58e08d;
	}

	.arcade__result.is-lost {
		color: var(--red-ink);
	}

	.arcade__points {
		padding: 2px 8px;
		border-radius: var(--r-sm);
		background: rgb(0 0 0 / 0.2);
		color: var(--ink);
		font-size: 0.9rem;
	}

	.arcade-end {
		display: flex;
		flex: 1;
		flex-direction: column;
		gap: var(--s-4);
	}

	.end-score {
		display: flex;
		flex-direction: column;
		align-items: center;
		gap: var(--s-1);
		padding: var(--s-5) var(--s-4);
		border-radius: var(--r-lg);
		background: var(--panel-bg);
		box-shadow: 0 5px 0 var(--panel-edge);
	}

	.end-score__label {
		color: var(--ink-3);
		font-size: 0.75rem;
		font-weight: 700;
		letter-spacing: 0.1em;
		text-transform: uppercase;
	}

	.end-score__value {
		color: var(--yellow);
		font-family: var(--font-display);
		font-size: clamp(3rem, 18vw, 4.5rem);
		font-weight: 700;
		line-height: 1;
		text-shadow: 0 5px 0 var(--yellow-edge);
	}

	.end-score__best {
		margin-top: var(--s-1);
		padding: 4px 10px;
		border-radius: var(--r-full);
		background: var(--green);
		box-shadow: 0 3px 0 var(--green-edge);
		color: #ffffff;
		font-family: var(--font-display);
		font-size: 0.75rem;
		font-weight: 700;
		letter-spacing: 0.08em;
		text-transform: uppercase;
	}

	.end-stats {
		display: grid;
		grid-template-columns: repeat(3, 1fr);
		gap: var(--s-2);
		margin: 0;
	}

	.end-stats > div {
		display: flex;
		flex-direction: column;
		align-items: center;
		gap: 2px;
		padding: var(--s-3) var(--s-2);
		border-radius: var(--r-md);
		background: var(--well-bg);
		box-shadow: inset 0 3px 0 rgb(0 0 0 / 0.3);
	}

	.end-stats dt {
		color: var(--ink-3);
		font-size: 0.68rem;
		font-weight: 700;
		letter-spacing: 0.06em;
		text-align: center;
		text-transform: uppercase;
	}

	.end-stats dd {
		margin: 0;
		color: var(--ink);
		font-family: var(--font-display);
		font-size: 1.4rem;
		font-weight: 700;
	}

	.end-ranks {
		display: grid;
		grid-template-columns: 1fr 1fr;
		gap: var(--s-2);
	}

	.end-ranks > div {
		display: flex;
		align-items: center;
		justify-content: space-between;
		padding: var(--s-3);
		border-radius: var(--r-md);
		background: var(--panel-bg);
		box-shadow: 0 4px 0 var(--panel-edge);
	}

	.end-ranks span {
		color: var(--ink-3);
		font-size: 0.8rem;
		font-weight: 600;
	}

	.end-ranks strong {
		color: var(--ink);
		font-family: var(--font-display);
		font-size: 1.2rem;
	}

	.end-best {
		color: var(--ink-3);
		text-align: center;
	}
</style>

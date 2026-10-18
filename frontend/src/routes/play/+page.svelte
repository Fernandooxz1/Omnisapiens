<script lang="ts">
	import { onMount } from 'svelte';
	import { goto } from '$app/navigation';
	import { page } from '$app/state';
	import type { ApiError } from '#lib/api/client';
	import { session } from '#lib/api/session.svelte';
	import AnswerTile, { type TileState } from '#lib/components/AnswerTile.svelte';
	import Button from '#lib/components/Button.svelte';
	import QuestionCard from '#lib/components/QuestionCard.svelte';
	import Scoreboard from '#lib/components/Scoreboard.svelte';
	import TimerBadge from '#lib/components/TimerBadge.svelte';
	import { categoryKey } from '#lib/categories';
	import { t, type MessageKey } from '#lib/i18n';
	import { createLiveMatch, type LiveMatch } from '#lib/match/live.svelte';

	type Who = 'you' | 'rival';

	/** La sala llega por query hasta que exista el lobby, que es quien la elige. */
	const code = $derived(page.url.searchParams.get('code') ?? '');

	let match = $state<LiveMatch | null>(null);
	/** Antes de tener canal: falta el código o la sesión. */
	let blocked = $state<MessageKey | null>(null);
	let now = $state(Date.now());

	const phase = $derived(match?.phase ?? 'connecting');
	const question = $derived(match?.question ?? null);
	const ended = $derived(match?.ended ?? null);
	const problem = $derived(blocked ?? failureKey(match?.failure ?? null));

	/** Segundos del `ends_at` del servidor: el cliente no calcula tiempo propio. */
	const seconds = $derived(
		question ? Math.max(0, Math.ceil((question.endsAt - now) / 1000)) : 0
	);
	const alert = $derived(phase === 'question' && seconds <= 5);
	const timeLeft = $derived(
		question ? Math.min(100, Math.round((seconds / question.totalSeconds) * 100)) : 0
	);

	const result = $derived(match?.result ?? null);
	const picked = $derived(match?.picked ?? null);
	const rivalPick = $derived(result?.opponent.choice ?? null);
	const youRight = $derived(result?.you.correct ?? false);
	const deltaText = $derived(
		t('play.delta', {
			you: delta(result?.you.points ?? 0),
			name: match?.rival ?? '',
			rival: delta(result?.opponent.points ?? 0)
		})
	);

	onMount(() => {
		let live: LiveMatch | null = null;

		(async () => {
			await session.restore();

			if (!session.token) {
				blocked = 'play.error_auth';
				return;
			}
			if (!code) {
				blocked = 'play.error_code';
				return;
			}

			live = createLiveMatch(code, session.token);
			match = live;
		})();

		// Irse de la pantalla es abandonar: el rival ve su ventana de gracia.
		return () => live?.close();
	});

	$effect(() => {
		const id = setInterval(() => (now = Date.now()), 250);
		return () => clearInterval(id);
	});

	function failureKey(error: ApiError | null): MessageKey | null {
		if (!error) return null;

		switch (error.code) {
			case 'AUTH_REQUIRED':
				return 'play.error_auth';
			case 'ROOM_NOT_FOUND':
				return 'play.error_room';
			case 'ROOM_FULL':
				return 'play.error_full';
			case 'RATE_LIMITED':
				return 'play.error_limited';
			default:
				return 'play.error_generic';
		}
	}

	function noticeKey(value: string): MessageKey {
		return value === 'NO_QUESTIONS' ? 'play.error_no_questions' : 'play.error_generic';
	}

	/** Cápsula de cada ronda: ganada, perdida, la que corre o todavía vacía. */
	function capsuleState(index: number): 'won' | 'lost' | 'current' | undefined {
		if (index === question?.round && phase !== 'reveal') return 'current';
		return match?.history[index];
	}

	/** Quiénes eligieron esta opción (el rival recién al revelar). */
	function whoPicked(index: number): Who[] {
		const who: Who[] = [];
		if (index === picked) who.push('you');
		if (phase === 'reveal' && index === rivalPick) who.push('rival');
		return who;
	}

	function tileState(index: number): TileState {
		if (phase === 'reveal') {
			if (index === result?.correctIndex) return 'correct';
			if (index === picked || index === rivalPick) return 'wrong';
			return 'dim';
		}
		if (phase !== 'question' && index === picked) return 'selected';
		return 'idle';
	}

	function tileTag(index: number): string | undefined {
		const who = whoPicked(index);
		if (who.length === 0) return undefined;
		return who.map((one) => (one === 'you' ? t('play.you') : (match?.rival ?? ''))).join(' · ');
	}

	function tileMark(index: number): 'correct' | 'wrong' | undefined {
		if (phase !== 'reveal' || whoPicked(index).length === 0) return undefined;
		return index === result?.correctIndex ? 'correct' : 'wrong';
	}

	function delta(points: number) {
		return points > 0 ? `+${points}` : '+0';
	}
</script>

{#if problem}
	<section class="match">
		<div class="match__foot">
			<h1 class="page-title">{t('play.title')}</h1>
			<p class="muted">{t(problem)}</p>
		</div>
		<div class="modes">
			<Button variant="slate" title={t('common.back')} onclick={() => goto('/')} />
		</div>
	</section>
{:else if phase === 'waiting' || phase === 'starting'}
	<section class="match">
		<div class="match__foot">
			<h1 class="page-title">{t('play.waiting_room', { code })}</h1>
			<p class="muted">
				{phase === 'starting' ? t('play.starting') : t('play.waiting_rival')}
			</p>
		</div>
		<div class="modes">
			<Button variant="slate" title={t('common.back')} onclick={() => goto('/')} />
		</div>
	</section>
{:else if phase === 'over' && ended}
	<section class="match">
		<div class="match__foot">
			<h1 class="page-title">
				{ended.winner === 'you'
					? t('play.won')
					: ended.winner === 'opponent'
						? t('play.lost')
						: t('play.tie')}
			</h1>
			<Scoreboard
				you={{ nick: match?.you ?? '', points: match?.scores.you ?? 0 }}
				rival={{ nick: match?.rival ?? '', points: match?.scores.opponent ?? 0 }}
			/>
			{#if ended.reason === 'abandoned'}
				<p class="muted">{t('play.abandoned')}</p>
			{/if}
			{#if match?.rematchWaiting}
				<p class="muted">{t('play.rematch_waiting')}</p>
			{/if}
		</div>
		<div class="modes">
			<Button
				variant="green"
				title={t('play.rematch')}
				disabled={match?.rematchWaiting}
				onclick={() => match?.rematch()}
			/>
			<Button variant="slate" title={t('common.back')} onclick={() => goto('/')} />
		</div>
	</section>
{:else if question && match}
	<section class="match match--live">
		<div class="match__head">
			<header class="brand">
				<h1 class="wordmark">
					{t('home.wordmark_omni')}<span class="wordmark__accent">{t('home.wordmark_sapiens')}</span>
				</h1>
			</header>

			<div class="match__top">
				<span class="sr-only">
					{t('play.round', { n: question.round + 1, total: match.total })}
				</span>
				<div class="round-capsules" aria-hidden="true">
					{#each { length: match.total } as _, index (index)}
						<span
							class="capsule"
							class:is-won={capsuleState(index) === 'won'}
							class:is-lost={capsuleState(index) === 'lost'}
							class:is-current={capsuleState(index) === 'current'}
						></span>
					{/each}
				</div>
				<TimerBadge {seconds} {alert} idle={phase !== 'question'} />
			</div>
		</div>

		<Scoreboard
			you={{ nick: match.you, points: match.scores.you }}
			rival={{ nick: match.rival, points: match.scores.opponent }}
		/>

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
					tag={tileTag(index)}
					mark={tileMark(index)}
					disabled={phase !== 'question'}
					onclick={() => match?.answer(index)}
				/>
			{/each}
		</div>

		<div class="match__foot" aria-live="polite">
			{#if match.rivalGone !== null}
				<p class="muted">{t('play.rival_gone', { nick: match.rival, n: match.rivalGone })}</p>
			{:else if match.status === 'reconnecting'}
				<p class="muted">{t('play.reconnecting')}</p>
			{:else if match.notice}
				<p class="muted">{t(noticeKey(match.notice))}</p>
			{:else if phase === 'question'}
				<p class="muted">
					{match.rivalAnswered ? t('play.opponent_answered') : t('play.hint')}
				</p>
			{:else if phase === 'answered'}
				<p class="muted">{t('play.waiting', { nick: match.rival })}</p>
			{:else}
				<p class="sr-only">{deltaText}. {youRight ? t('play.correct') : t('play.wrong')}</p>
			{/if}
		</div>

		{#if phase === 'reveal'}
			<div class="match__cta">
				<p class="muted">{deltaText}</p>
			</div>
		{/if}
	</section>
{:else}
	<section class="match">
		<div class="match__foot">
			<p class="muted">{t('play.connecting')}</p>
		</div>
	</section>
{/if}

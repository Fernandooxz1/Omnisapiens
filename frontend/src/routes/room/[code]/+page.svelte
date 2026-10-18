<script lang="ts">
	import { onMount } from 'svelte';
	import { goto } from '$app/navigation';
	import { page } from '$app/state';
	import { ApiError } from '#lib/api/client';
	import { previewRoom } from '#lib/api/rooms';
	import { session } from '#lib/api/session.svelte';
	import AnswerTile, { type TileState } from '#lib/components/AnswerTile.svelte';
	import Button from '#lib/components/Button.svelte';
	import Icon from '#lib/components/Icon.svelte';
	import PlayerPanel from '#lib/components/PlayerPanel.svelte';
	import QuestionCard from '#lib/components/QuestionCard.svelte';
	import Scoreboard from '#lib/components/Scoreboard.svelte';
	import TimerBadge from '#lib/components/TimerBadge.svelte';
	import { categoryKey } from '#lib/categories';
	import { t, type MessageKey } from '#lib/i18n';
	import { bindAnswerKeys } from '#lib/keyboard.svelte';
	import { createLiveMatch, type LiveMatch } from '#lib/match/live.svelte';
	import { sound } from '#lib/sound.svelte';

	type Who = 'you' | 'rival';

	const code = $derived((page.params.code ?? '').toUpperCase());

	let match = $state<LiveMatch | null>(null);
	/** Antes de tener canal: falta el código o la sesión. */
	let blocked = $state<MessageKey | null>(null);
	/** El host es quien creó la sala; `room_state` no lo manda (ver `docs/api.md`). */
	let hostNick = $state<string | null>(null);
	let starting = $state(false);
	let copied = $state(false);
	let copyTimer: ReturnType<typeof setTimeout> | null = null;
	let revealTimer: ReturnType<typeof setTimeout> | null = null;
	let now = $state(Date.now());
	/** Opción marcada con `1`–`4`, a la espera de `Enter`. */
	let selected = $state<number | null>(null);

	const phase = $derived(match?.phase ?? 'connecting');
	const question = $derived(match?.question ?? null);
	const ended = $derived(match?.ended ?? null);
	const seats = $derived(match?.players ?? []);
	const config = $derived(match?.config ?? { rounds: 0, seconds: 0 });
	const isHost = $derived(hostNick !== null && match?.you === hostNick);
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

	/** Una pregunta nueva empieza sin marca de teclado. */
	$effect(() => {
		if (question) selected = null;
	});

	let lastTick = 0;
	$effect(() => {
		if (phase !== 'question') {
			lastTick = 0;
			return;
		}
		if (seconds > 0 && seconds <= 5 && seconds !== lastTick) {
			lastTick = seconds;
			sound.play('tick');
		}
	});

	let lastPhase = 'connecting';
	$effect(() => {
		const next = phase;
		if (next === 'starting' && lastPhase !== 'starting') sound.play('match_start');
		lastPhase = next;
	});

	let lastReveal = false;
	$effect(() => {
		const revealing = phase === 'reveal';
		if (revealing && !lastReveal) {
			sound.play('reveal');
			const correct = result?.you.correct;
			if (correct !== undefined) {
				if (revealTimer) clearTimeout(revealTimer);
				revealTimer = setTimeout(() => sound.play(correct ? 'correct' : 'wrong'), 120);
			}
		}
		lastReveal = revealing;
	});

	let lastEnded: unknown = null;
	$effect(() => {
		if (phase !== 'over' || !ended || ended === lastEnded) return;
		lastEnded = ended;
		sound.play(
			ended.winner === 'you' ? 'match_win' : ended.winner === 'opponent' ? 'match_lose' : 'reveal'
		);
	});

	bindAnswerKeys({
		enabled: () => phase === 'question' && question !== null,
		count: () => question?.options.length ?? 0,
		select: (index) => (selected = index),
		confirm: () => {
			if (selected === null) return;
			choose(selected);
		}
	});

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

			// La vista previa valida la sala y trae el host; si la API no contesta,
			// el WebSocket decide (y reintenta) sin bloquear la pantalla.
			try {
				const preview = await previewRoom(code);
				hostNick = preview.host_nick;
			} catch (failure) {
				if (failure instanceof ApiError && failure.code === 'ROOM_NOT_FOUND') {
					blocked = 'play.error_room';
					return;
				}
			}

			live = createLiveMatch(code, session.token);
			match = live;
		})();

		// Irse de la pantalla es abandonar: el rival ve su ventana de gracia.
		return () => {
			live?.close();
			if (copyTimer) clearTimeout(copyTimer);
			if (revealTimer) clearTimeout(revealTimer);
		};
	});

	$effect(() => {
		// Al volver al lobby (o si el `start` fue rechazado) el botón se destraba.
		if (phase === 'waiting' || match?.notice) starting = false;
	});

	$effect(() => {
		const id = setInterval(() => (now = Date.now()), 250);
		return () => clearInterval(id);
	});

	function startMatch() {
		if (starting || !match) return;
		starting = match.start();
	}

	function choose(index: number) {
		selected = null;
		match?.answer(index);
	}

	async function copyCode() {
		try {
			await navigator.clipboard.writeText(code);
			copied = true;
			if (copyTimer) clearTimeout(copyTimer);
			copyTimer = setTimeout(() => (copied = false), 1600);
		} catch {
			/* sin portapapeles: el código queda seleccionable a mano */
		}
	}

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
		switch (value) {
			case 'NOT_READY':
				return 'lobby.error_not_ready';
			case 'ALREADY_PLAYING':
				return 'lobby.error_already';
			case 'NO_QUESTIONS':
				return 'play.error_no_questions';
			default:
				return 'play.error_generic';
		}
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
		if (index === selected) return 'selected';
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
	<section class="lobby">
		<header class="brand">
			<h1 class="wordmark">
				{t('home.wordmark_omni')}<span class="wordmark__accent">{t('home.wordmark_sapiens')}</span>
			</h1>
		</header>

		<div class="lobby__code-card">
			<p class="lobby__eyebrow">{t('lobby.title')}</p>
			<p class="lobby__code" aria-label={t('play.waiting_room', { code })}>{code}</p>
			<button type="button" class="lobby__copy" onclick={copyCode} aria-live="polite">
				{copied ? t('lobby.copied') : t('lobby.copy')}
			</button>
		</div>

		<p class="lobby__config">
			{t('lobby.config', { rounds: config.rounds, seconds: config.seconds })}
		</p>

		<div class="lobby__players" aria-label={t('lobby.players')}>
			{#each seats as player (player.id)}
				<PlayerPanel nick={player.nick} you={player.id === match?.youId} />
			{/each}
			{#if seats.length < 2}
				<PlayerPanel empty />
			{/if}
		</div>

		<div class="lobby__foot">
			{#if phase === 'starting'}
				<p class="muted">{t('play.starting')}</p>
			{:else if isHost}
				<Button
					variant="green"
					title={t('lobby.start')}
					disabled={seats.length < 2 || starting}
					onclick={startMatch}
				/>
				{#if seats.length < 2}
					<p class="muted">{t('lobby.host_hint')}</p>
				{/if}
			{:else}
				<p class="muted">{t('lobby.guest_hint')}</p>
			{/if}

			{#if match?.notice}
				<p class="lobby__error" role="alert">{t(noticeKey(match.notice))}</p>
			{/if}
		</div>

		<a class="rank-link" href="/">{t('lobby.leave')}</a>
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
			{#if ended.rounds.length > 0}
				<section class="summary" aria-label={t('end.summary')}>
					<h2 class="summary__title">{t('end.summary')}</h2>
					<div class="summary__head" aria-hidden="true">
						<span></span>
						<span>{t('play.you')}</span>
						<span class="summary__rival">{match?.rival ?? ''}</span>
					</div>
					<ol class="summary__list">
						{#each ended.rounds as round (round.round)}
							<li class="summary__row">
								<span class="summary__round">{t('end.round', { n: round.round + 1 })}</span>
								<span
									class="summary__score"
									aria-label={`${round.you.correct ? t('end.correct') : t('end.missed')} ${delta(round.you.points)}`}
								>
									<span class:is-won={round.you.correct} class:is-lost={!round.you.correct}>
										<Icon name={round.you.correct ? 'check' : 'x'} size={14} />
									</span>
									{delta(round.you.points)}
								</span>
								<span
									class="summary__score"
									aria-label={`${round.opponent.correct ? t('end.correct') : t('end.missed')} ${delta(round.opponent.points)}`}
								>
									<span
										class:is-won={round.opponent.correct}
										class:is-lost={!round.opponent.correct}
									>
										<Icon name={round.opponent.correct ? 'check' : 'x'} size={14} />
									</span>
									{delta(round.opponent.points)}
								</span>
							</li>
						{/each}
					</ol>
				</section>
			{/if}
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
					onclick={() => choose(index)}
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

<style>
	.lobby {
		display: flex;
		flex: 1;
		flex-direction: column;
		gap: var(--s-4);
	}

	.lobby__code-card {
		display: flex;
		flex-direction: column;
		align-items: center;
		gap: var(--s-3);
		padding: var(--s-5) var(--s-4);
		border-radius: var(--r-lg);
		background: var(--panel-bg);
		box-shadow: 0 5px 0 var(--panel-edge);
		text-align: center;
	}

	.lobby__eyebrow {
		color: var(--ink-3);
		font-family: var(--font-ui);
		font-size: 0.75rem;
		font-weight: 700;
		letter-spacing: 0.12em;
		text-transform: uppercase;
	}

	.lobby__code {
		user-select: all;
		color: var(--yellow);
		font-family: var(--font-display);
		font-size: clamp(2.75rem, 16vw, 3.9rem);
		font-weight: 700;
		letter-spacing: 0.12em;
		line-height: 1;
		text-shadow: 0 5px 0 var(--yellow-edge);
	}

	.lobby__copy {
		min-height: 44px;
		padding: 0 var(--s-4);
		border: 0;
		border-radius: var(--r-full);
		background: var(--well-bg);
		box-shadow: inset 0 3px 0 rgb(0 0 0 / 0.35);
		color: var(--ink-2);
		font-family: var(--font-ui);
		font-size: 0.85rem;
		font-weight: 600;
		cursor: pointer;
	}

	.lobby__config {
		color: var(--ink-3);
		font-size: 0.9rem;
		text-align: center;
	}

	.lobby__players {
		display: flex;
		flex-direction: column;
		gap: var(--s-2);
	}

	.lobby__foot {
		display: flex;
		flex-direction: column;
		gap: var(--s-2);
		margin-top: auto;
	}

	.lobby__error {
		color: var(--red-ink);
		font-size: 0.85rem;
		font-weight: 600;
		text-align: center;
	}

	.summary {
		display: flex;
		flex-direction: column;
		gap: var(--s-2);
		padding: var(--s-3);
		border-radius: var(--r-md);
		background: var(--well-bg);
		box-shadow: inset 0 3px 0 rgb(0 0 0 / 0.3);
	}

	.summary__title {
		color: var(--ink-3);
		font-family: var(--font-ui);
		font-size: 0.75rem;
		font-weight: 700;
		letter-spacing: 0.08em;
		text-transform: uppercase;
	}

	.summary__head,
	.summary__row {
		display: grid;
		grid-template-columns: minmax(64px, auto) 1fr 1fr;
		align-items: center;
		gap: var(--s-2);
	}

	.summary__head {
		color: var(--ink-3);
		font-size: 0.7rem;
		font-weight: 600;
		letter-spacing: 0.04em;
		text-transform: uppercase;
	}

	.summary__head > span:not(:first-child) {
		overflow: hidden;
		text-align: center;
		text-overflow: ellipsis;
		white-space: nowrap;
	}

	.summary__list {
		display: flex;
		flex-direction: column;
		gap: var(--s-1);
		margin: 0;
		padding: 0;
		list-style: none;
	}

	.summary__round {
		color: var(--ink-3);
		font-size: 0.8rem;
		font-weight: 600;
	}

	.summary__score {
		display: flex;
		align-items: center;
		justify-content: center;
		gap: 5px;
		min-height: 30px;
		border-radius: var(--r-sm);
		background: var(--panel-bg);
		box-shadow: 0 2px 0 var(--panel-edge);
		color: var(--ink);
		font-family: var(--font-display);
		font-size: 0.95rem;
		font-weight: 700;
	}

	.summary__score > span {
		display: inline-flex;
	}

	.summary__score .is-won {
		color: #58e08d;
	}

	.summary__score .is-lost {
		color: var(--red-ink);
	}
</style>

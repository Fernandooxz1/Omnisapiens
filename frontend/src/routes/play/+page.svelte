<script lang="ts">
	import { goto } from '$app/navigation';
	import AnswerTile, { type TileState } from '#lib/components/AnswerTile.svelte';
	import Button from '#lib/components/Button.svelte';
	import QuestionCard from '#lib/components/QuestionCard.svelte';
	import Scoreboard from '#lib/components/Scoreboard.svelte';
	import TimerBadge from '#lib/components/TimerBadge.svelte';
	import { categoryKey } from '#lib/categories';
	import {
		DEMO_POINTS,
		DEMO_RIVAL,
		DEMO_ROUNDS,
		DEMO_YOU,
		ROUND_SECONDS
	} from '#lib/demo/partida';
	import { t } from '#lib/i18n';

	type Phase = 'question' | 'waiting' | 'reveal';
	type Who = 'you' | 'rival';

	let round = $state(0);
	let phase = $state<Phase>('question');
	let picked = $state<number | null>(null);
	let pointsYou = $state(0);
	let pointsRival = $state(0);
	let results = $state<('won' | 'lost')[]>([]);
	let endsAt = $state(Date.now() + ROUND_SECONDS * 1000);
	let now = $state(Date.now());

	const current = $derived(DEMO_ROUNDS[Math.min(round, DEMO_ROUNDS.length - 1)]);
	const finished = $derived(round >= DEMO_ROUNDS.length);
	const seconds = $derived(Math.max(0, Math.ceil((endsAt - now) / 1000)));
	const alert = $derived(phase === 'question' && seconds <= 5);
	const youRight = $derived(picked === current.correct);
	const timeLeft = $derived(phase === 'reveal' ? 0 : Math.round((seconds / ROUND_SECONDS) * 100));

	// Demo: en el juego real el cliente solo dibuja el `ends_at` que manda el servidor.
	$effect(() => {
		const id = setInterval(() => (now = Date.now()), 250);
		return () => clearInterval(id);
	});

	$effect(() => {
		if (phase === 'question' && !finished && seconds === 0) reveal();
	});

	function pick(index: number) {
		if (phase !== 'question' || finished) return;
		picked = index;
		phase = 'waiting';
		setTimeout(reveal, 900);
	}

	function reveal() {
		if (phase === 'reveal' || finished) return;
		phase = 'reveal';
		results[round] = picked === current.correct ? 'won' : 'lost';
		if (picked === current.correct) pointsYou += DEMO_POINTS;
		if (current.rivalPick === current.correct) pointsRival += DEMO_POINTS;
	}

	function next() {
		round += 1;
		picked = null;
		phase = 'question';
		endsAt = Date.now() + ROUND_SECONDS * 1000;
	}

	function restart() {
		round = 0;
		picked = null;
		phase = 'question';
		pointsYou = 0;
		pointsRival = 0;
		results = [];
		endsAt = Date.now() + ROUND_SECONDS * 1000;
	}

	/** Cápsula de cada ronda: ganada, perdida, la que corre o todavía vacía. */
	function capsuleState(index: number): 'won' | 'lost' | 'current' | undefined {
		if (index === round && phase !== 'reveal') return 'current';
		return results[index];
	}

	/** Quiénes eligieron esta opción (el rival recién al revelar). */
	function whoPicked(index: number): Who[] {
		const who: Who[] = [];
		if (index === picked) who.push('you');
		if (phase === 'reveal' && index === current.rivalPick) who.push('rival');
		return who;
	}

	function tileState(index: number): TileState {
		if (phase === 'reveal') {
			if (index === current.correct) return 'correct';
			if (index === picked || index === current.rivalPick) return 'wrong';
			return 'dim';
		}
		if (phase === 'waiting' && index === picked) return 'selected';
		return 'idle';
	}

	function tileTag(index: number): string | undefined {
		const who = whoPicked(index);
		if (who.length === 0) return undefined;
		return who.map((one) => (one === 'you' ? t('play.you') : DEMO_RIVAL)).join(' · ');
	}

	function tileMark(index: number): 'correct' | 'wrong' | undefined {
		if (phase !== 'reveal' || whoPicked(index).length === 0) return undefined;
		return index === current.correct ? 'correct' : 'wrong';
	}

	function delta(points: number) {
		return points > 0 ? `+${points}` : '+0';
	}
</script>

{#if finished}
	<section class="match">
		<div class="match__foot">
			<h1 class="page-title">{t('play.finish')}</h1>
			<Scoreboard
				you={{ nick: DEMO_YOU, points: pointsYou }}
				rival={{ nick: DEMO_RIVAL, points: pointsRival }}
			/>
			<p class="muted">{t('play.demo')}</p>
		</div>
		<div class="modes">
			<Button variant="green" title={t('play.rematch')} onclick={restart} />
			<Button variant="slate" title={t('common.back')} onclick={() => goto('/')} />
		</div>
	</section>
{:else}
	<section class="match">
		<div class="match__top">
			<span class="sr-only">{t('play.round', { n: round + 1, total: DEMO_ROUNDS.length })}</span>
			<div class="round-capsules" aria-hidden="true">
				{#each DEMO_ROUNDS as _, index (index)}
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

		<Scoreboard
			you={{ nick: DEMO_YOU, points: pointsYou }}
			rival={{ nick: DEMO_RIVAL, points: pointsRival }}
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
			category={current.category}
			categoryLabel={t(categoryKey(current.category))}
			prompt={current.prompt}
			badge={phase === 'question' ? t('play.answer_badge') : undefined}
		/>

		<div class="match__tiles">
			{#each current.options as option, index (index)}
				<AnswerTile
					keycap={String(index + 1)}
					label={option}
					state={tileState(index)}
					tag={tileTag(index)}
					mark={tileMark(index)}
					disabled={phase !== 'question'}
					onclick={() => pick(index)}
				/>
			{/each}
		</div>

		<div class="match__foot" aria-live="polite">
			{#if phase === 'question'}
				<p class="muted">{t('play.hint')}</p>
			{:else if phase === 'waiting'}
				<p class="muted">{t('play.waiting', { nick: DEMO_RIVAL })}</p>
			{:else}
				<p class="delta">
					{t('play.delta', {
						you: delta(youRight ? DEMO_POINTS : 0),
						name: DEMO_RIVAL,
						rival: delta(current.rivalPick === current.correct ? DEMO_POINTS : 0)
					})}
				</p>
				<p class="sr-only">{youRight ? t('play.correct') : t('play.wrong')}</p>
				<Button variant="blue" title={t('play.next')} onclick={next} />
			{/if}
		</div>
	</section>
{/if}

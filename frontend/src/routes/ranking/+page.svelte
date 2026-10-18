<script lang="ts">
	import { onMount } from 'svelte';
	import { leaderboard, myRanks } from '#lib/api/leaderboard';
	import { session } from '#lib/api/session.svelte';
	import type { LeaderboardEntry, LeaderboardPeriod, MyRanks } from '#lib/api/types';
	import Button from '#lib/components/Button.svelte';
	import Icon from '#lib/components/Icon.svelte';
	import { t } from '#lib/i18n';

	const LIMIT = 50;
	const PERIODS: LeaderboardPeriod[] = ['all', 'week'];

	let period = $state<LeaderboardPeriod>('week');
	let entries = $state<LeaderboardEntry[]>([]);
	let loading = $state(true);
	let failed = $state(false);
	let mine = $state<MyRanks | null>(null);
	let request = 0;

	const me = $derived(mine ? (period === 'all' ? mine.global : mine.week) : null);

	onMount(async () => {
		await session.restore();
		if (!session.token) return;

		try {
			mine = await myRanks(session.token);
		} catch {
			// Sin posición propia el ranking público sigue sirviendo.
			mine = null;
		}
	});

	$effect(() => {
		const selected = period;
		void load(selected);
	});

	async function load(selected: LeaderboardPeriod) {
		const current = ++request;
		loading = true;
		failed = false;
		entries = [];

		try {
			const board = await leaderboard(selected, LIMIT);
			if (current !== request) return;
			entries = board.entries;
		} catch {
			if (current === request) failed = true;
		} finally {
			if (current === request) loading = false;
		}
	}

	function isMe(nick: string): boolean {
		return session.user?.nick === nick;
	}
</script>

<section class="ranking">
	<header class="ranking__intro">
		<h1 class="page-title">{t('ranking.title')}</h1>
		<p class="ranking__hint">
			{period === 'week' ? t('ranking.week_hint') : t('ranking.all_hint')}
		</p>
	</header>

	<div class="segmented" role="group" aria-label={t('ranking.period')}>
		{#each PERIODS as value (value)}
			<button
				type="button"
				class="segment"
				class:is-on={period === value}
				aria-pressed={period === value}
				onclick={() => (period = value)}
			>
				{value === 'all' ? t('ranking.global') : t('ranking.week')}
			</button>
		{/each}
	</div>

	{#if mine}
		<div class="me">
			<span class="me__label">{t('ranking.mine')}</span>
			{#if me && me.rank !== null && me.score !== null}
				<strong class="me__rank">{t('arcade.rank', { n: me.rank })}</strong>
				<span class="me__score">{t('ranking.score', { n: me.score })}</span>
			{:else}
				<span class="me__hint">{t('ranking.no_rank')}</span>
			{/if}
		</div>
	{/if}

	{#if loading}
		<p class="ranking__state">{t('ranking.loading')}</p>
	{:else if failed}
		<div class="ranking__state">
			<p>{t('ranking.error')}</p>
			<Button variant="slate" title={t('ranking.retry')} onclick={() => load(period)} />
		</div>
	{:else if entries.length === 0}
		<p class="ranking__state">{t('ranking.empty')}</p>
	{:else}
		<div class="ranking__head" aria-hidden="true">
			<span></span>
			<span>{t('ranking.player')}</span>
			<span>{t('ranking.points')}</span>
		</div>
		<ol class="ranking__list" aria-label={t('ranking.title')}>
			{#each entries as entry (entry.position)}
				<li
					class="row"
					class:is-me={isMe(entry.nick)}
					aria-current={isMe(entry.nick) ? 'true' : undefined}
				>
					<span class="row__pos" class:is-first={entry.position === 1}>
						{entry.position}
						{#if entry.position === 1}
							<span class="row__crown"><Icon name="crown" size={13} /></span>
						{/if}
					</span>
					<span class="row__nick">
						<span class="row__name">{entry.nick}</span>
						{#if isMe(entry.nick)}
							<span class="row__tag">{t('lobby.you')}</span>
						{/if}
					</span>
					<span class="row__score">{entry.score}</span>
				</li>
			{/each}
		</ol>
	{/if}

	<a class="rank-link" href="/">{t('common.back')}</a>
</section>

<style>
	.ranking {
		display: flex;
		flex: 1;
		flex-direction: column;
		gap: var(--s-4);
	}

	.ranking__intro {
		display: flex;
		flex-direction: column;
		gap: var(--s-2);
		padding-top: var(--s-4);
	}

	.ranking__hint {
		color: var(--ink-3);
		font-size: 0.9rem;
	}

	.ranking__state {
		display: flex;
		flex-direction: column;
		align-items: center;
		gap: var(--s-3);
		padding: var(--s-6) var(--s-4);
		color: var(--ink-3);
		text-align: center;
	}

	.segmented {
		display: flex;
		gap: var(--s-1);
		padding: 4px;
		border-radius: var(--r-md);
		background: var(--well-bg);
		box-shadow: inset 0 3px 0 rgb(0 0 0 / 0.35);
	}

	.segment {
		flex: 1;
		min-height: 44px;
		border: 0;
		border-radius: var(--r-sm);
		background: transparent;
		color: var(--ink-3);
		font-family: var(--font-display);
		font-size: 0.95rem;
		font-weight: 700;
		cursor: pointer;
	}

	.segment.is-on {
		background: var(--panel-bg);
		box-shadow: 0 3px 0 var(--panel-edge);
		color: var(--ink);
	}

	.me {
		display: flex;
		align-items: center;
		gap: var(--s-3);
		padding: var(--s-3) var(--s-4);
		border-radius: var(--r-md);
		background: var(--well-bg);
		box-shadow: inset 0 3px 0 rgb(0 0 0 / 0.3);
	}

	.me__label {
		color: var(--ink-3);
		font-size: 0.72rem;
		font-weight: 700;
		letter-spacing: 0.08em;
		text-transform: uppercase;
	}

	.me__rank {
		margin-left: auto;
		color: var(--yellow);
		font-family: var(--font-display);
		font-size: 1.4rem;
		font-weight: 700;
		text-shadow: 0 3px 0 var(--yellow-edge);
	}

	.me__score {
		color: var(--ink-2);
		font-family: var(--font-display);
		font-size: 1rem;
		font-weight: 700;
	}

	.me__hint {
		margin-left: auto;
		color: var(--ink-3);
		font-size: 0.82rem;
		text-align: right;
	}

	.ranking__head {
		display: grid;
		grid-template-columns: 36px 1fr auto;
		gap: var(--s-3);
		padding: 0 var(--s-3);
		color: var(--ink-3);
		font-size: 0.7rem;
		font-weight: 700;
		letter-spacing: 0.08em;
		text-transform: uppercase;
	}

	.ranking__head > span:last-child {
		text-align: right;
	}

	.ranking__list {
		display: flex;
		flex-direction: column;
		gap: var(--s-1);
		margin: 0;
		padding: 0;
		list-style: none;
	}

	.row {
		display: grid;
		grid-template-columns: 36px 1fr auto;
		align-items: center;
		gap: var(--s-3);
		min-height: 48px;
		padding: var(--s-2) var(--s-3);
		border-radius: var(--r-md);
		background: var(--panel-bg);
		box-shadow: 0 3px 0 var(--panel-edge);
	}

	.row.is-me {
		background: var(--well-bg);
		box-shadow:
			inset 0 0 0 2px var(--yellow),
			0 3px 0 var(--panel-edge);
	}

	.row__pos {
		display: inline-flex;
		align-items: center;
		justify-content: center;
		gap: 3px;
		width: 36px;
		height: 32px;
		border-radius: var(--r-sm);
		background: var(--well-bg);
		color: var(--ink-3);
		font-family: var(--font-display);
		font-size: 0.95rem;
		font-weight: 700;
	}

	.row__pos.is-first {
		background: var(--yellow);
		box-shadow: 0 2px 0 var(--yellow-edge);
		color: var(--card-edge);
	}

	.row__crown {
		display: inline-flex;
	}

	.row__nick {
		display: flex;
		align-items: center;
		gap: var(--s-2);
		min-width: 0;
	}

	.row__name {
		overflow: hidden;
		color: var(--ink);
		font-size: 0.95rem;
		font-weight: 600;
		text-overflow: ellipsis;
		white-space: nowrap;
	}

	.row__tag {
		flex: none;
		padding: 2px 6px;
		border-radius: var(--r-full);
		background: var(--yellow);
		color: var(--card-edge);
		font-size: 0.62rem;
		font-weight: 700;
		letter-spacing: 0.06em;
		text-transform: uppercase;
	}

	.row__score {
		color: var(--ink);
		font-family: var(--font-display);
		font-size: 1.15rem;
		font-weight: 700;
	}
</style>

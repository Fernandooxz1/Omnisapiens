<script lang="ts">
	import { page } from '$app/state';
	import Icon from '#lib/components/Icon.svelte';
	import CaseEnvelope from '#lib/games/components/CaseEnvelope.svelte';
	import DifficultyChips from '#lib/games/components/DifficultyChips.svelte';
	import { findGame } from '#lib/games/catalog';
	import { DIFFICULTIES, DIFFICULTY_LABEL, countByDifficulty } from '#lib/games/difficulty';
	import type { DifficultyFilter } from '#lib/games/difficulty';
	import { fixturePreviews } from '#lib/games/murdoku/fixtures';
	import { countSolved } from '#lib/games/progress.svelte';
	import { t } from '#lib/i18n';

	const game = $derived(findGame(page.params.game ?? ''));

	/** Los casos reales llegan en la fase 2; por ahora el catálogo muestra previews. */
	const previews = $derived(game?.id === 'murdoku' ? fixturePreviews : []);
	const counts = $derived(countByDifficulty(previews.map((preview) => preview.meta)));
	const solved = $derived(game ? countSolved(game.id) : 0);

	let filter = $state<DifficultyFilter>('all');

	const sections = $derived(
		DIFFICULTIES.map((difficulty) => ({
			difficulty,
			cases: previews.filter((preview) => preview.meta.difficulty === difficulty)
		})).filter(
			(section) =>
				section.cases.length > 0 && (filter === 'all' || section.difficulty === filter)
		)
	);

	function caseCount(n: number): string {
		return n === 1 ? t('games.case_count_one', { n }) : t('games.case_count', { n });
	}
</script>

<svelte:head>
	<title>{game ? t(game.titleKey) : t('games.unknown_title')} · {t('app.title')}</title>
</svelte:head>

<section class="catalog">
	<a class="catalog__back" href="/juegos">
		<span class="catalog__back-icon"><Icon name="arrow" size={18} /></span>
		{t('games.back_hub')}
	</a>

	<header class="catalog__head">
		{#if game}
			<span class="catalog__icon"><Icon name={game.icon} size={30} /></span>
		{/if}
		<h1 class="page-title">{game ? t(game.titleKey) : t('games.unknown_title')}</h1>
		<p class="catalog__hint">{game ? t(game.blurbKey) : t('games.unknown_hint')}</p>
		{#if game && previews.length > 0}
			<p class="catalog__progress">
				{t('games.progress_summary', { solved, total: previews.length })}
			</p>
		{/if}
	</header>

	{#if game && previews.length > 0}
		<DifficultyChips
			{counts}
			total={previews.length}
			selected={filter}
			onselect={(value) => (filter = value)}
		/>

		<p class="catalog__note">{t('games.preview_note')}</p>

		{#if sections.length === 0}
			<p class="catalog__empty">{t('games.level_empty')}</p>
		{:else}
			{#each sections as section (section.difficulty)}
				<section class="catalog__section">
					<h2 class="catalog__section-title">
						{t(DIFFICULTY_LABEL[section.difficulty])}
						<span class="catalog__section-count">
							{caseCount(section.cases.length)}
						</span>
					</h2>

					<ul class="catalog__grid">
						{#each section.cases as preview (preview.meta.id)}
							<li>
								<CaseEnvelope {preview} href="/juegos/murdoku/{preview.meta.id}" />
							</li>
						{/each}
					</ul>
				</section>
			{/each}
		{/if}
	{:else if game}
		<div class="catalog__soon">
			<h2 class="catalog__soon-title">{t('games.catalog_soon')}</h2>
			<p class="catalog__soon-hint">{t('games.catalog_soon_hint')}</p>
		</div>
	{/if}
</section>

<style>
	.catalog {
		display: flex;
		flex: 1;
		flex-direction: column;
		gap: var(--s-4);
	}

	.catalog__back {
		display: inline-flex;
		align-self: flex-start;
		align-items: center;
		gap: var(--s-2);
		min-height: 44px;
		color: var(--ink-3);
		font-size: 0.9rem;
		font-weight: 700;
		text-decoration: none;
	}

	.catalog__back:hover {
		color: var(--ink);
	}

	.catalog__back-icon {
		display: inline-flex;
		transform: rotate(180deg);
	}

	.catalog__head {
		display: flex;
		flex-direction: column;
		gap: var(--s-2);
	}

	.catalog__icon {
		display: inline-flex;
		color: var(--accent);
	}

	.catalog__hint {
		max-width: 46ch;
		color: var(--ink-3);
	}

	.catalog__progress {
		color: var(--ink-2);
		font-family: var(--font-display);
		font-size: 1rem;
		font-weight: 700;
	}

	.catalog__note {
		color: var(--ink-3);
		font-size: 0.82rem;
	}

	.catalog__section {
		display: flex;
		flex-direction: column;
		gap: var(--s-3);
	}

	.catalog__section-title {
		display: flex;
		align-items: baseline;
		gap: var(--s-2);
		font-family: var(--font-display);
		font-size: 1.15rem;
	}

	.catalog__section-count {
		color: var(--ink-3);
		font-family: var(--font-ui);
		font-size: 0.78rem;
		font-weight: 700;
		letter-spacing: 0.04em;
		text-transform: uppercase;
	}

	.catalog__grid {
		display: grid;
		grid-template-columns: repeat(2, minmax(0, 1fr));
		gap: var(--s-3);
		margin: 0;
		padding: 0;
		list-style: none;
	}

	@media (min-width: 720px) {
		.catalog__grid {
			grid-template-columns: repeat(3, minmax(0, 1fr));
		}
	}

	@media (min-width: 1000px) {
		.catalog__grid {
			grid-template-columns: repeat(4, minmax(0, 1fr));
		}
	}

	.catalog__empty {
		color: var(--ink-3);
	}

	.catalog__soon {
		display: flex;
		flex-direction: column;
		gap: var(--s-2);
		padding: var(--s-5);
		border-radius: var(--r-lg);
		background: var(--well-bg);
		box-shadow: inset 0 4px 0 rgb(0 0 0 / 0.35);
	}

	.catalog__soon-title {
		font-family: var(--font-display);
		font-size: 1.15rem;
	}

	.catalog__soon-hint {
		color: var(--ink-3);
		font-size: 0.92rem;
	}
</style>

<script lang="ts">
	import { t } from '#lib/i18n';

	/** Una pregunta cerrada, con lo que eligió el jugador y la solución. */
	export interface ReviewItem {
		round: number;
		prompt: string;
		options: string[];
		correctIndex: number;
		choice: number | null;
		explanation: string | null;
	}

	interface Props {
		items: ReviewItem[];
	}

	let { items }: Props = $props();
</script>

<details class="review">
	<summary class="review__toggle">{t('review.title')}</summary>

	<ol class="review__list">
		{#each items as item (item.round)}
			<li class="review__row">
				<span class="review__round">{t('review.round', { n: item.round + 1 })}</span>
				<p class="review__prompt">{item.prompt}</p>

				<dl class="review__answers">
					<div>
						<dt>{t('review.yours')}</dt>
						<dd class:is-missing={item.choice === null}>
							{item.choice === null
								? t('review.none')
								: (item.options[item.choice] ?? t('review.none'))}
						</dd>
					</div>
					<div>
						<dt>{t('review.correct')}</dt>
						<dd>{item.options[item.correctIndex] ?? t('review.none')}</dd>
					</div>
				</dl>

				{#if item.explanation}
					<p class="review__why">{item.explanation}</p>
				{/if}
			</li>
		{/each}
	</ol>
</details>

<style>
	.review {
		border-radius: var(--r-md);
		background: var(--well-bg);
		box-shadow: inset 0 3px 0 rgb(0 0 0 / 0.3);
	}

	.review__toggle {
		display: flex;
		align-items: center;
		min-height: 44px;
		padding: 0 var(--s-3);
		color: var(--ink-2);
		font-family: var(--font-display);
		font-size: 0.9rem;
		font-weight: 700;
		letter-spacing: 0.04em;
		list-style: none;
		cursor: pointer;
	}

	.review__toggle::-webkit-details-marker {
		display: none;
	}

	.review__toggle::before {
		content: '▸';
		display: inline-block;
		margin-right: var(--s-2);
		color: var(--ink-3);
		transition: transform 0.15s ease;
	}

	.review[open] .review__toggle::before {
		transform: rotate(90deg);
	}

	.review__list {
		display: flex;
		flex-direction: column;
		gap: var(--s-3);
		margin: 0;
		padding: var(--s-1) var(--s-3) var(--s-3);
		list-style: none;
	}

	.review__row {
		display: flex;
		flex-direction: column;
		gap: var(--s-1);
	}

	.review__row + .review__row {
		padding-top: var(--s-3);
		border-top: 1px solid rgb(255 255 255 / 0.08);
	}

	.review__round {
		color: var(--ink-3);
		font-size: 0.68rem;
		font-weight: 700;
		letter-spacing: 0.08em;
		text-transform: uppercase;
	}

	.review__prompt {
		color: var(--ink);
		font-size: 0.95rem;
		font-weight: 600;
		line-height: 1.35;
	}

	.review__answers {
		display: grid;
		grid-template-columns: 1fr 1fr;
		gap: var(--s-2);
		margin: 0;
	}

	.review__answers dt {
		color: var(--ink-3);
		font-size: 0.68rem;
		font-weight: 700;
		letter-spacing: 0.06em;
		text-transform: uppercase;
	}

	.review__answers dd {
		margin: 0;
		color: var(--ink);
		font-size: 0.9rem;
		font-weight: 600;
	}

	.review__answers dd.is-missing {
		color: var(--ink-3);
		font-weight: 500;
	}

	.review__why {
		color: var(--ink-3);
		font-size: 0.85rem;
		line-height: 1.4;
	}
</style>

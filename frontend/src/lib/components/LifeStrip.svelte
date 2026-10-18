<script lang="ts">
	import { t } from '#lib/i18n';
	import Icon from './Icon.svelte';

	interface Props {
		lives: number;
		total?: number;
	}

	let { lives, total = 3 }: Props = $props();

	const cells = $derived(Array.from({ length: total }, (_, index) => index < lives));
</script>

<span
	class="lives"
	role="img"
	aria-label={t('arcade.lives_value', { n: Math.max(0, lives), total })}
>
	{#each cells as alive, index (index)}
		<span class="lives__heart" class:is-off={!alive}>
			<Icon name="heart" size={18} />
		</span>
	{/each}
</span>

<style>
	.lives {
		display: inline-flex;
		align-items: center;
		gap: 4px;
	}

	.lives__heart {
		display: inline-flex;
		color: var(--red-ink);
		filter: drop-shadow(0 2px 0 var(--red-edge));
		transition:
			opacity 0.18s ease,
			transform 0.18s ease,
			filter 0.18s ease;
	}

	.lives__heart.is-off {
		opacity: 0.22;
		transform: scale(0.82);
		filter: none;
	}

	@media (prefers-reduced-motion: reduce) {
		.lives__heart {
			transition: none;
		}
	}
</style>

<script lang="ts">
	import type { Category } from '#lib/categories';
	import CategoryBadge from './CategoryBadge.svelte';

	interface Props {
		category: Category;
		categoryLabel: string;
		prompt: string;
		/** Texto del esticker flotante (ej. "Responde"), o nada. */
		badge?: string;
	}

	let { category, categoryLabel, prompt, badge }: Props = $props();
</script>

<div class="question-card" data-cat={category}>
	{#if badge}<span class="responde-badge">{badge}</span>{/if}
	<CategoryBadge {category} label={categoryLabel} />
	<p class="question-card__prompt">{prompt}</p>
</div>

<script lang="ts">
	import type { Category } from '#lib/categories';
	import CategoryBadge from './CategoryBadge.svelte';

	interface Props {
		/** Vacío cuando el protocolo del modo no publica la categoría. */
		category?: Category;
		categoryLabel?: string;
		prompt: string;
		/** Texto del esticker flotante (ej. "Responde"), o nada. */
		badge?: string;
		/** Últimos segundos: el borde de la tarjeta late en rojo. */
		danger?: boolean;
	}

	let { category, categoryLabel, prompt, badge, danger = false }: Props = $props();
</script>

<div class="question-card" class:is-danger={danger} data-cat={category}>
	{#if badge}<span class="responde-badge">{badge}</span>{/if}
	{#if category && categoryLabel}<CategoryBadge {category} label={categoryLabel} />{/if}
	<p class="question-card__prompt">{prompt}</p>
</div>

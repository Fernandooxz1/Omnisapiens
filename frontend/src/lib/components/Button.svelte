<script lang="ts">
	import type { Snippet } from 'svelte';
	import type { HTMLButtonAttributes } from 'svelte/elements';

	type Variant = 'green' | 'blue' | 'slate';

	interface Props extends HTMLButtonAttributes {
		/** Color de la piel: verde (CTA), azul (secundario) o pizarra (neutro). */
		variant?: Variant;
		/** Destello diagonal en loop. Solo el modo principal. */
		sheen?: boolean;
		title: string;
		sub?: string;
		icon?: Snippet;
	}

	let {
		variant = 'green',
		sheen = false,
		title,
		sub,
		icon,
		class: className = '',
		...rest
	}: Props = $props();
</script>

<button
	type="button"
	class="btn btn--{variant} {className}"
	class:btn--sheen={sheen}
	{...rest}
>
	<span class="btn__title">
		{#if icon}{@render icon()}{/if}
		{title}
	</span>
	{#if sub}<span class="btn__sub">{sub}</span>{/if}
</button>

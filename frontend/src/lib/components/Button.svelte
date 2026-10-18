<script lang="ts">
	import type { Snippet } from 'svelte';
	import type { HTMLButtonAttributes } from 'svelte/elements';

	type Variant = 'green' | 'blue' | 'slate';

	interface Props extends HTMLButtonAttributes {
		/** Color del botón: verde (CTA), azul (secundario) o pizarra (neutro). */
		variant?: Variant;
		title: string;
		sub?: string;
		icon?: Snippet;
		/** Pastilla al extremo derecho (vidas del arcade, "VS" del duelo). */
		aside?: Snippet;
	}

	let {
		variant = 'green',
		title,
		sub,
		icon,
		aside,
		class: className = '',
		...rest
	}: Props = $props();
</script>

<button type="button" class="btn btn--{variant} {className}" class:btn--split={aside} {...rest}>
	<span class="btn__body">
		<span class="btn__title">
			{#if icon}{@render icon()}{/if}
			{title}
		</span>
		{#if sub}<span class="btn__sub">{sub}</span>{/if}
	</span>
	{#if aside}<span class="btn__aside">{@render aside()}</span>{/if}
</button>

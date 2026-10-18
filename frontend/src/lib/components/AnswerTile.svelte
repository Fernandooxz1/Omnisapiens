<script lang="ts">
	import type { HTMLButtonAttributes } from 'svelte/elements';

	export type TileState = 'idle' | 'selected' | 'correct' | 'wrong' | 'dim';

	interface Props extends HTMLButtonAttributes {
		/** Tecla visible 1–4. */
		keycap: string;
		label: string;
		state?: TileState;
	}

	let { keycap, label, state = 'idle', class: className = '', ...rest }: Props = $props();

	const locked = $derived(state === 'correct' || state === 'wrong' || state === 'dim');
</script>

<button
	type="button"
	class="tile is-{state} {className}"
	class:is-locked={locked}
	{...rest}
>
	<span class="tile__key">{keycap}</span>
	<span class="tile__label">{label}</span>
</button>

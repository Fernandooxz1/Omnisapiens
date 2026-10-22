<script lang="ts">
	import type { HTMLButtonAttributes } from 'svelte/elements';
	import { haptics } from '#lib/haptics';
	import Icon from './Icon.svelte';

	export type TileState = 'idle' | 'selected' | 'correct' | 'wrong' | 'dim';

	interface Props extends HTMLButtonAttributes {
		/** Tecla visible 1–4. */
		keycap: string;
		label: string;
		state?: TileState;
		/** Quién eligió esta opción; aparece al revelar. */
		tag?: string;
		mark?: 'correct' | 'wrong';
	}

	let { keycap, label, state = 'idle', tag, mark, class: className = '', ...rest }: Props =
		$props();

	const locked = $derived(state === 'correct' || state === 'wrong' || state === 'dim');
</script>

<button
	type="button"
	class="tile is-{state} {className}"
	class:is-locked={locked}
	{...rest}
	onpointerdown={() => {
		if (!locked) haptics.tap();
	}}
>
	<span class="tile__key">{keycap}</span>
	<span class="tile__label">{label}</span>
	{#if tag || mark}
		<span class="tile__side">
			{#if tag}<span class="tile__tag">{tag}</span>{/if}
			{#if mark}
				<span class="tile__mark">
					<Icon name={mark === 'correct' ? 'check' : 'x'} size={22} />
				</span>
			{/if}
		</span>
	{/if}
</button>

<script lang="ts">
	import type { Snippet } from 'svelte';
	import Icon from './Icon.svelte';

	interface Props {
		id: string;
		label: string;
		hint?: string;
		/** Muestra el badge verde de validación a la derecha. */
		valid?: boolean;
		value: string;
		/** Lo que va delante del campo, dentro del pozo (el avatar). */
		prefix?: Snippet;
	}

	let { id, label, hint, valid = false, value = $bindable(), prefix }: Props = $props();
</script>

<div class="field">
	<label class="field__label" for={id}>{label}</label>
	<div class="field__well">
		{#if prefix}{@render prefix()}{/if}
		<input
			{id}
			class="field__input"
			bind:value
			maxlength={16}
			autocomplete="off"
			spellcheck="false"
		/>
		{#if valid}
			<span class="field__ok">
				<Icon name="check" size={18} />
			</span>
		{/if}
	</div>
	{#if hint}<p class="field__hint">{hint}</p>{/if}
</div>

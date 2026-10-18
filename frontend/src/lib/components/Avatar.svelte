<script lang="ts">
	import Icon from './Icon.svelte';

	interface Props {
		nick: string;
		/** El propio jugador lleva el acento elegido; el rival, naranja fijo. */
		tone?: 'you' | 'rival';
		/** Corona al que va ganando. */
		crown?: boolean;
	}

	let { nick, tone = 'you', crown = false }: Props = $props();

	const initial = $derived(nick.trim().charAt(0).toUpperCase() || '?');
</script>

<span class="avatar avatar--{tone}" aria-hidden="true">
	{#if crown}
		<span class="avatar__crown"><Icon name="crown" size={20} /></span>
	{/if}
	{initial}
</span>

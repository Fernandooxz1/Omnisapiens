<script lang="ts">
	import { getEmblem } from '#lib/emblem.svelte';
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
	/** El emblema es del jugador de esta pestaña: el rival mantiene su avatar liso. */
	const emblem = $derived(tone === 'you' ? getEmblem() : null);
</script>

<span class="avatar avatar--{tone}" aria-hidden="true">
	{#if crown}
		<span class="avatar__crown"><Icon name="crown" size={20} /></span>
	{/if}
	{initial}
	{#if emblem}
		<span class="avatar__emblem"><Icon name={emblem} size={13} /></span>
	{/if}
</span>

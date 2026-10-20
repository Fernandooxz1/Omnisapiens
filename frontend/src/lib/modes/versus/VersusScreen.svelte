<script lang="ts">
	import VersusLobby from './VersusLobby.svelte';
	import VersusRoom from './VersusRoom.svelte';

	/** Sin código es el lobby (crear o entrar); con código, la sala. */
	let { code = null }: { code?: string | null } = $props();
</script>

{#if code}
	<VersusRoom {code} />
{:else}
	<VersusLobby />
{/if}

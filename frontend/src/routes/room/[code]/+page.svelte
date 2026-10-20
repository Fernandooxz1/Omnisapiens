<script lang="ts">
	import { page } from '$app/state';
	import VersusScreen from '#lib/modes/versus/VersusScreen.svelte';

	const code = $derived(page.params.code ?? '');
</script>

<VersusScreen {code} />

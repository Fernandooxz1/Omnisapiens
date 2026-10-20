<script lang="ts">
	import { goto } from '$app/navigation';
	import { page } from '$app/state';
	import Button from '#lib/components/Button.svelte';
	import { t } from '#lib/i18n';
	import ArcadeScreen from '#lib/modes/arcade/ArcadeScreen.svelte';
	import VersusScreen from '#lib/modes/versus/VersusScreen.svelte';
	import { modeEntry } from '#lib/modes/registry';

	/** El registry decide qué pantalla monta cada modo; el backend manda el catálogo. */
	const entry = $derived(modeEntry(page.params.mode ?? ''));
</script>

{#if entry?.renderer === 'arcade'}
	<ArcadeScreen />
{:else if entry?.renderer === 'versus'}
	<VersusScreen />
{:else}
	<section class="mode-missing">
		<h1 class="page-title">{t('play.mode_unknown')}</h1>
		<Button variant="slate" title={t('common.back')} onclick={() => goto('/')} />
	</section>
{/if}

<style>
	.mode-missing {
		display: flex;
		flex: 1;
		flex-direction: column;
		align-items: center;
		justify-content: center;
		gap: var(--s-4);
		text-align: center;
	}
</style>

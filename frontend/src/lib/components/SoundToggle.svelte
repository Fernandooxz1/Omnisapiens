<script lang="ts">
	import { t } from '#lib/i18n';
	import { sound } from '#lib/sound.svelte';
	import Icon from './Icon.svelte';

	const label = $derived(sound.muted ? t('sound.enable') : t('sound.mute'));
</script>

<button
	type="button"
	class="sound"
	aria-pressed={!sound.muted}
	aria-label={label}
	title={label}
	onclick={() => sound.toggle()}
>
	<Icon name={sound.muted ? 'sound-off' : 'sound-on'} size={22} />
</button>

<style>
	.sound {
		display: grid;
		place-items: center;
		width: 44px;
		height: 44px;
		padding: 0;
		border: 0;
		border-radius: var(--r-md);
		background: var(--panel-bg);
		box-shadow: 0 4px 0 var(--panel-edge);
		color: var(--ink-2);
		cursor: pointer;
		-webkit-tap-highlight-color: transparent;
		transition:
			transform 0.07s ease,
			box-shadow 0.07s ease,
			color 0.12s ease;
	}

	.sound:hover {
		color: var(--ink);
	}

	.sound:active {
		transform: translateY(3px);
		box-shadow: 0 1px 0 var(--panel-edge);
	}

	.sound[aria-pressed='false'] {
		color: var(--ink-3);
	}
</style>

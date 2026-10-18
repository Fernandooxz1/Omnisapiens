<script lang="ts">
	import { t } from '#lib/i18n';
	import Avatar from './Avatar.svelte';

	interface Props {
		nick?: string;
		/** El jugador de esta pestaña lleva el acento propio; el otro, naranja. */
		you?: boolean;
		empty?: boolean;
	}

	let { nick = '', you = false, empty = false }: Props = $props();
</script>

{#if empty}
	<div class="player-panel player-panel--empty">
		<span class="player-panel__slot" aria-hidden="true">?</span>
		<span class="player-panel__hint">{t('lobby.waiting_player')}</span>
	</div>
{:else}
	<div class="player-panel">
		<Avatar {nick} tone={you ? 'you' : 'rival'} />
		<span class="player-panel__lines">
			<span class="player-panel__nick">{nick}</span>
			<span class="player-panel__tag">{you ? t('lobby.you') : t('lobby.rival')}</span>
		</span>
	</div>
{/if}

<style>
	.player-panel {
		display: flex;
		align-items: center;
		gap: var(--s-3);
		padding: var(--s-3);
		border-radius: var(--r-md);
		background: var(--panel-bg);
		box-shadow: 0 4px 0 var(--panel-edge);
	}

	.player-panel--empty {
		border: 2px dashed var(--well-border);
		background: transparent;
		box-shadow: none;
	}

	.player-panel__slot {
		display: grid;
		place-items: center;
		flex: none;
		width: 44px;
		height: 44px;
		border-radius: 14px;
		background: var(--well-bg);
		color: var(--ink-3);
		font-family: var(--font-display);
		font-size: 1.2rem;
		font-weight: 700;
	}

	.player-panel__lines {
		display: flex;
		flex-direction: column;
		gap: 2px;
		min-width: 0;
	}

	.player-panel__nick {
		overflow: hidden;
		color: var(--ink);
		font-family: var(--font-display);
		font-size: 1.05rem;
		font-weight: 700;
		text-overflow: ellipsis;
		white-space: nowrap;
	}

	.player-panel__tag {
		color: var(--ink-3);
		font-size: 0.75rem;
		font-weight: 600;
		letter-spacing: 0.06em;
		text-transform: uppercase;
	}

	.player-panel__hint {
		color: var(--ink-3);
		font-family: var(--font-ui);
		font-size: 0.9rem;
		font-weight: 600;
	}
</style>

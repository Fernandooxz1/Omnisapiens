<script lang="ts">
	import { connection } from '#lib/api/connection.svelte';
	import { t } from '#lib/i18n';
</script>

{#if connection.down}
	<div class="connection" role="alert">
		<span class="connection__body">
			<strong>{t('connection.down')}</strong>
			<span>{t('connection.hint')}</span>
		</span>
		<button
			type="button"
			class="connection__retry"
			disabled={connection.probing}
			onclick={() => connection.retry()}
		>
			{connection.probing ? t('connection.retrying') : t('connection.retry')}
		</button>
	</div>
{/if}

<style>
	.connection {
		position: fixed;
		top: max(var(--s-3), env(safe-area-inset-top));
		left: 50%;
		z-index: 40;
		display: flex;
		align-items: center;
		gap: var(--s-3);
		width: min(calc(var(--shell-max) - 2 * var(--s-4)), calc(100% - 2 * var(--s-4)));
		padding: var(--s-2) var(--s-2) var(--s-2) var(--s-4);
		border-left: 4px solid var(--red);
		border-radius: var(--r-md);
		background: var(--panel-bg);
		box-shadow:
			0 4px 0 var(--panel-edge),
			0 10px 28px -12px rgb(0 0 0 / 0.7);
		transform: translateX(-50%);
	}

	.connection__body {
		display: flex;
		flex: 1;
		flex-direction: column;
		gap: 1px;
		min-width: 0;
	}

	.connection__body strong {
		color: var(--ink);
		font-family: var(--font-display);
		font-size: 0.95rem;
	}

	.connection__body span {
		color: var(--ink-3);
		font-size: 0.78rem;
	}

	.connection__retry {
		flex: none;
		min-height: 44px;
		padding: 0 var(--s-3);
		border: 0;
		border-radius: var(--r-sm);
		background: var(--red);
		box-shadow: 0 3px 0 var(--red-edge);
		color: #ffffff;
		font-family: var(--font-display);
		font-size: 0.85rem;
		font-weight: 700;
		cursor: pointer;
	}

	.connection__retry:active:not(:disabled) {
		box-shadow: 0 1px 0 var(--red-edge);
		transform: translateY(2px);
	}

	.connection__retry:disabled {
		cursor: default;
		opacity: 0.7;
	}
</style>

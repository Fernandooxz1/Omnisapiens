<script lang="ts">
	import { t } from '#lib/i18n';
	import { toast } from '#lib/toast.svelte';
	import Icon from './Icon.svelte';
</script>

{#if toast.items.length > 0}
	<div class="toasts" aria-label={t('toast.region')}>
		{#each toast.items as item (item.id)}
			<div class="toast" role="alert">
				<span class="toast__code">{item.code}</span>
				<p class="toast__message">{item.message}</p>
				<button
					type="button"
					class="toast__close"
					aria-label={t('toast.dismiss')}
					onclick={() => toast.dismiss(item.id)}
				>
					<Icon name="x" size={16} />
				</button>
			</div>
		{/each}
	</div>
{/if}

<style>
	.toasts {
		position: fixed;
		right: 0;
		bottom: max(var(--s-4), env(safe-area-inset-bottom));
		left: 0;
		z-index: 50;
		display: flex;
		flex-direction: column;
		gap: var(--s-2);
		width: min(calc(var(--shell-max) - 2 * var(--s-4)), calc(100% - 2 * var(--s-4)));
		margin-inline: auto;
		pointer-events: none;
	}

	.toast {
		display: flex;
		align-items: flex-start;
		gap: var(--s-2);
		padding: var(--s-2) var(--s-2) var(--s-2) var(--s-3);
		border-left: 4px solid var(--red);
		border-radius: var(--r-md);
		background: var(--panel-bg);
		box-shadow:
			0 4px 0 var(--panel-edge),
			0 10px 24px -12px rgb(0 0 0 / 0.7);
		pointer-events: auto;
		animation: toast-in 0.18s ease;
	}

	@keyframes toast-in {
		from {
			opacity: 0;
			transform: translateY(6px);
		}
	}

	.toast__code {
		flex: none;
		margin-top: 3px;
		padding: 3px 7px;
		border-radius: var(--r-sm);
		background: var(--well-bg);
		box-shadow: inset 0 2px 0 rgb(0 0 0 / 0.4);
		color: var(--red-ink);
		font-family: var(--font-ui);
		font-size: 0.66rem;
		font-weight: 700;
		letter-spacing: 0.04em;
	}

	.toast__message {
		flex: 1;
		padding-top: 2px;
		color: var(--ink-2);
		font-size: 0.85rem;
		line-height: 1.35;
		overflow-wrap: anywhere;
	}

	.toast__close {
		display: grid;
		flex: none;
		place-items: center;
		width: 44px;
		height: 44px;
		margin: -8px -6px -8px 0;
		padding: 0;
		border: 0;
		border-radius: var(--r-sm);
		background: transparent;
		color: var(--ink-3);
		cursor: pointer;
	}

	.toast__close:hover {
		color: var(--ink);
	}
</style>

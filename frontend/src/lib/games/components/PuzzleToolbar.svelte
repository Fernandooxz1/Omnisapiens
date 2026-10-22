<script lang="ts">
	import Icon from '#lib/components/Icon.svelte';
	import { t } from '#lib/i18n';

	interface Props {
		onMark: () => void;
		onUndo: () => void;
		onHint: () => void;
		onReset: () => void;
		markDisabled?: boolean;
		undoDisabled?: boolean;
		hintDisabled?: boolean;
		resetDisabled?: boolean;
	}

	let {
		onMark,
		onUndo,
		onHint,
		onReset,
		markDisabled = false,
		undoDisabled = false,
		hintDisabled = false,
		resetDisabled = false
	}: Props = $props();
</script>

<div class="tools" role="group" aria-label={t('games.tools_label')}>
	<button type="button" class="tool" onclick={onMark} disabled={markDisabled}>
		<span class="tool__icon"><Icon name="x" size={20} /></span>
		<span class="tool__label">{t('games.tool.mark')}</span>
	</button>

	<button type="button" class="tool" onclick={onUndo} disabled={undoDisabled}>
		<span class="tool__icon"><Icon name="undo" size={20} /></span>
		<span class="tool__label">{t('games.tool.undo')}</span>
	</button>

	<button type="button" class="tool" onclick={onHint} disabled={hintDisabled}>
		<span class="tool__icon"><Icon name="bulb" size={20} /></span>
		<span class="tool__label">{t('games.tool.hint')}</span>
	</button>

	<button type="button" class="tool" onclick={onReset} disabled={resetDisabled}>
		<span class="tool__icon"><Icon name="restart" size={20} /></span>
		<span class="tool__label">{t('games.tool.reset')}</span>
	</button>
</div>

<style>
	.tools {
		display: grid;
		grid-template-columns: repeat(4, minmax(0, 1fr));
		gap: var(--s-2);
	}

	.tool {
		display: flex;
		flex-direction: column;
		align-items: center;
		justify-content: center;
		gap: 3px;
		min-height: 60px;
		padding: var(--s-2) var(--s-1);
		border: 0;
		border-radius: var(--r-md);
		background: var(--panel-bg);
		box-shadow: 0 4px 0 var(--panel-edge);
		color: var(--ink-2);
		cursor: pointer;
		transition:
			transform 0.07s ease,
			box-shadow 0.07s ease,
			filter 0.15s ease;
	}

	.tool:hover:not(:disabled) {
		filter: brightness(1.06);
		transform: translateY(-1px);
	}

	.tool:active:not(:disabled) {
		transform: translateY(3px);
		box-shadow: 0 1px 0 var(--panel-edge);
	}

	.tool:disabled {
		cursor: not-allowed;
		filter: grayscale(0.5) opacity(0.55);
	}

	.tool__icon {
		display: inline-flex;
		color: var(--ink);
	}

	.tool__label {
		font-family: var(--font-ui);
		font-size: 0.72rem;
		font-weight: 700;
		letter-spacing: 0.02em;
		text-align: center;
	}
</style>

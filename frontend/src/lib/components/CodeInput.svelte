<script lang="ts">
	import { t } from '#lib/i18n';

	const LENGTH = 6;
	const ALPHABET = 'ABCDEFGHJKLMNPQRSTUVWXYZ23456789';

	interface Props {
		label: string;
		value?: string;
		error?: string;
		/** Se llama con el código completo, también al pegar. */
		oncomplete?: (code: string) => void;
	}

	let { label, value = $bindable(''), error, oncomplete }: Props = $props();

	let boxes: HTMLDivElement | undefined = $state();
	let chars = $state<string[]>(Array(LENGTH).fill(''));
	/** El código ya estaba completo: no se reenvía en cada tecla. */
	let complete = false;

	// Un código externo (o un reset del padre) se refleja en las casillas.
	$effect(() => {
		if (value !== chars.join('')) {
			const incoming = sanitize(value).slice(0, LENGTH).split('');
			chars = Array.from({ length: LENGTH }, (_, index) => incoming[index] ?? '');
		}
		complete = chars.every(Boolean);
	});

	function sanitize(raw: string): string {
		return [...raw.toUpperCase()].filter((char) => ALPHABET.includes(char)).join('');
	}

	function write(next: string[]): void {
		const wasComplete = complete;
		chars = next;
		value = next.join('');
		complete = next.every(Boolean);
		if (complete && !wasComplete) oncomplete?.(next.join(''));
	}

	function type(event: Event, index: number): void {
		const input = event.currentTarget as HTMLInputElement;
		const letter = sanitize(input.value).slice(-1);
		// El navegador ya pintó lo tecleado; si era inválido, se borra a mano.
		input.value = letter;

		const next = [...chars];
		next[index] = letter;
		write(next);
		if (letter) focus(index + 1);
	}

	function key(event: KeyboardEvent, index: number): void {
		if (event.key === 'Backspace') {
			event.preventDefault();
			const next = [...chars];
			if (next[index]) {
				next[index] = '';
				write(next);
			} else if (index > 0) {
				next[index - 1] = '';
				write(next);
				focus(index - 1);
			}
			return;
		}

		if (event.key === 'ArrowLeft') {
			event.preventDefault();
			focus(index - 1);
		} else if (event.key === 'ArrowRight') {
			event.preventDefault();
			focus(index + 1);
		} else if (event.key === 'Enter' && chars.every(Boolean)) {
			event.preventDefault();
			oncomplete?.(chars.join(''));
		}
	}

	function paste(event: ClipboardEvent): void {
		event.preventDefault();
		const pasted = sanitize(event.clipboardData?.getData('text') ?? '').slice(0, LENGTH);
		if (!pasted) return;

		write(Array.from({ length: LENGTH }, (_, index) => pasted[index] ?? ''));
		focus(Math.min(pasted.length, LENGTH - 1));
	}

	function focus(index: number): void {
		if (index < 0 || index >= LENGTH) return;
		const input = boxes?.querySelectorAll<HTMLInputElement>('input')[index];
		input?.focus();
		input?.select();
	}
</script>

<fieldset class="code">
	<legend class="code__label">{label}</legend>
	<div class="code__boxes" class:code__boxes--bad={!!error} bind:this={boxes} onpaste={paste}>
		{#each { length: LENGTH } as _, index (index)}
			<input
				class="code__box"
				value={chars[index]}
				maxlength={1}
				inputmode="text"
				autocomplete="one-time-code"
				autocapitalize="characters"
				spellcheck="false"
				aria-label={t('play.code_digit', { n: index + 1 })}
				oninput={(event) => type(event, index)}
				onkeydown={(event) => key(event, index)}
				onfocus={(event) => (event.currentTarget as HTMLInputElement).select()}
				onclick={(event) => (event.currentTarget as HTMLInputElement).select()}
			/>
		{/each}
	</div>
	{#if error}<p class="code__error" role="alert">{error}</p>{/if}
</fieldset>

<style>
	.code {
		display: flex;
		flex-direction: column;
		gap: var(--s-2);
		min-inline-size: 0;
		margin: 0;
		padding: 0;
		border: 0;
	}

	.code__label {
		padding: 0;
		color: var(--ink-3);
		font-family: var(--font-ui);
		font-size: 0.8125rem;
		font-weight: 600;
		letter-spacing: 0.06em;
		text-transform: uppercase;
	}

	.code__boxes {
		display: grid;
		grid-template-columns: repeat(6, minmax(0, 1fr));
		gap: var(--s-2);
	}

	.code__box {
		width: 100%;
		aspect-ratio: 1 / 1.08;
		padding: 0;
		border: 2px solid var(--well-border);
		border-radius: var(--r-md);
		background: var(--well-bg);
		box-shadow: inset 0 4px 0 rgb(0 0 0 / 0.45);
		color: var(--ink);
		font-family: var(--font-display);
		font-size: clamp(1.35rem, 7vw, 1.9rem);
		font-weight: 700;
		line-height: 1;
		text-align: center;
		text-transform: uppercase;
		caret-color: var(--yellow);
		outline: none;
	}

	.code__box:focus-visible {
		border-color: var(--focus-ring);
	}

	.code__boxes--bad .code__box {
		border-color: var(--red-ink);
	}

	.code__error {
		color: var(--red-ink);
		font-size: 0.8125rem;
		font-weight: 600;
	}
</style>

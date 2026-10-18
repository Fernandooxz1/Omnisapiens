<script lang="ts">
	import { ACCENTS, ACCENT_SWATCH, getAccent, isAccent, setAccent, type Accent } from '#lib/accent';
	import { t } from '#lib/i18n';

	interface Props {
		label: string;
	}

	let { label }: Props = $props();

	let current = $state<Accent>(getAccent());

	function pick(accent: Accent) {
		if (accent === current) return;
		current = accent;
		setAccent(accent);
	}

	// El DOM es la fuente de verdad: el bootstrap de app.html pudo haber elegido otro acento.
	$effect(() => {
		const value = document.documentElement.dataset.accent;
		if (isAccent(value) && value !== current) current = value;
	});
</script>

<div class="accent">
	<span class="accent__label">{label}</span>
	<div class="accent__list" role="group" aria-label={label}>
		{#each ACCENTS as accent (accent)}
			<button
				type="button"
				class="swatch"
				style="--swatch: {ACCENT_SWATCH[accent]}"
				aria-pressed={accent === current}
				aria-label={t(`accent.${accent}`)}
				onclick={() => pick(accent)}
			></button>
		{/each}
	</div>
</div>

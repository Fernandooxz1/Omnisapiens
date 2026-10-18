<script lang="ts">
	import { getSkin, isSkin, setSkin, SKINS } from '#lib/skin';
	import { t } from '#lib/i18n';

	interface Props {
		groupLabel: string;
	}

	let { groupLabel }: Props = $props();

	let current = $state(getSkin());

	function pick(skin: (typeof SKINS)[number]) {
		if (skin === current) return;
		current = skin;
		setSkin(skin);
	}

	const labels: Record<(typeof SKINS)[number], string> = {
		papel: t('home.skin_papel'),
		colorido: t('home.skin_colorido')
	};

	// El DOM es la fuente de verdad: el bootstrap de app.html pudo haber elegido otra piel.
	$effect(() => {
		const value = document.documentElement.dataset.skin;
		if (isSkin(value) && value !== current) current = value;
	});
</script>

<div class="skins" role="group" aria-label={groupLabel}>
	<span class="skins__label">{groupLabel}</span>
	{#each SKINS as skin (skin)}
		<button
			type="button"
			class="skin-chip"
			aria-pressed={skin === current}
			onclick={() => pick(skin)}
		>
			{labels[skin]}
			<svg
				class="skin-chip__check"
				width="14"
				height="14"
				viewBox="0 0 24 24"
				fill="none"
				aria-hidden="true"
			>
				<path
					d="M5 12.5 10 17.5 19 7"
					stroke="currentColor"
					stroke-width="2.5"
					stroke-linecap="round"
					stroke-linejoin="round"
				/>
			</svg>
		</button>
	{/each}
</div>

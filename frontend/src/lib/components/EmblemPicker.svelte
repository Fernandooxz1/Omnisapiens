<script lang="ts">
	import { EMBLEMS, getEmblem, setEmblem, type Emblem } from '#lib/emblem.svelte';
	import { t } from '#lib/i18n';
	import Icon from './Icon.svelte';

	interface Props {
		label: string;
	}

	let { label }: Props = $props();

	let current = $state<Emblem>(getEmblem());

	function pick(emblem: Emblem) {
		if (emblem === current) return;
		current = emblem;
		setEmblem(emblem);
	}
</script>

<div class="emblem">
	<span class="emblem__label">{label}</span>
	<div class="emblem__list" role="group" aria-label={label}>
		{#each EMBLEMS as emblem (emblem)}
			<button
				type="button"
				class="emblem__button"
				aria-pressed={emblem === current}
				aria-label={t(`emblem.${emblem}`)}
				onclick={() => pick(emblem)}
			>
				<Icon name={emblem} size={20} />
			</button>
		{/each}
	</div>
</div>

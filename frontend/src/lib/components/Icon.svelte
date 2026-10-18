<script lang="ts">
	type Name = 'check' | 'x' | 'arrow' | 'trophy';

	interface Props {
		name: Name;
		size?: number;
	}

	let { name, size = 20 }: Props = $props();
</script>

<svg width={size} height={size} viewBox="0 0 24 24" fill="none" aria-hidden="true">
	{#if name === 'check'}
		<path
			d="M5 12.5 10 17.5 19 7"
			stroke="currentColor"
			stroke-width="2.5"
			stroke-linecap="round"
			stroke-linejoin="round"
		/>
	{:else if name === 'x'}
		<path
			d="M7 7l10 10M17 7 7 17"
			stroke="currentColor"
			stroke-width="2.5"
			stroke-linecap="round"
			stroke-linejoin="round"
		/>
	{:else if name === 'arrow'}
		<path
			d="M5 12h14M13 6l6 6-6 6"
			stroke="currentColor"
			stroke-width="2.5"
			stroke-linecap="round"
			stroke-linejoin="round"
		/>
	{:else if name === 'trophy'}
		<path
			d="M7 4h10v4a5 5 0 0 1-10 0V4ZM5 5h2v3a3 3 0 0 1-2-3ZM19 5h-2v3a3 3 0 0 0 2-3ZM12 13v4M8 20h8M9 20a3 3 0 0 1 6 0"
			stroke="currentColor"
			stroke-width="2.5"
			stroke-linecap="round"
			stroke-linejoin="round"
		/>
	{/if}
</svg>

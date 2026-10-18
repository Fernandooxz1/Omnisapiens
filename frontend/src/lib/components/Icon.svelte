<script lang="ts">
	type Name =
		| 'check'
		| 'x'
		| 'arrow'
		| 'trophy'
		| 'crown'
		| 'heart'
		| 'clock'
		| 'sound-on'
		| 'sound-off';

	interface Props {
		name: Name;
		size?: number;
	}

	let { name, size = 20 }: Props = $props();

	/** Los macizos no llevan trazo: se pintan con `currentColor`. */
	const filled: Name[] = ['crown', 'heart'];
</script>

<svg
	width={size}
	height={size}
	viewBox="0 0 24 24"
	fill={filled.includes(name) ? 'currentColor' : 'none'}
	aria-hidden="true"
>
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
	{:else if name === 'crown'}
		<path d="M2 4l3 12h14l3-12-6 7-4-7-4 7-6-7zm3 16h14v2H5v-2z" />
	{:else if name === 'heart'}
		<path
			d="M12 21.35l-1.45-1.32C5.4 15.36 2 12.28 2 8.5 2 5.42 4.42 3 7.5 3c1.74 0 3.41.81 4.5 2.09C13.09 3.81 14.76 3 16.5 3 19.58 3 22 5.42 22 8.5c0 3.78-3.4 6.86-8.55 11.54L12 21.35z"
		/>
	{:else if name === 'clock'}
		<path
			d="M12 3a9 9 0 1 0 0 18 9 9 0 0 0 0-18ZM12 7v5.2l3.6 2.1"
			stroke="currentColor"
			stroke-width="2.5"
			stroke-linecap="round"
			stroke-linejoin="round"
		/>
	{:else if name === 'sound-on'}
		<path
			d="M4 9.5h3.2L12 5.5v13l-4.8-4H4v-5ZM15.5 8.5a5 5 0 0 1 0 7M18.3 6a8.5 8.5 0 0 1 0 12"
			stroke="currentColor"
			stroke-width="2.5"
			stroke-linecap="round"
			stroke-linejoin="round"
		/>
	{:else if name === 'sound-off'}
		<path
			d="M4 9.5h3.2L12 5.5v13l-4.8-4H4v-5ZM16 9.5l5 5M21 9.5l-5 5"
			stroke="currentColor"
			stroke-width="2.5"
			stroke-linecap="round"
			stroke-linejoin="round"
		/>
	{/if}
</svg>

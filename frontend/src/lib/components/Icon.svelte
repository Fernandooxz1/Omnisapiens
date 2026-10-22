<script module lang="ts">
	export type IconName =
		| 'check'
		| 'x'
		| 'arrow'
		| 'home'
		| 'grid'
		| 'case'
		| 'undo'
		| 'bulb'
		| 'restart'
		| 'trophy'
		| 'crown'
		| 'flame'
		| 'heart'
		| 'clock'
		| 'sound-on'
		| 'sound-off'
		| 'brain'
		| 'bolt'
		| 'glasses'
		| 'star';
</script>

<script lang="ts">
	interface Props {
		name: IconName;
		size?: number;
	}

	let { name, size = 20 }: Props = $props();

	/** Los macizos no llevan trazo: se pintan con `currentColor`. */
	const filled: IconName[] = ['crown', 'flame', 'heart', 'bolt', 'star'];
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
	{:else if name === 'home'}
		<path
			d="M4 11 12 4l8 7v8a1 1 0 0 1-1 1h-5v-6h-4v6H5a1 1 0 0 1-1-1v-8Z"
			stroke="currentColor"
			stroke-width="2.5"
			stroke-linecap="round"
			stroke-linejoin="round"
		/>
	{:else if name === 'grid'}
		<path
			d="M4 4h6v6H4V4Zm10 0h6v6h-6V4ZM4 14h6v6H4v-6Zm10 0h6v6h-6v-6Z"
			stroke="currentColor"
			stroke-width="2.5"
			stroke-linecap="round"
			stroke-linejoin="round"
		/>
	{:else if name === 'case'}
		<path
			d="M3 7.5A2.5 2.5 0 0 1 5.5 5H10l2 2.5h6.5A2.5 2.5 0 0 1 21 10v7a2.5 2.5 0 0 1-2.5 2.5h-13A2.5 2.5 0 0 1 3 17V7.5Z"
			stroke="currentColor"
			stroke-width="2.5"
			stroke-linecap="round"
			stroke-linejoin="round"
		/>
	{:else if name === 'undo'}
		<path
			d="M3.5 12a8.5 8.5 0 1 0 2.6-6.1M3.5 4.5v5h5"
			stroke="currentColor"
			stroke-width="2.5"
			stroke-linecap="round"
			stroke-linejoin="round"
		/>
	{:else if name === 'restart'}
		<path
			d="M20.5 12a8.5 8.5 0 1 1-2.6-6.1M20.5 4.5v5h-5"
			stroke="currentColor"
			stroke-width="2.5"
			stroke-linecap="round"
			stroke-linejoin="round"
		/>
	{:else if name === 'bulb'}
		<path
			d="M9.5 17.5h5M10.5 20.5h3M12 3a6 6 0 0 0-3.6 10.8V16h7.2v-2.2A6 6 0 0 0 12 3Z"
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
	{:else if name === 'flame'}
		<path
			d="M8.5 14.5A2.5 2.5 0 0 0 11 12c0-1.38-.5-2-1-3-1.07-2.14-.22-4.05 2-6 .5 2.5 2 4.9 4 6.5 2 1.6 3 3.5 3 5.5a7 7 0 1 1-14 0c0-1.15.43-2.29 1-3a2.5 2.5 0 0 0 2.5 2.5Z"
		/>
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
	{:else if name === 'brain'}
		<g fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
			<path
				d="M12 5.5a3 3 0 1 0-6 0 4 4 0 0 0-2.5 5.8A4 4 0 0 0 4 18a3.5 3.5 0 0 0 6 2.3V5.5Z"
			/>
			<path d="M12 5.5a3 3 0 1 1 6 0 4 4 0 0 1 2.5 5.8A4 4 0 0 1 20 18a3.5 3.5 0 0 1-6 2.3V5.5Z" />
		</g>
	{:else if name === 'bolt'}
		<path d="M13.5 2 4 14h6l-1.5 8L19 10h-6l.5-8Z" />
	{:else if name === 'glasses'}
		<path
			d="M3 9h18M4 9v2.5a3 3 0 0 0 6 0V9M14 9v2.5a3 3 0 0 0 6 0V9M10 10.5h4"
			fill="none"
			stroke="currentColor"
			stroke-width="2.2"
			stroke-linecap="round"
			stroke-linejoin="round"
		/>
	{:else if name === 'star'}
		<path d="m12 2.5 2.9 5.9 6.5.9-4.7 4.6 1.1 6.5-5.8-3-5.8 3 1.1-6.5L2.6 9.3l6.5-.9L12 2.5Z" />
	{/if}
</svg>

<script lang="ts">
	export type Category =
		| 'science'
		| 'geography'
		| 'history'
		| 'sports'
		| 'entertainment'
		| 'art';

	interface Props {
		category: Category;
		label: string;
	}

	let { category, label }: Props = $props();
</script>

<span class="cat-badge" data-cat={category}>{label}</span>

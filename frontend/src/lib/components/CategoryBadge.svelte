<script lang="ts">
	import type { Category } from '#lib/categories';

	interface Props {
		category: Category;
		label: string;
	}

	let { category, label }: Props = $props();
</script>

<span class="cat-badge" data-cat={category}>{label}</span>

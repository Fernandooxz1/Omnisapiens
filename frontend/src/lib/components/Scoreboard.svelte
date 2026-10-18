<script lang="ts">
	import { t } from '#lib/i18n';
	import Avatar from './Avatar.svelte';

	interface Player {
		nick: string;
		points: number;
	}

	interface Props {
		you: Player;
		rival: Player;
	}

	let { you, rival }: Props = $props();

	const youLead = $derived(you.points > rival.points);
	const rivalLead = $derived(rival.points > you.points);
</script>

<div class="scoreboard">
	<div class="score">
		<Avatar nick={you.nick} tone="you" crown={youLead} />
		<span class="score__lines">
			<span class="score__who">{you.nick}</span>
			<span class="score__points">{you.points}</span>
		</span>
	</div>
	<span class="scoreboard__vs">{t('play.vs')}</span>
	<div class="score score--right">
		<Avatar nick={rival.nick} tone="rival" crown={rivalLead} />
		<span class="score__lines">
			<span class="score__who">{rival.nick}</span>
			<span class="score__points">{rival.points}</span>
		</span>
	</div>
</div>

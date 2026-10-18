<script lang="ts">
	interface Player {
		nick: string;
		points: number;
	}

	interface Props {
		you: Player;
		rival: Player;
	}

	let { you, rival }: Props = $props();

	const initial = (nick: string) => nick.trim().charAt(0).toUpperCase() || '?';
</script>

<div class="scoreboard">
	<div class="score">
		<span class="avatar-token avatar-token--you" aria-hidden="true">{initial(you.nick)}</span>
		<span class="score__lines">
			<span class="score__who">{you.nick}</span>
			<span class="score__points">{you.points}</span>
		</span>
	</div>
	<span class="delta" aria-hidden="true">—</span>
	<div class="score score--right">
		<span class="avatar-token avatar-token--rival" aria-hidden="true">{initial(rival.nick)}</span>
		<span class="score__lines">
			<span class="score__who">{rival.nick}</span>
			<span class="score__points">{rival.points}</span>
		</span>
	</div>
</div>

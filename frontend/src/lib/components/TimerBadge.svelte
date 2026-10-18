<script lang="ts">
	interface Props {
		seconds: number;
		/** Últimos segundos: late y se pinta de rojo. */
		alert?: boolean;
		/** Fuera del turno de respuesta: se apaga. */
		idle?: boolean;
	}

	let { seconds, alert = false, idle = false }: Props = $props();
</script>

<span class="timer-badge" class:is-alert={alert} class:is-idle={idle} aria-hidden="true">
	{seconds}
</span>

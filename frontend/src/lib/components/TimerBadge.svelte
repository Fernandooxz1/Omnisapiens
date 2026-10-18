<script lang="ts">
	import { t } from '#lib/i18n';
	import Icon from './Icon.svelte';

	interface Props {
		seconds: number;
		/** Últimos segundos: late y se pinta de rojo. */
		alert?: boolean;
		/** Fuera del turno de respuesta: se apaga. */
		idle?: boolean;
	}

	let { seconds, alert = false, idle = false }: Props = $props();
</script>

<span class="timer-pill" class:is-alert={alert} class:is-idle={idle}>
	<Icon name="clock" size={16} />
	{t('play.timer', { n: seconds })}
</span>

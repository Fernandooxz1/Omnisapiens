import { browser } from '$app/env';
import { PUBLIC_API_URL } from '$app/env/public';

const base = PUBLIC_API_URL.replace(/\/+$/, '');
/** Con la API caída se sondea `/health` hasta que vuelva; el jugador no recarga. */
const POLL_MS = 4000;

function createConnection() {
	let down = $state(false);
	let probing = $state(false);
	let poll: ReturnType<typeof setInterval> | null = null;

	function stopPolling() {
		if (!poll) return;
		clearInterval(poll);
		poll = null;
	}

	async function probe(): Promise<boolean> {
		if (probing) return !down;

		probing = true;
		try {
			const response = await fetch(`${base}/health`, { cache: 'no-store' });
			if (!response.ok) return false;

			reachable();
			return true;
		} catch {
			return false;
		} finally {
			probing = false;
		}
	}

	function startPolling() {
		if (!browser || poll) return;
		poll = setInterval(() => void probe(), POLL_MS);
	}

	/** Cualquier respuesta HTTP, aunque sea un error, confirma que la API está en pie. */
	function reachable() {
		if (!down) return;
		down = false;
		stopPolling();
	}

	/** El `fetch` no llegó al servidor: red caída o API apagada. */
	function unreachable() {
		if (down) return;
		down = true;
		startPolling();
	}

	return {
		get down() {
			return down;
		},
		get probing() {
			return probing;
		},
		reachable,
		unreachable,
		retry: () => void probe()
	};
}

export const connection = createConnection();

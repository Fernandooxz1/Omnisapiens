import { ApiError, NETWORK_ERROR } from '#lib/api/client';

export interface Toast {
	id: number;
	code: string;
	message: string;
}

const MAX = 3;
const TTL_MS = 7000;

function createToasts() {
	let items = $state<Toast[]>([]);
	let next = 0;
	const timers = new Map<number, ReturnType<typeof setTimeout>>();

	function dismiss(id: number) {
		const timer = timers.get(id);
		if (timer) clearTimeout(timer);
		timers.delete(id);
		items = items.filter((item) => item.id !== id);
	}

	function push(code: string, message: string) {
		const id = ++next;
		items = [...items, { id, code, message }];

		// Lo más viejo se va primero: la pila nunca tapa la partida.
		while (items.length > MAX) {
			const dropped = items[0];
			const timer = timers.get(dropped.id);
			if (timer) clearTimeout(timer);
			timers.delete(dropped.id);
			items = items.slice(1);
		}

		timers.set(
			id,
			setTimeout(() => dismiss(id), TTL_MS)
		);
	}

	/**
	 * Error de la API con el código y el mensaje del servidor. La caída de red
	 * no se repite acá: ya la avisa la banda de conexión.
	 */
	function failure(error: unknown, fallback: string) {
		if (error instanceof ApiError) {
			if (error.code === NETWORK_ERROR) return;
			push(error.code, error.message);
			return;
		}
		push('UNKNOWN', fallback);
	}

	return {
		get items() {
			return items;
		},
		push,
		failure,
		dismiss
	};
}

export const toast = createToasts();

import { PUBLIC_API_URL } from '$app/env/public';
import { ApiError } from './client';

/** Envelope único del WebSocket: `{"t","id"?,"d"}` (`docs/api.md`). */
export interface Envelope {
	t: string;
	id?: string;
	d?: unknown;
}

export type SocketStatus = 'connecting' | 'open' | 'reconnecting' | 'closed';

export interface Socket {
	/** `false` = el canal no estaba abierto y el mensaje se descartó. */
	send(t: string, d?: unknown, id?: string): boolean;
	close(): void;
	readonly status: SocketStatus;
}

interface Handlers {
	onMessage: (message: Envelope) => void;
	onStatus?: (status: SocketStatus) => void;
	/** Canal listo, también al reconectar. */
	onOpen?: () => void;
	/** El servidor no deja entrar: token, sala, rate limit. No se reintenta. */
	onRejected?: (error: ApiError) => void;
}

interface Options extends Handlers {
	url: string;
	/** Lo que repinta el estado después de un corte; la sala usa `hello`. */
	resume?: string;
}

const HEARTBEAT_MS = 15_000;
const PONG_TIMEOUT_MS = 10_000;
const RETRY_MIN_MS = 500;
const RETRY_MAX_MS = 10_000;
/** Cierre con el que el servidor rechaza la entrada. */
const CLOSE_POLICY = 1008;
/** Reintentar esto golpea el rate limit o una sala que ya no existe. */
const FATAL_CODES = ['AUTH_REQUIRED', 'ROOM_NOT_FOUND', 'ROOM_FULL', 'RATE_LIMITED'];

function endpoint(path: string, token: string): string {
	const url = new URL(path, PUBLIC_API_URL);
	url.protocol = url.protocol === 'https:' ? 'wss:' : 'ws:';
	// El token viaja en la URL: la dirección no se loguea nunca.
	url.searchParams.set('token', token);
	return url.toString();
}

function parse(raw: unknown): Envelope | null {
	if (typeof raw !== 'string') return null;

	try {
		const message = JSON.parse(raw);
		return typeof message?.t === 'string' ? (message as Envelope) : null;
	} catch {
		return null;
	}
}

function fatal(message: Envelope): ApiError | null {
	if (message.t !== 'error') return null;

	const { code, message: text } = (message.d ?? {}) as { code?: string; message?: string };
	if (!code || !FATAL_CODES.includes(code)) return null;

	return new ApiError(CLOSE_POLICY, code, text ?? 'El servidor rechazó la conexión.');
}

function createSocket({ url, resume, onMessage, onStatus, onOpen, onRejected }: Options): Socket {
	let socket: WebSocket | null = null;
	let status: SocketStatus = 'closed';
	let attempts = 0;
	let retry: ReturnType<typeof setTimeout> | null = null;
	let heartbeat: ReturnType<typeof setInterval> | null = null;
	let deadline: ReturnType<typeof setTimeout> | null = null;
	/** El `resume` es solo para reconexiones: la primera conexión ya nace sincronizada. */
	let first = true;
	let stopped = false;

	function setStatus(next: SocketStatus) {
		if (status === next) return;
		status = next;
		onStatus?.(next);
	}

	function clearTimers() {
		if (retry) clearTimeout(retry);
		if (heartbeat) clearInterval(heartbeat);
		if (deadline) clearTimeout(deadline);
		retry = heartbeat = deadline = null;
	}

	function send(t: string, d?: unknown, id?: string): boolean {
		if (!socket || socket.readyState !== WebSocket.OPEN) {
			// Nada se encola: un `answer` de la ronda anterior al reconectar es `ROUND_MISMATCH`.
			return false;
		}

		const message: Envelope = { t };
		if (d !== undefined) message.d = d;
		if (id !== undefined) message.id = id;
		socket.send(JSON.stringify(message));
		return true;
	}

	function beat() {
		send('ping');
		// El canal mudo no cierra solo: sin `pong` a tiempo se da por caído.
		if (deadline) clearTimeout(deadline);
		deadline = setTimeout(() => {
			deadline = null;
			socket?.close();
		}, PONG_TIMEOUT_MS);
	}

	function stop(error: ApiError) {
		stopped = true;
		clearTimers();
		socket?.close();
		socket = null;
		setStatus('closed');
		onRejected?.(error);
	}

	function open() {
		setStatus(attempts === 0 ? 'connecting' : 'reconnecting');

		let connection: WebSocket;
		try {
			connection = new WebSocket(url);
		} catch {
			stop(new ApiError(CLOSE_POLICY, 'BAD_URL', 'No se pudo abrir el canal.'));
			return;
		}

		socket = connection;

		connection.onopen = () => {
			attempts = 0;
			setStatus('open');
			heartbeat = setInterval(beat, HEARTBEAT_MS);
			if (resume && !first) send(resume);
			first = false;
			onOpen?.();
		};

		connection.onmessage = (event) => {
			const message = parse(event.data);
			if (!message) return;

			// Todo mensaje prueba que el canal vive; el `pong` solo responde al ping.
			if (deadline) {
				clearTimeout(deadline);
				deadline = null;
			}
			if (message.t === 'pong') return;

			const rejection = fatal(message);
			if (rejection) {
				stop(rejection);
				return;
			}

			onMessage(message);
		};

		connection.onclose = (event) => {
			socket = null;
			clearTimers();

			if (stopped) {
				setStatus('closed');
				return;
			}

			if (event.code === CLOSE_POLICY) {
				stop(new ApiError(CLOSE_POLICY, 'REJECTED', 'El servidor rechazó la conexión.'));
				return;
			}

			attempts += 1;
			setStatus('reconnecting');
			retry = setTimeout(open, Math.min(RETRY_MIN_MS * 2 ** (attempts - 1), RETRY_MAX_MS));
		};
	}

	open();

	return {
		send,
		close() {
			stopped = true;
			clearTimers();
			socket?.close();
			socket = null;
			setStatus('closed');
		},
		get status() {
			return status;
		}
	};
}

/** Sala 1v1: al reconectar manda `hello` y espera el `room_state` completo. */
export function connectRoom(code: string, token: string, handlers: Handlers): Socket {
	return createSocket({
		...handlers,
		url: endpoint(`/ws/room/${encodeURIComponent(code)}`, token),
		resume: 'hello'
	});
}

/** Arcade: `start` vale una vez por conexión; para otra corrida se abre otra. */
export function connectArcade(token: string, handlers: Handlers): Socket {
	return createSocket({ ...handlers, url: endpoint('/ws/arcade', token) });
}

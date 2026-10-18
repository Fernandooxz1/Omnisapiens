import { PUBLIC_API_URL } from '$app/env/public';

/**
 * Falla del contrato (`{"error": {"code", "message"}}`). Se ramifica por `code`:
 * `message` es del servidor y puede cambiar.
 */
export class ApiError extends Error {
	readonly status: number;
	readonly code: string;

	constructor(status: number, code: string, message: string) {
		super(message);
		this.name = 'ApiError';
		this.status = status;
		this.code = code;
	}
}

/** `code` propio: no hay respuesta HTTP, el servidor no se alcanzó. */
export const NETWORK_ERROR = 'NETWORK';

const base = PUBLIC_API_URL.replace(/\/+$/, '');

interface RequestOptions {
	method?: 'GET' | 'POST' | 'PATCH' | 'DELETE';
	body?: unknown;
	/** Sin token la llamada va anónima. */
	token?: string | null;
}

/** Única salida HTTP del cliente: arma la URL, pone el `Bearer` y traduce el error. */
export async function request<T>(path: string, options: RequestOptions = {}): Promise<T> {
	const { method = 'GET', body, token } = options;
	let response: Response;

	try {
		response = await fetch(base + path, {
			method,
			headers: {
				...(body === undefined ? {} : { 'content-type': 'application/json' }),
				...(token ? { authorization: `Bearer ${token}` } : {})
			},
			body: body === undefined ? undefined : JSON.stringify(body)
		});
	} catch {
		throw new ApiError(0, NETWORK_ERROR, 'No se pudo conectar con el servidor.');
	}

	if (response.status === 204) return undefined as T;

	const payload = await response.json().catch(() => null);

	if (!response.ok) {
		throw new ApiError(
			response.status,
			payload?.error?.code ?? 'UNKNOWN',
			payload?.error?.message ?? response.statusText
		);
	}

	return payload as T;
}

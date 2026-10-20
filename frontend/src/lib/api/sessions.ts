import { request } from './client';

/** Sesión solo recién creada: el socket que la juega se abre después. */
export interface SoloSession {
	session_id: string;
	/** Ruta del backend; el cliente le pone el host y el esquema del resto de los sockets. */
	ws_url: string;
}

/**
 * Crea la partida solo. El catálogo manda: `mode` es el `code` de `GET /modes` y
 * `config` lo valida el `config_schema` de ese modo.
 */
export function createSoloSession(
	token: string,
	mode: string,
	config: Record<string, unknown> = {}
): Promise<SoloSession> {
	return request<SoloSession>('/sessions', {
		method: 'POST',
		token,
		body: { mode, config }
	});
}

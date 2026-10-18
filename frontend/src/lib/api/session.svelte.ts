import { browser } from '$app/env';
import { ApiError, request } from './client';
import type { AuthOut, Me, User } from './types';

/** El token vive solo en la pestaña: cerrarla es cerrar la sesión. */
const TOKEN_KEY = 'omni-token';

function readToken(): string | null {
	try {
		return browser ? sessionStorage.getItem(TOKEN_KEY) : null;
	} catch {
		return null;
	}
}

function writeToken(token: string | null): void {
	try {
		if (token) sessionStorage.setItem(TOKEN_KEY, token);
		else sessionStorage.removeItem(TOKEN_KEY);
	} catch {
		/* sin persistencia: la sesión igual vale mientras dure la pestaña */
	}
}

function createSession() {
	let token = $state<string | null>(readToken());
	let user = $state<User | null>(null);

	function apply(auth: AuthOut): User {
		token = auth.token;
		user = auth.user;
		writeToken(token);
		return auth.user;
	}

	/** Reconoce una pestaña recargada; sin token o sin red, la sesión queda anónima. */
	async function restore(): Promise<void> {
		if (!token || user) return;

		try {
			user = await request<Me>('/me', { token });
		} catch (error) {
			// El token se descarta solo si el servidor lo rechazó: sin red todavía sirve.
			if (error instanceof ApiError && error.status === 401) {
				token = null;
				writeToken(null);
			}
		}
	}

	/** Deja la sesión lista para jugar y devuelve el usuario vigente. */
	async function identify(nick: string): Promise<User> {
		const wanted = nick.trim();
		let current = user;

		if (!current) {
			// Con token válido el alta devuelve el mismo usuario; sin token crea al invitado.
			current = apply(
				await request<AuthOut>('/auth/guest', {
					method: 'POST',
					token,
					body: wanted ? { nick: wanted } : {}
				})
			);
		}

		// El alta ignora el nick cuando el token ya vale, así que el cambio va por `PATCH`.
		if (wanted && wanted !== current.nick) {
			current = apply(
				await request<AuthOut>('/me', { method: 'PATCH', token, body: { nick: wanted } })
			);
		}

		return current;
	}

	return {
		get user() {
			return user;
		},
		get token() {
			return token;
		},
		/** Hay token en la pestaña: la sesión existe aunque el perfil todavía no se leyó. */
		get active() {
			return token !== null;
		},
		restore,
		identify
	};
}

export const session = createSession();

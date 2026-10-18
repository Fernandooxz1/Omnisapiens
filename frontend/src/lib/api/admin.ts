import { browser } from '$app/env';
import { request } from './client';
import type {
	AdminFilters,
	AdminQuestionPage,
	ImportReport,
	QuestionStatus
} from './types';

/** El token del panel vive en la pestaña, nunca en el repo. */
const TOKEN_KEY = 'omni-admin-token';

export function readAdminToken(): string | null {
	try {
		return browser ? sessionStorage.getItem(TOKEN_KEY) : null;
	} catch {
		return null;
	}
}

export function writeAdminToken(token: string | null): void {
	try {
		if (token) sessionStorage.setItem(TOKEN_KEY, token);
		else sessionStorage.removeItem(TOKEN_KEY);
	} catch {
		/* sin persistencia: el token igual vale mientras dure la pestaña */
	}
}

/** Listado del banco con filtros y paginación; el servidor calcula `pages`. */
export function listQuestions(
	adminToken: string,
	filters: AdminFilters = {}
): Promise<AdminQuestionPage> {
	const params = new URLSearchParams();

	for (const [key, value] of Object.entries(filters)) {
		if (value !== undefined && value !== '') params.set(key, String(value));
	}

	const query = params.toString();
	return request<AdminQuestionPage>(`/admin/questions${query ? `?${query}` : ''}`, {
		adminToken
	});
}

/** Subida CSV/JSON; la respuesta es el mismo informe que imprime la CLI. */
export function importQuestions(
	adminToken: string,
	file: File,
	status: QuestionStatus
): Promise<ImportReport> {
	const form = new FormData();
	form.append('file', file);
	form.append('status', status);

	return request<ImportReport>('/admin/questions/import', {
		method: 'POST',
		form,
		adminToken
	});
}

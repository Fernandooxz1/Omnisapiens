import es from './es.json';

export type MessageKey = keyof typeof es;

/**
 * Única puerta de entrada a las cadenas visibles: un componente nunca escribe texto
 * literal y una clave inexistente falla en `svelte-check`, no en pantalla.
 */
export function t(key: MessageKey, vars?: Record<string, string | number>): string {
	const template = es[key];
	if (!vars) return template;
	return template.replace(/\{(\w+)\}/g, (match, name: string) =>
		name in vars ? String(vars[name]) : match
	);
}

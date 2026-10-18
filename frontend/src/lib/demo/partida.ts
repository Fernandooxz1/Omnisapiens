import type { Category } from '#lib/categories';

/**
 * Datos de ejemplo SOLO para revisar la pantalla de partida mientras no exista el
 * cliente WS (`docs/api.md`). Cuando llegue el servidor, esta carpeta se borra: el
 * cliente nunca calcula puntajes ni el resultado de una ronda, solo dibuja el estado.
 */

export const DEMO_YOU = 'Ana';
export const DEMO_RIVAL = 'Beto';
export const DEMO_POINTS = 133;
export const ROUND_SECONDS = 15;

export interface DemoRound {
	category: Category;
	prompt: string;
	options: [string, string, string, string];
	/** Índice de la opción correcta. */
	correct: number;
	/** Lo que eligió el rival (fijo, para poder mostrar la revelación). */
	rivalPick: number;
	explanation: string;
}

export const DEMO_ROUNDS: readonly DemoRound[] = [
	{
		category: 'science',
		prompt: '¿Cuál es el símbolo químico del oro?',
		options: ['Au', 'Ag', 'Fe', 'Or'],
		correct: 0,
		rivalPick: 1,
		explanation: 'Au viene del latín aurum. Ag es plata y Fe, hierro.'
	},
	{
		category: 'geography',
		prompt: '¿Cuál es la capital de Australia?',
		options: ['Sídney', 'Canberra', 'Melbourne', 'Perth'],
		correct: 1,
		rivalPick: 1,
		explanation: 'Canberra es la capital desde 1927; Sídney y Melbourne son las más pobladas.'
	},
	{
		category: 'history',
		prompt: '¿En qué año cayó el Muro de Berlín?',
		options: ['1985', '1989', '1991', '1993'],
		correct: 1,
		rivalPick: 3,
		explanation: 'El 9 de noviembre de 1989, tras 28 años en pie.'
	},
	{
		category: 'sports',
		prompt: '¿En qué estadio juega de local el Valencia CF?',
		options: ['Mestalla', 'La Cartuja', 'Santiago Bernabéu', 'Camp Nou'],
		correct: 0,
		rivalPick: 0,
		explanation: 'Mestalla, con capacidad para unos 49.000 espectadores.'
	}
];

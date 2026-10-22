import type { GameMeta } from './types';

/** Registro de juegos del hub: sumar uno es agregar una entrada acá. */
export const games: GameMeta[] = [
	{
		id: 'murdoku',
		route: '/juegos/murdoku',
		titleKey: 'games.murdoku.title',
		blurbKey: 'games.murdoku.blurb',
		icon: 'glasses',
		accent: 'purple',
		order: 1,
		caseCount: 62
	}
];

export function orderGames(list: GameMeta[] = games): GameMeta[] {
	return [...list].sort((a, b) => a.order - b.order);
}

export function findGame(id: string): GameMeta | undefined {
	return games.find((game) => game.id === id);
}

import { request } from './client';
import type { Leaderboard, LeaderboardPeriod, MyRanks } from './types';

/** Tabla pública del arcade. `limit` va de 1 a 100. */
export function leaderboard(period: LeaderboardPeriod, limit = 50): Promise<Leaderboard> {
	return request<Leaderboard>(`/leaderboard/arcade?period=${period}&limit=${limit}`);
}

/** Posición propia en los dos períodos. Requiere sesión. */
export function myRanks(token: string): Promise<MyRanks> {
	return request<MyRanks>('/leaderboard/arcade/me', { token });
}

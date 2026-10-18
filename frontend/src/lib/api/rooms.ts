import { request } from './client';
import type { RoomConfig, RoomCreated, RoomPreview } from './types';

/** Crea la sala; el `code` es lo único que el cliente necesita guardar. */
export function createRoom(token: string, config: RoomConfig): Promise<RoomCreated> {
	return request<RoomCreated>('/rooms', { method: 'POST', token, body: config });
}

/** Vista previa pública: sirve para validar el código y saber quién es el host. */
export function previewRoom(code: string): Promise<RoomPreview> {
	return request<RoomPreview>(`/rooms/${encodeURIComponent(code)}`);
}

# Fase 9 — Medios (**opcional**)

> Rol: **backend + frontend**. "Adivina la canción" / "adivina la película".
> Depende de: fase 8 (o de la 7 si el rosco no se hizo). Al terminar, tag
> `refactor-fase-9`.

**Gate de entrada:** la primera tarea pregunta:
"La fase 9 (medios) es opcional y depende de una decisión de licencias. ¿La hacemos,
la dejamos para después o cerramos el refactor acá?"

---

### 9.1 — `media_assets` y almacenamiento

**Rol:** backend · **Depende de:** 8.5 (o 7.3) · **Sesión:** 1

**Leé:**
- `docs/plan-refactor/diseno.md` §6.2
- `backend/app/models/content.py`
- `backend/app/config.py`

**Hacé:**
- Crear `backend/app/models/media.py` con `MediaAsset`: kind (audio/image/video),
  storage_key, duration_ms, mime, license, attribution, timestamps.
- Migración `0006_media.py` (o el número que corresponda si 0006 se usó para dropear
  tablas; en ese caso, renumerar y actualizar `estado.md`).
- Adaptador de storage: local (`backend/media/`) en desarrollo; interfaz para S3/MinIO
  en producción. El `storage_key` es un UUID opaco, **nunca** el título.
- Endpoint de lectura con URL pública/opaca; no se expone `license` si no hace falta.
- Tests: mime/duración válidos, clave opaca, archivo inexistente.

**No toques:** `frontend/`, el contenido todavía.

**Verificá:** `make lint && make cov && make check-schema`.

**Documentá:** `docs/api.md` §medios y `docs/backend.md`.

**Commit:** `feat(media): add media assets and storage`

**Hecho cuando:** un clip de prueba se sube/registra y se sirve por una URL sin la
respuesta en el nombre.

---

### 9.2 — `ContentKind` de canción y película

**Rol:** backend · **Depende de:** 9.1 · **Sesión:** 1

**Leé:**
- `backend/app/game/modes/quiz/`
- `backend/app/game/modes/rosco/` (si existe)
- `docs/plan-refactor/diseno.md` §3.2

**Hacé:**
- Crear `backend/app/game/modes/song/` y `movie/` (o un `media_quiz` compartido si la
  forma es idéntica; elegir una y documentar por qué).
- `payload`: `{v, media_asset_id, duration_ms, clue?}`; `solution`: `{title, artist?,
  alternatives}`.
- `parse_row`: acepta el archivo de medios + metadatos; valida mime/duración.
- `grade`: normaliza título/artista (sin acentos, sin artículo, sin mayúsculas).
- Registrar `song_solo` y `movie_solo` con `ranking=None` en la v1.
- Tests: alternativa válida, título con acentos, archivo faltante, dedupe.

**No toques:** `frontend/`.

**Verificá:** `make lint && make cov`.

**Documentá:** `docs/api.md` §contenido con medios y `docs/plan.md`.

**Commit:** `feat(media): add song and movie content kinds`

**Hecho cuando:** un clip y una imagen se importan y se corrigen sin filtrar la
respuesta.

---

### 9.3 — Pantalla con audio/imagen

**Rol:** frontend · **Depende de:** 9.2 · **Sesión:** 1

**Leé:**
- `frontend/src/lib/modes/registry.ts`
- `frontend/src/routes/play/[mode]/+page.svelte`
- `frontend/src/lib/sound.svelte.ts`
- `docs/diseno.md`

**Hacé:**
- Renderer de medios: `<audio>`/`<img>` con play/pause, volumen, mute y reintento.
- Entrada de texto o elección según `input` del modo.
- El reloj y el puntaje siguen viniendo del servidor; el cliente no adelanta el
  resultado.
- E2E: una canción de prueba hasta el resultado y un error de carga del medio.

**No toques:** `backend/`.

**Verificá:** `npm run check && npm run build && npm run test:e2e`.

**Documentá:** `docs/frontend.md` y `docs/plan.md`.

**Commit:** `feat(media): add the audio and image renderer`

**Hecho cuando:** un modo con medios se juega desde la home y la e2e lo cubre.

---

### 9.4 — Licencias, catálogo y cierre

**Rol:** backend · **Depende de:** 9.3 · **Sesión:** 1

**Leé:**
- `docs/plan-refactor/diseno.md` §6.2
- `docs/plan.md`
- `docs/api.md`

**Hacé:**
- Documentar en `docs/plan.md` la decisión de catálogo (dominio público / CC /
  licencia), atribución y qué pasa con los clips.
- Confirmar que `song_solo`/`movie_solo` no tienen ranking (o activarlo con una
  decisión explícita).
- Actualizar `docs/api.md`, `docs/backend.md`, `docs/frontend.md`, `estado.md`.
- Verificación completa.

**No toques:** código de juego; esta tarea solo decide catálogo y cierra docs.

**Verificá:** `make lint && make cov && make check-schema` y
`npm run check && npm run build && npm run test:e2e`.

**Documentá:** `docs/plan.md`, `docs/api.md`, `docs/backend.md`, `docs/frontend.md` y
`estado.md`.

**Commit:** `docs(media): record the catalog and licensing decision`

**Hecho cuando:** la decisión está escrita, los modos con medios no tienen ranking por
defecto y las e2e pasan.

**Cierre de fase:** `git tag refactor-fase-9`.

/* Banco de pruebas del backend. Sin framework ni build: solo el API y dos WebSocket.
   La página vive en :5173 y el API en :8000 (origen ya permitido por CORS). */

const API_BASE = "http://localhost:8000";
const WS_BASE = API_BASE.replace(/^http/, "ws");
const LETTERS = ["A", "B", "C", "D"];

const $ = (id) => document.getElementById(id);

// ---------------------------------------------------------------------------
// Sesión: sessionStorage y no localStorage. Cada pestaña es un invitado distinto;
// con localStorage las dos pestañas del 1v1 serían el mismo jugador.
// ---------------------------------------------------------------------------

const session = {
  token: sessionStorage.getItem("omni.token"),
  user: readStored("omni.user"),
  hostCode: sessionStorage.getItem("omni.hostCode"),
};

function readStored(key) {
  try {
    return JSON.parse(sessionStorage.getItem(key) || "null");
  } catch {
    return null;
  }
}

function saveSession() {
  if (session.token && session.user) {
    sessionStorage.setItem("omni.token", session.token);
    sessionStorage.setItem("omni.user", JSON.stringify(session.user));
  }
  if (session.hostCode) sessionStorage.setItem("omni.hostCode", session.hostCode);
  else sessionStorage.removeItem("omni.hostCode");
}

function clearSession() {
  session.token = null;
  session.user = null;
  session.hostCode = null;
  for (const key of ["omni.token", "omni.user", "omni.hostCode"]) {
    sessionStorage.removeItem(key);
  }
}

// ---------------------------------------------------------------------------
// HTTP
// ---------------------------------------------------------------------------

async function api(path, { method = "GET", body, auth = true } = {}) {
  const headers = {};
  if (body !== undefined) headers["Content-Type"] = "application/json";
  if (auth && session.token) headers.Authorization = `Bearer ${session.token}`;

  let response;
  try {
    response = await fetch(API_BASE + path, {
      method,
      headers,
      body: body === undefined ? undefined : JSON.stringify(body),
    });
  } catch {
    throw new Error(
      `No se pudo hablar con el API en ${API_BASE}. ¿Está corriendo make api?`,
    );
  }

  if (response.status === 204) return null;

  const text = await response.text();
  let data = null;
  if (text) {
    try {
      data = JSON.parse(text);
    } catch {
      data = null;
    }
  }

  if (!response.ok) {
    const detail = data?.error;
    const error = new Error(detail?.message || `HTTP ${response.status}`);
    error.code = detail?.code;
    error.status = response.status;
    throw error;
  }
  return data;
}

function errorText(error) {
  return error.code ? `${error.code}: ${error.message}` : error.message;
}

// ---------------------------------------------------------------------------
// Avisos y log crudo
// ---------------------------------------------------------------------------

let noticeTimer = null;

function notice(message, kind = "info") {
  const box = $("notice");
  box.textContent = message;
  box.className = `notice notice--${kind}`;
  box.hidden = false;
  clearTimeout(noticeTimer);
  noticeTimer = setTimeout(
    () => {
      box.hidden = true;
    },
    kind === "error" ? 9000 : 5000,
  );
}

function log(direction, payload) {
  const stamp = new Date().toLocaleTimeString("es-AR", { hour12: false });
  const line = `${stamp} ${direction} ${JSON.stringify(payload)}`;
  const pre = $("log");
  pre.textContent += line + "\n";
  // El log es de depuración, no un archivo: se recorta para no crecer sin fin.
  if (pre.textContent.length > 60000) {
    pre.textContent = pre.textContent.slice(-40000);
  }
  pre.scrollTop = pre.scrollHeight;
}

// ---------------------------------------------------------------------------
// Autenticación y modos
// ---------------------------------------------------------------------------

let currentMode = "sala";

function renderAuth() {
  const logged = Boolean(session.token && session.user);
  $("login-view").hidden = logged;
  $("modes").hidden = !logged;
  $("app").hidden = !logged;

  if (logged) {
    $("who").textContent = `${session.user.nick} · ${String(session.user.id).slice(0, 8)}`;
    if (!$("code-input").value) $("code-input").value = session.hostCode || "";
    selectMode(currentMode);
  } else {
    $("who").textContent = "Sin entrar";
  }
}

function selectMode(mode) {
  currentMode = mode;
  for (const button of document.querySelectorAll("[data-mode]")) {
    const active = button.dataset.mode === mode;
    button.classList.toggle("is-active", active);
    button.setAttribute("aria-pressed", String(active));
  }
  $("mode-sala").hidden = mode !== "sala";
  $("mode-arcade").hidden = mode !== "arcade";
  if (mode === "arcade") refreshBoard();
}

async function onLogin(event) {
  event.preventDefault();
  const nick = $("nick-input").value.trim();
  if (!nick) return;
  const button = event.target.querySelector("button[type=submit]");
  button.disabled = true;
  try {
    const data = await api("/auth/guest", {
      method: "POST",
      body: { nick },
      auth: false,
    });
    session.token = data.token;
    session.user = data.user;
    session.hostCode = null;
    saveSession();
    $("nick-input").value = "";
    renderAuth();
    notice(`Entraste como ${data.user.nick}.`, "ok");
  } catch (error) {
    notice(errorText(error), "error");
  } finally {
    button.disabled = false;
  }
}

function onLogout() {
  closeRoom(true);
  closeArcadeSocket();
  clearSession();
  renderAuth();
  notice("Sesión cerrada en esta pestaña.", "info");
}

// ---------------------------------------------------------------------------
// Sala 1v1
// ---------------------------------------------------------------------------

const room = {
  seq: 0,
  ws: null,
  connected: false,
  code: null,
  isHost: false,
  me: null,
  players: [],
  status: null,
  config: null,
  round: null,
  totalRounds: null,
  scores: { you: 0, opponent: 0 },
  locked: true,
  answeredRound: null,
  ended: null,
  rematchRequested: false,
  clockTimer: null,
  pingTimer: null,
};

function connectRoom(code) {
  if (!code) return;
  closeRoom(false);

  Object.assign(room, {
    code,
    isHost: session.hostCode === code,
    me: null,
    players: [],
    status: "connecting",
    config: null,
    round: null,
    totalRounds: null,
    scores: { you: 0, opponent: 0 },
    locked: true,
    answeredRound: null,
    ended: null,
    rematchRequested: false,
  });

  $("lobby").hidden = true;
  $("room-view").hidden = false;
  $("room-code").textContent = code;
  $("question").hidden = true;
  $("last-result").hidden = true;
  $("room-end").hidden = true;
  $("options").textContent = "";
  $("clock").textContent = "";
  setRoomStatus("Conectando...");

  const seq = ++room.seq;
  const ws = new WebSocket(
    `${WS_BASE}/ws/room/${encodeURIComponent(code)}?token=${encodeURIComponent(session.token)}`,
  );
  room.ws = ws;
  renderRoom();

  ws.onopen = () => {
    if (seq !== room.seq) return;
    room.connected = true;
    setRoomStatus("Conectado. Pidiendo el estado de la sala...");
    // `hello` repinta el estado y, si la partida está en curso, la ronda con su
    // `ends_at` actualizado. Es lo que hace que reconectar no pierda el reloj.
    sendRoom({ t: "hello" });
    clearInterval(room.pingTimer);
    room.pingTimer = setInterval(() => {
      sendRoom({ t: "ping", id: String(Date.now()) });
    }, 15000);
    renderRoom();
  };

  ws.onmessage = (event) => {
    if (seq !== room.seq) return;
    let message;
    try {
      message = JSON.parse(event.data);
    } catch {
      log("RX", event.data);
      return;
    }
    log("RX", message);
    onRoomMessage(message);
  };

  ws.onclose = () => {
    if (seq !== room.seq) return;
    room.ws = null;
    room.connected = false;
    clearInterval(room.pingTimer);
    room.pingTimer = null;
    stopRoomClock();
    setRoomStatus(
      "Se cortó la conexión. Reconectá dentro de la gracia de 20 s para seguir.",
    );
    renderRoom();
  };

  ws.onerror = () => {
    if (seq === room.seq) log("WS", "error de socket");
  };
}

function closeRoom(reset) {
  room.seq += 1;
  if (room.ws) {
    const ws = room.ws;
    room.ws = null;
    try {
      ws.close(1000, "cerrar");
    } catch {
      // El socket ya estaba cerrado: no hay nada que hacer.
    }
  }
  clearInterval(room.pingTimer);
  room.pingTimer = null;
  room.connected = false;
  stopRoomClock();
  if (!reset) return;

  Object.assign(room, {
    code: null,
    isHost: false,
    me: null,
    players: [],
    status: null,
    config: null,
    round: null,
    totalRounds: null,
    scores: { you: 0, opponent: 0 },
    locked: true,
    answeredRound: null,
    ended: null,
    rematchRequested: false,
  });
  $("lobby").hidden = false;
  $("room-view").hidden = true;
  $("room-code").textContent = "------";
  $("room-badge").textContent = "Sin conectar";
  $("room-badge").removeAttribute("data-state");
  $("room-players").textContent = "";
  $("question").hidden = true;
  $("last-result").hidden = true;
  $("room-end").hidden = true;
  $("options").textContent = "";
  $("clock").textContent = "";
  $("scorebar").hidden = true;
  setRoomStatus("");
  renderRoom();
}

function sendRoom(message) {
  if (!room.ws || room.ws.readyState !== WebSocket.OPEN) {
    notice("No hay conexión con la sala.", "error");
    return false;
  }
  log("TX", message);
  room.ws.send(JSON.stringify(message));
  return true;
}

function onRoomMessage(message) {
  const data = message.d || {};

  switch (message.t) {
    case "room_state": {
      room.me = data.you;
      room.players = data.players || [];
      room.status = data.status;
      room.config = data.config;
      if (data.status === "waiting") {
        setRoomStatus(
          room.players.length < 2
            ? "Esperando al otro jugador..."
            : "Los dos conectados. El host puede arrancar.",
        );
      } else if (data.status === "playing") {
        setRoomStatus("Partida en curso.");
      } else if (data.status === "finished") {
        setRoomStatus("Partida terminada.");
        if (!room.ended) showRoomEndFallback();
      }
      renderRoom();
      break;
    }

    case "match_start":
      room.status = "playing";
      room.totalRounds = data.rounds_total;
      room.ended = null;
      room.rematchRequested = false;
      room.locked = true;
      room.scores = { you: 0, opponent: 0 };
      $("room-end").hidden = true;
      $("last-result").hidden = true;
      $("question").hidden = true;
      setRoomStatus(`Partida en curso: ${data.rounds_total} rondas.`);
      renderRoom();
      break;

    case "round_start":
      room.status = "playing";
      room.round = data;
      room.locked = false;
      room.answeredRound = null;
      showRoomQuestion(data);
      break;

    case "opponent_answered":
      setRoomStatus(`El rival respondió: ${roundName(data.round)}.`);
      break;

    case "round_result":
      room.locked = true;
      room.scores = data.scores;
      showRoomResult(data);
      renderRoom();
      break;

    case "match_end":
      room.status = "finished";
      room.ended = data;
      room.locked = true;
      stopRoomClock();
      $("question").hidden = true;
      $("options").textContent = "";
      $("last-result").hidden = true;
      showRoomEnd(data);
      setRoomStatus("Partida terminada.");
      renderRoom();
      break;

    case "reconnect_pending":
      // El servidor pausa el reloj de la ronda: no se responde contra el reloj
      // mientras el rival está en gracia, pero el que quedó sí puede contestar.
      stopRoomClock();
      setRoomStatus(
        `El rival se desconectó: ${data.seconds_left} s de gracia. El reloj está en pausa.`,
      );
      break;

    case "opponent_returned":
      setRoomStatus("El rival volvió. Retomando el reloj...");
      // El `ends_at` local quedó viejo por la pausa: `hello` trae la ronda nueva.
      sendRoom({ t: "hello" });
      break;

    case "rematch_waiting":
      setRoomStatus("El rival quiere revancha.");
      break;

    case "error":
      notice(`${data.code}: ${data.message}`, "error");
      setRoomStatus(`Error: ${data.message}`);
      if (["ROOM_FULL", "ROOM_NOT_FOUND", "AUTH_REQUIRED"].includes(data.code)) {
        setTimeout(() => closeRoom(true), 10);
      }
      break;

    default:
      break;
  }
}

function renderRoom() {
  $("room-code").textContent = room.code || "------";

  const state = room.connected
    ? room.status || "waiting"
    : room.ws
      ? "connecting"
      : "offline";
  const badge = $("room-badge");
  badge.dataset.state = state;
  badge.textContent =
    {
      connecting: "Conectando",
      waiting: "Esperando",
      playing: "Jugando",
      finished: "Terminada",
      offline: "Desconectado",
    }[state] || state;

  const players = $("room-players");
  players.textContent = "";
  for (const player of room.players) {
    const chip = document.createElement("span");
    chip.className = "player";
    const mine = room.me && player.id === room.me.id;
    if (mine) chip.classList.add("is-me");
    chip.textContent = mine ? `${player.nick} (vos)` : player.nick;
    players.append(chip);
  }
  const count = document.createElement("span");
  count.className = "player";
  count.textContent = `${room.players.length}/2`;
  players.append(count);

  const rival = room.players.find((player) => !room.me || player.id !== room.me.id);
  $("score-them-nick").textContent = rival ? rival.nick : "Rival";
  $("score-you").textContent = room.scores.you;
  $("score-them").textContent = room.scores.opponent;
  $("scorebar").hidden = !room.connected || !(
    room.status === "playing" ||
    (room.status === "finished" && room.ended)
  );

  const waiting = room.status === "waiting";
  const finished = room.status === "finished";

  $("room-start").hidden = !(room.isHost && waiting && room.connected);
  $("room-start").disabled = room.players.length !== 2;

  $("room-rematch").hidden = !(finished && room.connected);
  $("room-rematch").disabled = room.rematchRequested;
  $("room-rematch").textContent = room.rematchRequested
    ? "Esperando revancha"
    : "Revancha";

  $("room-reconnect").hidden = room.connected;
}

function setRoomStatus(text) {
  $("room-status").textContent = text;
}

function showRoomQuestion(data) {
  $("question").hidden = false;
  $("q-category").textContent = data.category;
  $("q-difficulty").textContent = `Dificultad ${data.difficulty}`;
  $("q-round").textContent =
    room.totalRounds && data.round < room.totalRounds
      ? `${roundName(data.round)} de ${room.totalRounds}`
      : roundName(data.round);
  $("q-prompt").textContent = data.prompt;
  paintOptions($("options"), data.options, (index) => answerRoom(data.round, index));
  startRoomClock(data.ends_at);
  setRoomStatus("");
}

function answerRoom(roundIndex, choice) {
  if (!room.connected || room.locked || room.answeredRound === roundIndex) return;
  room.locked = true;
  room.answeredRound = roundIndex;
  $("options").classList.add("is-locked");
  markPick($("options"), choice);
  $("last-result").hidden = true;
  if (sendRoom({ t: "answer", d: { round: roundIndex, choice } })) {
    setRoomStatus(`Respuesta enviada (${letter(choice)}). Esperando al rival...`);
  } else {
    room.locked = false;
    room.answeredRound = null;
    $("options").classList.remove("is-locked");
  }
}

function showRoomResult(data) {
  stopRoomClock();
  $("options").classList.add("is-locked");
  markAnswer($("options"), data.correct_index, data.you.choice);

  const box = $("last-result");
  box.hidden = false;
  box.textContent = "";

  const title = document.createElement("h3");
  title.textContent = `${roundName(data.round)}: la correcta era ${letter(data.correct_index)}`;
  box.append(title);

  const correctText = room.round?.options?.[data.correct_index];
  if (correctText) {
    const line = document.createElement("p");
    line.className = "line";
    line.textContent = `${letter(data.correct_index)}) ${correctText}`;
    box.append(line);
  }

  const line = document.createElement("p");
  line.className = "line";
  line.textContent = `Vos: ${describeChoice(data.you, room.round)} · Rival: ${describeChoice(data.opponent, room.round)}`;
  box.append(line);

  const score = document.createElement("p");
  score.className = "line";
  score.textContent = `Puntaje: ${data.scores.you} a ${data.scores.opponent}`;
  box.append(score);

  if (data.explanation) {
    const explanation = document.createElement("p");
    explanation.className = "line muted";
    explanation.textContent = data.explanation;
    box.append(explanation);
  }
}

function showRoomEnd(data) {
  const end = $("room-end");
  end.hidden = false;
  end.textContent = "";

  const title = document.createElement("h3");
  title.textContent =
    data.winner === "you"
      ? "Ganaste"
      : data.winner === "opponent"
        ? "Ganó el rival"
        : "Empate";
  end.append(title);

  const score = document.createElement("p");
  score.className = "line";
  score.textContent = `Puntaje final: ${data.scores.you} a ${data.scores.opponent}`;
  end.append(score);

  const reason = document.createElement("p");
  reason.className = "line muted";
  reason.textContent =
    data.reason === "abandoned"
      ? "Terminó por abandono: alguien no volvió dentro de la gracia."
      : "Partida completa.";
  end.append(reason);

  if (data.rounds?.length) {
    const list = document.createElement("div");
    list.className = "round-list";
    for (const round of data.rounds) {
      const row = document.createElement("div");
      row.textContent = `${roundName(round.round)}: vos ${round.you.points} · rival ${round.opponent.points}`;
      list.append(row);
    }
    end.append(list);
  }
}

function showRoomEndFallback() {
  const end = $("room-end");
  end.hidden = false;
  end.textContent = "";
  const title = document.createElement("h3");
  title.textContent = "La partida ya terminó";
  const line = document.createElement("p");
  line.className = "line muted";
  line.textContent =
    "Al reconectar no se reenvía el resumen; el historial queda en GET /me. Podés pedir revancha.";
  end.append(title, line);
}

function startRoomClock(endsAt) {
  stopRoomClock();
  const clock = $("clock");
  const tick = () => {
    const seconds = Math.max(0, Math.ceil((endsAt - Date.now()) / 1000));
    clock.textContent = seconds > 0 ? `${seconds} s` : "Tiempo";
    clock.classList.toggle("is-low", seconds <= 5);
    if (seconds <= 0) {
      room.locked = true;
      $("options").classList.add("is-locked");
    }
  };
  tick();
  room.clockTimer = setInterval(tick, 200);
}

function stopRoomClock() {
  clearInterval(room.clockTimer);
  room.clockTimer = null;
}

async function onCreateRoom(event) {
  event.preventDefault();
  const button = event.target.querySelector("button[type=submit]");
  button.disabled = true;
  try {
    const data = await api("/rooms", {
      method: "POST",
      body: {
        rounds: Number($("rounds").value),
        seconds: Number($("seconds").value),
      },
    });
    session.hostCode = data.code;
    saveSession();
    connectRoom(data.code);
    notice(`Sala ${data.code} creada. Compartí el código.`, "ok");
  } catch (error) {
    notice(errorText(error), "error");
  } finally {
    button.disabled = false;
  }
}

async function onJoinRoom(event) {
  event.preventDefault();
  const code = $("code-input").value.trim().toUpperCase();
  if (!code) return;
  const button = event.target.querySelector("button[type=submit]");
  button.disabled = true;
  try {
    const preview = await api(`/rooms/${encodeURIComponent(code)}`);
    $("code-input").value = "";
    connectRoom(preview.code);
    notice(
      `Sala ${preview.code} de ${preview.host_nick || "un invitado"} (${preview.status}).`,
      "ok",
    );
  } catch (error) {
    notice(errorText(error), "error");
  } finally {
    button.disabled = false;
  }
}

// ---------------------------------------------------------------------------
// Arcade
// ---------------------------------------------------------------------------

const arcade = {
  seq: 0,
  ws: null,
  connected: false,
  running: false,
  locked: true,
  round: null,
  answeredRound: null,
  clockTimer: null,
  pingTimer: null,
};

function startArcade() {
  if (!session.token) {
    notice("Entrá primero.", "error");
    return;
  }
  closeArcadeSocket();
  resetArcadeView();
  $("arcade-start").disabled = true;
  $("arcade-start").textContent = "Jugando";
  setArcadeStatus("Conectando...");

  arcade.running = false;
  arcade.locked = true;
  arcade.round = null;
  arcade.answeredRound = null;

  const seq = ++arcade.seq;
  const ws = new WebSocket(
    `${WS_BASE}/ws/arcade?token=${encodeURIComponent(session.token)}`,
  );
  arcade.ws = ws;

  ws.onopen = () => {
    if (seq !== arcade.seq) return;
    arcade.connected = true;
    sendArcade({ t: "start" });
    clearInterval(arcade.pingTimer);
    arcade.pingTimer = setInterval(() => {
      sendArcade({ t: "ping", id: String(Date.now()) });
    }, 15000);
  };

  ws.onmessage = (event) => {
    if (seq !== arcade.seq) return;
    let message;
    try {
      message = JSON.parse(event.data);
    } catch {
      log("RX", event.data);
      return;
    }
    log("RX", message);
    onArcadeMessage(message);
  };

  ws.onclose = () => {
    if (seq !== arcade.seq) return;
    arcade.ws = null;
    arcade.connected = false;
    arcade.running = false;
    clearInterval(arcade.pingTimer);
    arcade.pingTimer = null;
    stopArcadeClock();
    $("arcade-start").disabled = false;
    $("arcade-start").textContent = "Jugar";
    if (!$("arcade-end").hidden) return;
    setArcadeStatus("Se cortó la conexión. La corrida no se puede retomar.");
  };

  ws.onerror = () => {
    if (seq === arcade.seq) log("WS", "error de socket");
  };
}

function closeArcadeSocket() {
  arcade.seq += 1;
  if (arcade.ws) {
    const ws = arcade.ws;
    arcade.ws = null;
    try {
      ws.close(1000, "cerrar");
    } catch {
      // Ya estaba cerrado.
    }
  }
  clearInterval(arcade.pingTimer);
  arcade.pingTimer = null;
  arcade.connected = false;
  stopArcadeClock();
}

function sendArcade(message) {
  if (!arcade.ws || arcade.ws.readyState !== WebSocket.OPEN) {
    notice("No hay conexión con el arcade.", "error");
    return false;
  }
  log("TX", message);
  arcade.ws.send(JSON.stringify(message));
  return true;
}

function onArcadeMessage(message) {
  const data = message.d || {};

  switch (message.t) {
    case "arcade_start":
      arcade.running = true;
      arcade.locked = true;
      updateArcadeStats({ lives: data.lives, score: 0, streak: 0, correct_count: 0 });
      $("arcade-stats").hidden = false;
      setArcadeStatus(`Corrida ${String(data.run_id).slice(0, 8)} · ${data.lives} vidas.`);
      break;

    case "arcade_question":
      arcade.round = data;
      arcade.locked = false;
      arcade.answeredRound = null;
      showArcadeQuestion(data);
      break;

    case "arcade_result":
      arcade.locked = true;
      stopArcadeClock();
      updateArcadeStats(data);
      showArcadeResult(data);
      break;

    case "arcade_end":
      arcade.running = false;
      arcade.locked = true;
      stopArcadeClock();
      $("arcade-question").hidden = true;
      $("arcade-last").hidden = true;
      $("a-options").textContent = "";
      $("a-clock").textContent = "";
      showArcadeEnd(data);
      setArcadeStatus("Corrida terminada.");
      $("arcade-start").disabled = false;
      $("arcade-start").textContent = "Jugar otra vez";
      closeArcadeSocket();
      refreshBoard();
      break;

    case "error":
      notice(`${data.code}: ${data.message}`, "error");
      break;

    default:
      break;
  }
}

function resetArcadeView() {
  $("arcade-stats").hidden = true;
  $("arcade-question").hidden = true;
  $("arcade-last").hidden = true;
  $("arcade-end").hidden = true;
  $("a-options").textContent = "";
  $("a-clock").textContent = "";
  setArcadeStatus("Tocá Jugar para abrir una corrida nueva.");
}

function showArcadeQuestion(data) {
  $("arcade-question").hidden = false;
  $("a-category").textContent = data.category;
  $("a-difficulty").textContent = `Dificultad ${data.difficulty}`;
  $("a-round").textContent = `Ronda ${data.round + 1}`;
  $("a-prompt").textContent = data.prompt;
  paintOptions($("a-options"), data.options, (index) =>
    answerArcade(data.round, index),
  );
  updateArcadeStats(data);
  startArcadeClock(data.ends_at);
  setArcadeStatus("");
}

function answerArcade(roundIndex, choice) {
  if (!arcade.connected || arcade.locked || arcade.answeredRound === roundIndex) {
    return;
  }
  arcade.locked = true;
  arcade.answeredRound = roundIndex;
  $("a-options").classList.add("is-locked");
  markPick($("a-options"), choice);
  if (sendArcade({ t: "answer", d: { round: roundIndex, choice } })) {
    setArcadeStatus("Respuesta enviada.");
  } else {
    arcade.locked = false;
    arcade.answeredRound = null;
    $("a-options").classList.remove("is-locked");
  }
}

function showArcadeResult(data) {
  const box = $("arcade-last");
  box.hidden = false;
  box.textContent = "";
  box.classList.toggle("is-ok", Boolean(data.you.correct));
  box.classList.toggle("is-bad", !data.you.correct);

  const title = document.createElement("h3");
  if (data.you.choice === null || data.you.choice === undefined) {
    title.textContent = `Ronda ${data.round + 1}: sin respuesta`;
  } else {
    title.textContent = data.you.correct
      ? `Ronda ${data.round + 1}: correcta`
      : `Ronda ${data.round + 1}: incorrecta`;
  }
  box.append(title);

  const correctText = arcade.round?.options?.[data.correct_index];
  const correct = document.createElement("p");
  correct.className = "line";
  correct.textContent = `La correcta era ${letter(data.correct_index)}${correctText ? `) ${correctText}` : ""}`;
  box.append(correct);

  const mine = document.createElement("p");
  mine.className = "line";
  mine.textContent = `Vos: ${describeChoice(data.you, arcade.round)}`;
  box.append(mine);

  const totals = document.createElement("p");
  totals.className = "line";
  totals.textContent = `Puntaje ${data.score} · vidas ${data.lives} · racha ${data.streak}`;
  box.append(totals);

  if (data.explanation) {
    const explanation = document.createElement("p");
    explanation.className = "line muted";
    explanation.textContent = data.explanation;
    box.append(explanation);
  }
}

function showArcadeEnd(data) {
  const end = $("arcade-end");
  end.hidden = false;
  end.textContent = "";

  const title = document.createElement("h3");
  title.textContent = "Corrida terminada";
  end.append(title);

  const summary = document.createElement("p");
  summary.className = "line";
  summary.textContent = `Puntaje ${data.score} · ${data.correct_count} correctas · racha máxima ${data.longest_streak} · dificultad máxima ${data.max_difficulty}`;
  end.append(summary);

  const ranks = document.createElement("p");
  ranks.className = "line";
  ranks.textContent = `Global ${data.rank_global ? `#${data.rank_global}` : "sin posición"} · Semanal ${data.rank_weekly ? `#${data.rank_weekly}` : "sin posición"}`;
  end.append(ranks);

  if (data.personal_best !== null && data.personal_best !== undefined) {
    const best = document.createElement("p");
    best.className = "line";
    best.textContent = data.is_new_best
      ? `Nuevo récord personal: ${data.personal_best}`
      : `Mejor personal: ${data.personal_best}`;
    end.append(best);
  }
}

function updateArcadeStats(data) {
  if (data.lives !== undefined) $("a-lives").textContent = data.lives;
  if (data.score !== undefined) $("a-score").textContent = data.score;
  if (data.streak !== undefined) $("a-streak").textContent = data.streak;
  if (data.correct_count !== undefined) $("a-correct").textContent = data.correct_count;
}

function startArcadeClock(endsAt) {
  stopArcadeClock();
  const clock = $("a-clock");
  const tick = () => {
    const seconds = Math.max(0, Math.ceil((endsAt - Date.now()) / 1000));
    clock.textContent = seconds > 0 ? `${seconds} s` : "Tiempo";
    clock.classList.toggle("is-low", seconds <= 3);
    if (seconds <= 0) {
      arcade.locked = true;
      $("a-options").classList.add("is-locked");
    }
  };
  tick();
  arcade.clockTimer = setInterval(tick, 200);
}

function stopArcadeClock() {
  clearInterval(arcade.clockTimer);
  arcade.clockTimer = null;
}

function setArcadeStatus(text) {
  $("arcade-status").textContent = text;
}

// ---------------------------------------------------------------------------
// Ranking
// ---------------------------------------------------------------------------

let boardPeriod = "all";

async function refreshBoard() {
  try {
    const data = await api(`/leaderboard/arcade?period=${boardPeriod}&limit=10`, {
      auth: false,
    });
    renderBoard(data.entries);
  } catch (error) {
    notice(errorText(error), "error");
  }
}

function renderBoard(entries) {
  const body = $("board-body");
  body.textContent = "";

  if (!entries.length) {
    const row = document.createElement("tr");
    const cell = document.createElement("td");
    cell.colSpan = 4;
    cell.className = "empty";
    cell.textContent = "Todavía no hay corridas en este período.";
    row.append(cell);
    body.append(row);
    return;
  }

  for (const entry of entries) {
    const row = document.createElement("tr");
    if (entry.nick === session.user?.nick) row.classList.add("is-me");

    const position = document.createElement("td");
    position.className = "num";
    position.textContent = entry.position;

    const nick = document.createElement("td");
    nick.textContent = entry.nick;

    const score = document.createElement("td");
    score.className = "score";
    score.textContent = entry.score;

    const when = document.createElement("td");
    when.className = "date";
    when.textContent = new Date(entry.achieved_at).toLocaleString("es-AR", {
      dateStyle: "short",
      timeStyle: "short",
    });

    row.append(position, nick, score, when);
    body.append(row);
  }
}

// ---------------------------------------------------------------------------
// Piezas compartidas
// ---------------------------------------------------------------------------

function paintOptions(container, options, onPick) {
  container.textContent = "";
  options.forEach((text, index) => {
    const button = document.createElement("button");
    button.type = "button";
    button.className = "juicy-btn juicy-btn--slate option";

    const key = document.createElement("span");
    key.className = "key";
    key.textContent = letter(index);

    const label = document.createElement("span");
    label.className = "label";
    label.textContent = text;

    button.append(key, label);
    button.addEventListener("click", () => onPick(index));
    container.append(button);
  });
  container.classList.remove("is-locked");
}

function markPick(container, choice) {
  [...container.children].forEach((button, index) => {
    button.classList.toggle("is-picked", index === choice);
  });
}

function markAnswer(container, correctIndex, chosenIndex) {
  [...container.children].forEach((button, index) => {
    button.classList.remove("is-correct", "is-wrong", "is-picked");
    if (index === correctIndex) button.classList.add("is-correct");
    else if (index === chosenIndex) button.classList.add("is-wrong");
  });
}

function describeChoice(choice, question) {
  if (!choice || choice.choice === null || choice.choice === undefined) {
    return "sin responder";
  }
  const text = question?.options?.[choice.choice];
  const label = `${letter(choice.choice)}${text ? `) ${text}` : ""}`;
  return `${label} · +${choice.points}`;
}

function letter(index) {
  return LETTERS[index] || "?";
}

function roundName(index) {
  if (room.totalRounds && index >= room.totalRounds) {
    return `Desempate ${index - room.totalRounds + 1}`;
  }
  return `Ronda ${index + 1}`;
}

function onKey(event) {
  if (event.ctrlKey || event.metaKey || event.altKey) return;
  if (event.target instanceof HTMLInputElement) return;
  if (event.target instanceof HTMLSelectElement) return;

  const choice = ["1", "2", "3", "4"].indexOf(event.key);
  if (choice === -1) return;

  if (!$("mode-sala").hidden && room.round && !room.locked) {
    event.preventDefault();
    answerRoom(room.round.round, choice);
  } else if (!$("mode-arcade").hidden && arcade.round && !arcade.locked) {
    event.preventDefault();
    answerArcade(arcade.round.round, choice);
  }
}

// ---------------------------------------------------------------------------
// Arranque
// ---------------------------------------------------------------------------

async function boot() {
  if (session.token) {
    try {
      session.user = await api("/me");
      saveSession();
    } catch (error) {
      if (error.status === 401) {
        clearSession();
        notice("La sesión venció. Entrá de nuevo.", "error");
      } else {
        notice(errorText(error), "error");
      }
    }
  }
  renderAuth();
  if (!session.user) $("nick-input").focus();
}

for (const button of document.querySelectorAll("[data-mode]")) {
  button.addEventListener("click", () => selectMode(button.dataset.mode));
}

for (const button of document.querySelectorAll("[data-period]")) {
  button.addEventListener("click", () => {
    boardPeriod = button.dataset.period;
    for (const other of document.querySelectorAll("[data-period]")) {
      const active = other === button;
      other.classList.toggle("juicy-btn--slate", !active);
      other.setAttribute("aria-pressed", String(active));
    }
    refreshBoard();
  });
}

$("login-form").addEventListener("submit", onLogin);
$("logout").addEventListener("click", onLogout);
$("create-form").addEventListener("submit", onCreateRoom);
$("join-form").addEventListener("submit", onJoinRoom);
$("room-start").addEventListener("click", () => {
  if (sendRoom({ t: "start" })) setRoomStatus("Arrancando la partida...");
});
$("room-rematch").addEventListener("click", () => {
  if (room.rematchRequested) return;
  room.rematchRequested = true;
  if (sendRoom({ t: "rematch" })) {
    setRoomStatus("Revancha pedida. Esperando al rival...");
  } else {
    room.rematchRequested = false;
  }
  renderRoom();
});
$("room-reconnect").addEventListener("click", () => {
  if (room.code) connectRoom(room.code);
});
$("room-leave").addEventListener("click", () => {
  closeRoom(true);
  notice("Saliste de la sala.", "info");
});
$("arcade-start").addEventListener("click", startArcade);
$("log-clear").addEventListener("click", () => {
  $("log").textContent = "";
});
document.addEventListener("keydown", onKey);

boot();

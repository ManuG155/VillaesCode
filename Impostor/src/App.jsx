import { useState, useRef, useCallback, useEffect } from "react";

// ─── DATA LOADING ──────────────────────────────────────────────────────────────
const rawModules = import.meta.glob('./assets/data/tematicas/*.json', { eager: true });
const ALL_THEMES = Object.values(rawModules).map((mod) => mod.default ?? mod);

// ─── HELPERS ───────────────────────────────────────────────────────────────────

/**
 * Fisher-Yates (Knuth) shuffle — O(n), sin sesgo estadístico.
 * Muta una COPIA del array, nunca el original.
 */
function fisherYates(arr) {
  const a = [...arr];
  for (let i = a.length - 1; i > 0; i--) {
    const j = Math.floor(Math.random() * (i + 1));
    [a[i], a[j]] = [a[j], a[i]];
  }
  return a;
}

const pickRandom = (arr) => arr[Math.floor(Math.random() * arr.length)];

/**
 * Normaliza el nombre de una categoría leído del JSON:
 * primera letra en mayúscula, el resto en minúscula.
 * Evita que palabras como "ANATOMÍA" o "HISTORIA" se vean en caps.
 */
const normalizeCategory = (str) =>
  str.charAt(0).toUpperCase() + str.slice(1).toLowerCase();

/**
 * Construye el estado de una partida completa.
 * Usa Fisher-Yates para asignar roles sin ningún patrón predecible.
 */
function buildGame(players, impostorCount, selectedThemes, hintsEnabled) {
  // 1. Pool de palabras de las temáticas seleccionadas
  const pool = selectedThemes.flatMap((t) => t.contenido);
  const chosen = pickRandom(pool);

  // 2. Barajar jugadores con Fisher-Yates
  const shuffledPlayers = fisherYates(players);

  // 3. Seleccionar índices de impostores: barajar índices y tomar los N primeros
  const shuffledIndices = fisherYates([...Array(shuffledPlayers.length).keys()]);
  const impostorIndices = new Set(shuffledIndices.slice(0, impostorCount));

  // 4. Asignar roles
  const roles = shuffledPlayers.map((name, i) => ({
    name,
    isImpostor: impostorIndices.has(i),
  }));

  return { word: chosen.palabra, hint: chosen.pista, roles, hintsEnabled };
}

// ─── SCREEN CONSTANTS ──────────────────────────────────────────────────────────
const SCREEN = {
  SETUP:       "SETUP",
  PASS:        "PASS",
  REVEAL:      "REVEAL",
  START_ROUND: "START_ROUND",
  END:         "END",
};

// Umbral de arrastre para considerar el swipe válido (30% de la altura de pantalla)
const SWIPE_THRESHOLD_RATIO = 0.3;

// ─── ICONS ─────────────────────────────────────────────────────────────────────
const IconPlus = () => (
  <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth={2.5} className="w-5 h-5">
    <path strokeLinecap="round" strokeLinejoin="round" d="M12 4v16m8-8H4" />
  </svg>
);
const IconMinus = () => (
  <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth={2.5} className="w-5 h-5">
    <path strokeLinecap="round" strokeLinejoin="round" d="M4 12h16" />
  </svg>
);
const IconX = () => (
  <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth={2.5} className="w-4 h-4">
    <path strokeLinecap="round" strokeLinejoin="round" d="M6 18L18 6M6 6l12 12" />
  </svg>
);
const IconSkull = () => (
  <svg viewBox="0 0 24 24" fill="currentColor" className="w-5 h-5">
    <path d="M12 2a9 9 0 0 1 9 9c0 3.18-1.65 5.97-4.14 7.6L16 21H8l.14-2.4A9 9 0 0 1 3 11 9 9 0 0 1 12 2zm-2.5 9a1.5 1.5 0 1 0 0-3 1.5 1.5 0 0 0 0 3zm5 0a1.5 1.5 0 1 0 0-3 1.5 1.5 0 0 0 0 3zm-3 3h1l.5 2h-2l.5-2z" />
  </svg>
);
const IconCheck = () => (
  <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth={2.5} className="w-4 h-4">
    <path strokeLinecap="round" strokeLinejoin="round" d="M5 13l4 4L19 7" />
  </svg>
);
const IconChevronUp = ({ size = 28, opacity = 1 }) => (
  <svg
    viewBox="0 0 24 24"
    fill="none"
    stroke="currentColor"
    strokeWidth={2.5}
    width={size}
    height={size}
    style={{ opacity }}
  >
    <path strokeLinecap="round" strokeLinejoin="round" d="M5 15l7-7 7 7" />
  </svg>
);

// ─── SHARED UI COMPONENTS ──────────────────────────────────────────────────────

function GlowButton({ children, onClick, variant = "primary", className = "", disabled = false }) {
  const base =
    "font-bold tracking-widest uppercase text-sm px-6 py-3 rounded-xl " +
    "transition-all duration-200 active:scale-95 " +
    "disabled:opacity-40 disabled:cursor-not-allowed select-none";

  const variants = {
    primary: "bg-violet-600 hover:bg-violet-500 text-white border border-violet-400/30 " +
             "shadow-[0_0_18px_rgba(139,92,246,0.4)]",
    danger:  "bg-rose-700 hover:bg-rose-600 text-white border border-rose-400/30 " +
             "shadow-[0_0_18px_rgba(225,29,72,0.4)]",
    ghost:   "bg-white/5 hover:bg-white/10 text-slate-300 border border-white/10 hover:border-white/20",
  };

  return (
    <button
      onClick={onClick}
      disabled={disabled}
      className={`${base} ${variants[variant]} ${className}`}
    >
      {children}
    </button>
  );
}

function Toggle({ checked, onChange }) {
  return (
    <button
      type="button"
      role="switch"
      aria-checked={checked}
      onClick={() => onChange(!checked)}
      className={`relative w-12 h-6 rounded-full transition-colors duration-250 cursor-pointer shrink-0 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-violet-500 ${
        checked ? "bg-violet-500" : "bg-slate-700"
      }`}
    >
      <span
        className={`absolute top-1 left-1 w-4 h-4 rounded-full bg-white shadow transition-transform duration-250 ${
          checked ? "translate-x-6" : "translate-x-0"
        }`}
      />
    </button>
  );
}

function PlayerChip({ name, onRemove }) {
  return (
    <div className="flex items-center gap-2 bg-slate-700/80 border border-slate-600/60 rounded-lg px-3 py-2 text-sm text-slate-200 font-medium">
      <span className="truncate max-w-[120px]">{name}</span>
      <button
        onClick={onRemove}
        aria-label={`Eliminar ${name}`}
        className="text-slate-500 hover:text-rose-400 transition-colors shrink-0"
      >
        <IconX />
      </button>
    </div>
  );
}

function Counter({ value, onInc, onDec, min, max }) {
  return (
    <div className="flex items-center gap-3">
      <button
        onClick={onDec}
        disabled={value <= min}
        aria-label="Reducir"
        className="w-9 h-9 rounded-lg bg-slate-700 border border-slate-600 flex items-center justify-center
                   text-slate-300 hover:text-white hover:border-slate-500 transition-all
                   disabled:opacity-30 active:scale-90"
      >
        <IconMinus />
      </button>
      <span className="w-8 text-center text-2xl font-bold text-white tabular-nums">{value}</span>
      <button
        onClick={onInc}
        disabled={value >= max}
        aria-label="Aumentar"
        className="w-9 h-9 rounded-lg bg-slate-700 border border-slate-600 flex items-center justify-center
                   text-slate-300 hover:text-white hover:border-slate-500 transition-all
                   disabled:opacity-30 active:scale-90"
      >
        <IconPlus />
      </button>
    </div>
  );
}

// Card sin backdrop-blur (pesado en GPUs móviles de gama media)
function Card({ children, className = "" }) {
  return (
    <div className={`bg-slate-800 border border-slate-700/60 rounded-2xl p-4 ${className}`}>
      {children}
    </div>
  );
}

// ─── SCREEN A: SETUP ───────────────────────────────────────────────────────────
// Estado de configuración elevado (lifted) al componente padre App,
// recibido por props para persistir entre sesiones de juego.
function SetupScreen({
  players, setPlayers,
  impostors, setImpostors,
  hintsEnabled, setHintsEnabled,
  selectedThemes, setSelectedThemes,
  onStart,
}) {
  const [inputName, setInputName] = useState("");

  // Límite: impostores < mitad de jugadores (siempre minoría estricta)
  const maxImpostors = players.length >= 3
    ? Math.ceil(players.length / 2) - 1
    : 1;
  const safeImpostors = Math.min(impostors, Math.max(1, maxImpostors));

  const addPlayer = () => {
    const name = inputName.trim();
    if (!name || players.includes(name) || players.length >= 24) return;
    setPlayers((prev) => [...prev, name]);
    setInputName("");
  };

  const removePlayer = (name) =>
    setPlayers((prev) => prev.filter((n) => n !== name));

  const toggleTheme = (cat) =>
    setSelectedThemes((prev) =>
      prev.includes(cat) ? prev.filter((c) => c !== cat) : [...prev, cat]
    );

  const toggleAllThemes = () =>
    setSelectedThemes(
      selectedThemes.length === ALL_THEMES.length
        ? []
        : ALL_THEMES.map((t) => t.categoria)
    );

  const canStart =
    players.length >= 3 && selectedThemes.length >= 1 && safeImpostors >= 1;

  const handleStart = () => {
    const themes = ALL_THEMES.filter((t) => selectedThemes.includes(t.categoria));
    onStart(players, safeImpostors, themes, hintsEnabled);
  };

  return (
    <div className="min-h-screen bg-slate-950 text-white pb-36 overflow-y-auto">

      {/* ── Cabecera ── */}
      <div className="bg-gradient-to-br from-slate-900 via-purple-950 to-slate-900 px-5 pt-12 pb-8">
        <p className="text-violet-400 text-xs tracking-[0.3em] uppercase font-semibold mb-1">
          — Bienvenido a... —
        </p>
        <h1 className="text-4xl font-black tracking-tight text-white leading-none">
          El Impostor
        </h1>
        <p className="text-slate-400 text-sm mt-2">Configura tu partida</p>
      </div>

      <div className="px-4 py-5 space-y-4">

        {/* ── Jugadores ── */}
        <Card>
          <div className="flex items-center justify-between mb-3">
            <h2 className="text-slate-200 font-bold text-sm tracking-wider uppercase">
              Jugadores
            </h2>
            <span
              className={`text-xs font-semibold px-2 py-0.5 rounded-full ${
                players.length >= 3
                  ? "bg-emerald-900/60 text-emerald-400"
                  : "bg-slate-700 text-slate-400"
              }`}
            >
              {players.length} / 24
            </span>
          </div>

          <div className="flex gap-2 mb-3">
            <input
              type="text"
              value={inputName}
              onChange={(e) => setInputName(e.target.value)}
              onKeyDown={(e) => e.key === "Enter" && addPlayer()}
              placeholder="Nombre del jugador…"
              maxLength={20}
              className="flex-1 bg-slate-900 border border-slate-700 rounded-xl px-4 py-2.5
                         text-sm text-white placeholder-slate-600
                         focus:outline-none focus:border-violet-500 transition-colors"
            />
            <button
              onClick={addPlayer}
              disabled={!inputName.trim() || players.length >= 24}
              className="w-10 h-10 rounded-xl bg-violet-600 hover:bg-violet-500
                         disabled:opacity-30 flex items-center justify-center transition-all active:scale-90"
            >
              <IconPlus />
            </button>
          </div>

          {players.length > 0 ? (
            <div className="flex flex-wrap gap-2">
              {players.map((p) => (
                <PlayerChip key={p} name={p} onRemove={() => removePlayer(p)} />
              ))}
            </div>
          ) : (
            <p className="text-slate-600 text-xs text-center py-3">
              Añade al menos 3 jugadores
            </p>
          )}
        </Card>

        {/* ── Impostores ── */}
        <Card>
          <div className="flex items-center justify-between">
            <div>
              <h2 className="text-slate-200 font-bold text-sm tracking-wider uppercase flex items-center gap-2">
                <IconSkull />
                Impostores
              </h2>
              <p className="text-slate-500 text-xs mt-0.5">
                Máx.{" "}
                {players.length >= 3 ? maxImpostors : "—"} con {players.length} jugadores
              </p>
            </div>
            <Counter
              value={safeImpostors}
              onInc={() => setImpostors((v) => Math.min(v + 1, maxImpostors))}
              onDec={() => setImpostors((v) => Math.max(v - 1, 1))}
              min={1}
              max={players.length >= 3 ? maxImpostors : 1}
            />
          </div>
        </Card>

        {/* ── Pistas ── */}
        <Card>
          <div className="flex items-center justify-between gap-4">
            <div>
              <h2 className="text-slate-200 font-bold text-sm tracking-wider uppercase">
                Pistas para impostores
              </h2>
              <p className="text-slate-500 text-xs mt-0.5">
                El impostor recibirá una pista de la palabra
              </p>
            </div>
            <Toggle checked={hintsEnabled} onChange={setHintsEnabled} />
          </div>
        </Card>

        {/* ── Temáticas ── */}
        <Card>
          <div className="flex items-center justify-between mb-3">
            <h2 className="text-slate-200 font-bold text-sm tracking-wider uppercase">
              Temáticas
            </h2>
            <button
              onClick={toggleAllThemes}
              className="text-xs font-semibold text-violet-400 hover:text-violet-300 transition-colors"
            >
              {selectedThemes.length === ALL_THEMES.length
                ? "Deseleccionar todas"
                : "Seleccionar todas"}
            </button>
          </div>

          <div className="grid grid-cols-2 gap-2">
            {ALL_THEMES.map((theme) => {
              const active = selectedThemes.includes(theme.categoria);
              // normalizeCategory evita que vengan en MAYÚSCULAS del JSON
              const label = normalizeCategory(theme.categoria);
              return (
                <button
                  key={theme.categoria}
                  onClick={() => toggleTheme(theme.categoria)}
                  className={`flex items-center gap-2 px-3 py-2.5 rounded-xl text-sm font-medium
                               text-left transition-all active:scale-95 border ${
                    active
                      ? "bg-violet-600/20 border-violet-500/50 text-violet-200"
                      : "bg-slate-900/60 border-slate-700/50 text-slate-400 hover:border-slate-600"
                  }`}
                >
                  <span
                    className={`shrink-0 w-5 h-5 rounded-full flex items-center justify-center transition-colors ${
                      active
                        ? "bg-violet-500"
                        : "bg-slate-700 border border-slate-600"
                    }`}
                  >
                    {active && <IconCheck />}
                  </span>
                  <span className="truncate">{label}</span>
                </button>
              );
            })}
          </div>

          {selectedThemes.length === 0 && (
            <p className="text-slate-600 text-xs text-center mt-3">
              Selecciona al menos una temática
            </p>
          )}
        </Card>
      </div>

      {/* ── CTA fijo inferior ── */}
      <div className="fixed bottom-0 left-0 right-0 p-4 bg-gradient-to-t from-slate-950 via-slate-950/90 to-transparent">
        <GlowButton
          onClick={handleStart}
          disabled={!canStart}
          className="w-full py-4 text-base"
        >
          ¡Iniciar Juego!
        </GlowButton>
        {!canStart && (
          <p className="text-center text-slate-600 text-xs mt-2">
            {players.length < 3
              ? `Faltan ${3 - players.length} jugador${3 - players.length > 1 ? "es" : ""}`
              : selectedThemes.length < 1
              ? "Selecciona al menos una temática"
              : ""}
          </p>
        )}
      </div>
    </div>
  );
}

// ─── SCREEN B: PASS DEVICE — CORTINA SWIPE UP ─────────────────────────────────
function PassScreen({ playerName, onReveal }) {
  // dragY: píxeles desplazados. Sólo valores negativos (hacia arriba).
  const [dragY, setDragY]         = useState(0);
  const [isDragging, setIsDragging] = useState(false);
  const [isReturning, setIsReturning] = useState(false);

  const startYRef    = useRef(null);
  const committedRef = useRef(false); // evita doble disparo de onReveal

  // ── Cálculo de progreso y umbral ──────────────────────────────────────────
  const threshold = typeof window !== "undefined"
    ? window.innerHeight * SWIPE_THRESHOLD_RATIO
    : 220;
  const travel    = Math.abs(Math.min(dragY, 0));
  const progress  = Math.min(1, travel / threshold);  // 0 → 1
  const overThreshold = travel >= threshold;

  // ── Acción al soltar ──────────────────────────────────────────────────────
  const handleRelease = useCallback(() => {
    if (committedRef.current) return;
    setIsDragging(false);
    startYRef.current = null;

    if (overThreshold) {
      committedRef.current = true;
      // Cortina sale volando; onReveal se dispara al terminar la transición
      setIsReturning(true);
      setDragY(-(window.innerHeight * 1.1));
      setTimeout(onReveal, 320);
    } else {
      // Rebote suave de vuelta a posición original
      setIsReturning(true);
      setDragY(0);
      setTimeout(() => setIsReturning(false), 380);
    }
  }, [overThreshold, onReveal]);

  // ── Touch handlers ────────────────────────────────────────────────────────
  const onTouchStart = (e) => {
    if (committedRef.current) return;
    startYRef.current = e.touches[0].clientY;
    setIsDragging(true);
    setIsReturning(false);
  };

  const onTouchMove = (e) => {
    if (startYRef.current === null || committedRef.current) return;
    const delta = e.touches[0].clientY - startYRef.current;
    setDragY(Math.min(0, delta)); // solo hacia arriba
  };

  const onTouchEnd = () => handleRelease();

  // ── Mouse handlers (desktop) ──────────────────────────────────────────────
  const onMouseDown = (e) => {
    if (committedRef.current) return;
    startYRef.current = e.clientY;
    setIsDragging(true);
    setIsReturning(false);
  };

  const onMouseMove = useCallback((e) => {
    if (!isDragging || startYRef.current === null || committedRef.current) return;
    const delta = e.clientY - startYRef.current;
    setDragY(Math.min(0, delta));
  }, [isDragging]);

  const onMouseUp = useCallback(() => {
    if (isDragging) handleRelease();
  }, [isDragging, handleRelease]);

  // Listener global para mouse (captura arrastre fuera del elemento)
  useEffect(() => {
    if (isDragging) {
      window.addEventListener("mousemove", onMouseMove);
      window.addEventListener("mouseup",   onMouseUp);
    }
    return () => {
      window.removeEventListener("mousemove", onMouseMove);
      window.removeEventListener("mouseup",   onMouseUp);
    };
  }, [isDragging, onMouseMove, onMouseUp]);

  // ── Estilos dinámicos de la cortina ───────────────────────────────────────
  const curtainStyle = {
    transform:  `translateY(${dragY}px)`,
    transition: isReturning
      ? "transform 0.38s cubic-bezier(0.22, 1, 0.36, 1)"
      : "none",
    willChange: "transform",
  };

  // Colores de acento que cambian al superar el umbral
  const accentColor = overThreshold ? "#34d399" : "#8b5cf6"; // emerald-400 : violet-500

  return (
    // touch-none: desactiva el scroll nativo del browser durante el swipe
    <div className="fixed inset-0 bg-slate-950 overflow-hidden select-none touch-none">

      {/* ── Fondo debajo de la cortina (visible conforme se desliza) ── */}
      <div
        className="absolute inset-0 flex flex-col items-center justify-center pointer-events-none px-6 gap-2"
        style={{ opacity: progress }}
      >
        <p className="text-slate-500 text-xs tracking-[0.25em] uppercase">
          Tu tarjeta está lista
        </p>
        <p className="text-white text-5xl font-black tracking-tight text-center">
          {playerName}
        </p>
        <p className="text-slate-600 text-sm mt-2">↑ sigue deslizando ↑</p>
      </div>

      {/* ── CORTINA DESLIZABLE ─────────────────────────────────────────── */}
      <div
        className="absolute inset-0 cursor-grab active:cursor-grabbing"
        style={curtainStyle}
        onTouchStart={onTouchStart}
        onTouchMove={onTouchMove}
        onTouchEnd={onTouchEnd}
        onMouseDown={onMouseDown}
      >
        {/* Superficie de la cortina */}
        <div className="absolute inset-0 bg-slate-900 flex flex-col items-center justify-center gap-6 px-8">

          {/* Icono central */}
          <div
            className="w-20 h-20 rounded-full border-2 flex items-center justify-center transition-colors duration-200"
            style={{
              backgroundColor: overThreshold ? "rgba(52,211,153,0.1)" : "rgba(139,92,246,0.1)",
              borderColor:     overThreshold ? "rgba(52,211,153,0.4)" : "rgba(139,92,246,0.35)",
            }}
          >
            <span className="text-4xl">🎭</span>
          </div>

          {/* Nombre del jugador */}
          <div className="text-center">
            <p className="text-slate-500 text-xs tracking-[0.3em] uppercase mb-2">
              Le toca a
            </p>
            <h2 className="text-4xl font-black text-white tracking-tight">
              {playerName}
            </h2>
          </div>

          {/* ── Indicador de swipe ── */}
          <div className="flex flex-col items-center gap-2 mt-2">
            {/* Tres chevrones apilados con opacidad escalonada */}
            <div className="flex flex-col items-center -space-y-1" style={{ color: accentColor }}>
              <IconChevronUp size={22} opacity={0.3 + progress * 0.7} />
              <IconChevronUp size={26} opacity={0.5 + progress * 0.5} />
              <IconChevronUp size={30} opacity={0.7 + progress * 0.3} />
            </div>
            <p
              className="text-sm font-semibold tracking-wider mt-1 transition-colors duration-200"
              style={{ color: accentColor }}
            >
              {overThreshold ? "¡Suelta para revelar!" : "Desliza hacia arriba"}
            </p>
            <p className="text-slate-600 text-xs">para revelar tu identidad</p>
          </div>
        </div>

        {/* Barra de progreso inferior */}
        <div className="absolute bottom-0 left-0 right-0 h-1 bg-slate-800">
          <div
            className="h-full transition-colors duration-150"
            style={{
              width:           `${progress * 100}%`,
              backgroundColor: accentColor,
            }}
          />
        </div>

        {/* Asa superior (hint visual) */}
        <div className="absolute top-3 inset-x-0 flex justify-center pointer-events-none">
          <div className="w-10 h-1 rounded-full bg-slate-600" />
        </div>
      </div>
    </div>
  );
}

// ─── SCREEN C: ROLE REVEAL ─────────────────────────────────────────────────────
function RevealScreen({ playerName, role, word, hint, hintsEnabled, isLast, onNext }) {
  const isImpostor = role === "impostor";

  return (
    <div
      className={`min-h-screen flex flex-col items-center justify-between px-5 py-12 select-none ${
        isImpostor
          ? "bg-gradient-to-b from-rose-950 via-slate-950 to-slate-950"
          : "bg-gradient-to-b from-blue-950 via-slate-950 to-slate-950"
      }`}
    >
      {/* Nombre del jugador */}
      <div className="text-center">
        <p className="text-slate-500 text-xs tracking-widest uppercase">Rol de</p>
        <p className="text-white font-bold text-xl">{playerName}</p>
      </div>

      {/* Tarjeta de rol */}
      <div className="w-full max-w-sm">
        <div
          className={`rounded-3xl border p-8 text-center ${
            isImpostor
              ? "bg-rose-950/70 border-rose-700/50"
              : "bg-blue-950/70 border-blue-700/50"
          }`}
        >
          {isImpostor ? (
            <>
              <div className="text-6xl mb-4">🎭</div>
              <p className="text-rose-400 text-xs tracking-[0.3em] uppercase font-semibold mb-2">
                Tu rol
              </p>
              <h2 className="text-4xl font-black text-rose-300 mb-4">Impostor</h2>
              {hintsEnabled && hint ? (
                <div className="mt-4 bg-rose-900/40 border border-rose-700/40 rounded-xl px-4 py-3">
                  <p className="text-rose-400 text-xs uppercase tracking-widest font-semibold mb-1">
                    Pista
                  </p>
                  <p className="text-rose-200 font-bold text-xl">{hint}</p>
                </div>
              ) : (
                <p className="text-rose-400/60 text-sm mt-2">
                  Descubre la palabra a través del debate
                </p>
              )}
            </>
          ) : (
            <>
              <div className="text-6xl mb-4">🕵️</div>
              <p className="text-blue-400 text-xs tracking-[0.3em] uppercase font-semibold mb-2">
                Tu rol
              </p>
              <h2 className="text-4xl font-black text-blue-200 mb-4">Civil</h2>
              <div className="bg-blue-900/40 border border-blue-700/40 rounded-xl px-4 py-3">
                <p className="text-blue-400 text-xs uppercase tracking-widest font-semibold mb-1">
                  La palabra secreta
                </p>
                <p className="text-white font-black text-3xl">{word}</p>
              </div>
            </>
          )}
        </div>
      </div>

      {/* Botón de acción */}
      <GlowButton
        onClick={onNext}
        variant={isImpostor ? "danger" : "primary"}
        className="w-full max-w-sm py-4"
      >
        {isLast ? "¡Todos listos! →" : "Ocultar y pasar al siguiente →"}
      </GlowButton>
    </div>
  );
}

// ─── SCREEN D: START ROUND ─────────────────────────────────────────────────────
function StartRoundScreen({ firstPlayer, onEnd }) {
  return (
    <div className="min-h-screen bg-slate-950 flex flex-col items-center justify-between px-5 py-16">
      <div className="text-center">
        <p className="text-violet-400 text-xs tracking-[0.3em] uppercase font-semibold mb-1">
          ¡Todos listos!
        </p>
        <h2 className="text-3xl font-black text-white">Comienza la ronda</h2>
      </div>

      <div className="text-center space-y-6">
        {/* Avatar con un único pulse suave — sin sombras GPU costosas */}
        <div className="relative w-36 h-36 mx-auto flex items-center justify-center">
          <div className="absolute inset-0 rounded-full bg-violet-600/15 animate-pulse" />
          <div className="w-28 h-28 rounded-full bg-gradient-to-br from-violet-600 to-purple-700 flex items-center justify-center">
            <span className="text-4xl font-black text-white">
              {firstPlayer.charAt(0).toUpperCase()}
            </span>
          </div>
        </div>

        <div>
          <p className="text-slate-400 text-sm">Empieza hablando</p>
          <p className="text-3xl font-black text-white mt-1">{firstPlayer}</p>
          <p className="text-slate-600 text-xs mt-2 max-w-xs mx-auto">
            Describe la palabra sin decirla.{"\n"}
            ¡Los impostores intentarán no ser descubiertos!
          </p>
        </div>
      </div>

      <GlowButton onClick={onEnd} variant="danger" className="w-full max-w-sm py-4">
        Finalizar ronda y revelar
      </GlowButton>
    </div>
  );
}

// ─── SCREEN E: END GAME ────────────────────────────────────────────────────────
function EndScreen({ word, roles, onReplay, onMenu }) {
  const impostorNames = roles.filter((r) =>  r.isImpostor).map((r) => r.name);
  const civilNames    = roles.filter((r) => !r.isImpostor).map((r) => r.name);

  return (
    <div className="min-h-screen bg-slate-950 overflow-y-auto pb-10">
      <div className="bg-gradient-to-br from-slate-900 via-rose-950/20 to-slate-900 px-5 pt-14 pb-8 text-center">
        <p className="text-rose-400 text-xs tracking-[0.3em] uppercase font-semibold mb-1">
          Fin de la partida
        </p>
        <h1 className="text-4xl font-black text-white">¡Revelación!</h1>
      </div>

      <div className="px-4 py-5 space-y-4">

        {/* Palabra secreta */}
        <div className="bg-slate-800 border border-slate-700/60 rounded-2xl p-4 text-center">
          <p className="text-slate-500 text-xs uppercase tracking-widest mb-2">
            La palabra secreta era
          </p>
          <p className="text-5xl font-black text-white">{word}</p>
        </div>

        {/* Impostores */}
        <div className="bg-slate-800 border border-slate-700/60 rounded-2xl p-4">
          <h3 className="text-rose-400 font-bold text-sm tracking-widest uppercase mb-3 flex items-center gap-2">
            <IconSkull /> Impostores
          </h3>
          <div className="space-y-2">
            {impostorNames.map((name) => (
              <div
                key={name}
                className="flex items-center gap-3 bg-rose-950/40 border border-rose-800/30 rounded-xl px-4 py-3"
              >
                <span className="text-xl">🎭</span>
                <span className="font-bold text-rose-200">{name}</span>
              </div>
            ))}
          </div>
        </div>

        {/* Civiles */}
        <div className="bg-slate-800 border border-slate-700/60 rounded-2xl p-4">
          <h3 className="text-blue-400 font-bold text-sm tracking-widest uppercase mb-3">
            Civiles
          </h3>
          <div className="grid grid-cols-2 gap-2">
            {civilNames.map((name) => (
              <div
                key={name}
                className="flex items-center gap-2 bg-blue-950/30 border border-blue-800/20 rounded-xl px-3 py-2"
              >
                <span className="text-base">🕵️</span>
                <span className="font-medium text-blue-200 text-sm truncate">{name}</span>
              </div>
            ))}
          </div>
        </div>

        {/* Acciones */}
        <div className="space-y-3 pt-2">
          <GlowButton onClick={onReplay} variant="primary" className="w-full py-4">
            🔄 Jugar de nuevo (mismos jugadores)
          </GlowButton>
          <GlowButton onClick={onMenu} variant="ghost" className="w-full py-4">
            ← Volver al menú principal
          </GlowButton>
        </div>
      </div>
    </div>
  );
}

// ─── APP ROOT ──────────────────────────────────────────────────────────────────
// El estado de configuración vive aquí (lifted state) para que persista
// al navegar entre pantallas, especialmente al volver al menú principal.
export default function App() {
  // ── Estado de configuración elevado (persiste entre partidas) ──
  const [players,        setPlayers]        = useState([]);
  const [impostors,      setImpostors]      = useState(1);
  const [hintsEnabled,   setHintsEnabled]   = useState(false);
  const [selectedThemes, setSelectedThemes] = useState([]);

  // ── Estado de sesión de juego ──
  const [screen,              setScreen]              = useState(SCREEN.SETUP);
  const [game,                setGame]                = useState(null);
  const [currentPlayerIndex,  setCurrentPlayerIndex]  = useState(0);
  const [firstSpeaker,        setFirstSpeaker]        = useState("");

  // ── Handlers ──────────────────────────────────────────────────────────────
  const handleStart = useCallback((playerList, impostorCount, themes, hints) => {
    const g = buildGame(playerList, impostorCount, themes, hints);
    setGame(g);
    setCurrentPlayerIndex(0);
    setScreen(SCREEN.PASS);
  }, []);

  // Swipe completado → mostrar rol
  const handleReveal = useCallback(() => {
    setScreen(SCREEN.REVEAL);
  }, []);

  // Pasar al siguiente jugador o abrir pantalla de inicio de ronda
  const handleNext = useCallback((currentGame) => {
    setCurrentPlayerIndex((idx) => {
      const next = idx + 1;
      if (next >= currentGame.roles.length) {
        // Elegir primer orador entre los civiles (nunca un impostor)
        const civils = currentGame.roles.filter((r) => !r.isImpostor);
        setFirstSpeaker(pickRandom(civils).name);
        setScreen(SCREEN.START_ROUND);
        return idx; // no avanza más allá del último índice válido
      }
      setScreen(SCREEN.PASS);
      return next;
    });
  }, []);

  const handleEndRound = useCallback(() => setScreen(SCREEN.END), []);

  // "Jugar de nuevo" rehace la partida con los mismos jugadores y config
  const handleReplay = useCallback(() => {
    const themes = ALL_THEMES.filter((t) => selectedThemes.includes(t.categoria));
    const safeCount = Math.min(impostors, Math.ceil(players.length / 2) - 1);
    handleStart(players, safeCount, themes, hintsEnabled);
  }, [players, impostors, selectedThemes, hintsEnabled, handleStart]);

  // "Volver al menú" — los jugadores y config se CONSERVAN gracias al lifted state
  const handleMenu = useCallback(() => {
    setGame(null);
    setScreen(SCREEN.SETUP);
  }, []);

  // ── Render ────────────────────────────────────────────────────────────────
  return (
    <div className="font-sans antialiased">

      {screen === SCREEN.SETUP && (
        <SetupScreen
          players={players}           setPlayers={setPlayers}
          impostors={impostors}       setImpostors={setImpostors}
          hintsEnabled={hintsEnabled} setHintsEnabled={setHintsEnabled}
          selectedThemes={selectedThemes} setSelectedThemes={setSelectedThemes}
          onStart={handleStart}
        />
      )}

      {screen === SCREEN.PASS && game && (
        // key={currentPlayerIndex} fuerza re-mount en cada turno → resetea estado del drag
        <PassScreen
          key={currentPlayerIndex}
          playerName={game.roles[currentPlayerIndex].name}
          onReveal={handleReveal}
        />
      )}

      {screen === SCREEN.REVEAL && game && (
        <RevealScreen
          playerName={game.roles[currentPlayerIndex].name}
          role={game.roles[currentPlayerIndex].isImpostor ? "impostor" : "civil"}
          word={game.word}
          hint={game.hint}
          hintsEnabled={game.hintsEnabled}
          isLast={currentPlayerIndex === game.roles.length - 1}
          onNext={() => handleNext(game)}
        />
      )}

      {screen === SCREEN.START_ROUND && game && (
        <StartRoundScreen
          firstPlayer={firstSpeaker}
          onEnd={handleEndRound}
        />
      )}

      {screen === SCREEN.END && game && (
        <EndScreen
          word={game.word}
          roles={game.roles}
          onReplay={handleReplay}
          onMenu={handleMenu}
        />
      )}
    </div>
  );
}

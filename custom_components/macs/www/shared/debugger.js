// custom_components/macs/www/shared/debugger.js

/**
 * Shared Debugger for M.A.C.S.
 * ----------------------------
 * Centralise les logs frontend/backend de la carte Lovelace.
 *
 * Modes supportés :
 * - None : aucun log
 * - All  : tous les logs
 * - Nom de fichier / module : uniquement ce module
 *
 * Exemple :
 *   const debug = createDebugger(import.meta.url);
 *   debug("Message");
 *   debug("warn", "Attention");
 *   debug("error", err);
 */

let DEBUG_OVERRIDE = null;

const DEFAULT_DEBUG_MODE = "None";

const LEVELS = {
  log: "log",
  info: "info",
  warn: "warn",
  error: "error",
  debug: "debug"
};

function safeString(value) {
  if (value === null) return "null";
  if (typeof value === "undefined") return "undefined";

  if (typeof value === "string") return value;

  if (value instanceof Error) {
    return value.stack || value.message || String(value);
  }

  if (typeof value === "object") {
    try {
      return JSON.stringify(value, null, 2);
    } catch {
      return String(value);
    }
  }

  return String(value);
}

function getFileNameFromUrl(source) {
  const raw = safeString(source);

  try {
    const url = new URL(raw, window.location.href);
    const pathname = url.pathname || "";
    const parts = pathname.split("/").filter(Boolean);
    return parts.length ? parts[parts.length - 1] : raw;
  } catch {
    const clean = raw.split("?")[0].split("#")[0];
    const parts = clean.split("/").filter(Boolean);
    return parts.length ? parts[parts.length - 1] : raw;
  }
}

function getModuleName(source) {
  const file = getFileNameFromUrl(source);
  return file.replace(/\.(js|mjs|ts)$/i, "");
}

function normalizeDebugMode(value) {
  const mode = safeString(value).trim();

  if (!mode) return DEFAULT_DEBUG_MODE;

  if (mode.toLowerCase() === "none") return "None";
  if (mode.toLowerCase() === "all") return "All";

  return mode;
}

function getWindowDebugMode() {
  if (typeof window === "undefined") return DEFAULT_DEBUG_MODE;

  if (DEBUG_OVERRIDE !== null && typeof DEBUG_OVERRIDE !== "undefined") {
    return normalizeDebugMode(DEBUG_OVERRIDE);
  }

  if (typeof window.__MACS_DEBUG__ !== "undefined") {
    return normalizeDebugMode(window.__MACS_DEBUG__);
  }

  try {
    const params = new URLSearchParams(window.location.search || "");
    const fromUrl = params.get("debug");

    if (fromUrl !== null) {
      return normalizeDebugMode(fromUrl);
    }
  } catch {
    // ignore
  }

  return DEFAULT_DEBUG_MODE;
}

function isDebugEnabled(moduleName, fileName) {
  const mode = getWindowDebugMode();

  if (mode === "All") return true;
  if (mode === "None") return false;

  const wanted = mode.toLowerCase().trim();
  const moduleLower = safeString(moduleName).toLowerCase();
  const fileLower = safeString(fileName).toLowerCase();

  return (
    wanted === moduleLower ||
    wanted === fileLower ||
    wanted === fileLower.replace(/\.(js|mjs|ts)$/i, "")
  );
}

function writeToDebugDiv(moduleName, level, args) {
  if (typeof document === "undefined") return;

  const debugDiv = document.getElementById("debug");
  if (!debugDiv) return;

  let logContainer = debugDiv.querySelector(".debug-log");

  if (!logContainer) {
    logContainer = document.createElement("div");
    logContainer.className = "debug-log";
    debugDiv.appendChild(logContainer);
  }

  const line = document.createElement("div");
  line.className = `debug-line debug-${level}`;

  const time = new Date().toLocaleTimeString([], {
    hour: "2-digit",
    minute: "2-digit",
    second: "2-digit"
  });

  line.textContent = `[${time}] [${moduleName}] ${args.map(safeString).join(" ")}`;

  logContainer.appendChild(line);

  const maxLines = 200;
  while (logContainer.children.length > maxLines) {
    logContainer.removeChild(logContainer.firstChild);
  }
}

function consoleWrite(moduleName, level, args) {
  if (typeof console === "undefined") return;

  const method = LEVELS[level] || LEVELS.log;
  const fn = console[method] || console.log;

  try {
    fn.call(console, `[MACS:${moduleName}]`, ...args);
  } catch {
    try {
      console.log(`[MACS:${moduleName}] ${args.map(safeString).join(" ")}`);
    } catch {
      // ignore
    }
  }
}

export function setDebugOverride(value, debugFn = null) {
  DEBUG_OVERRIDE = normalizeDebugMode(value);

  if (typeof window !== "undefined") {
    window.__MACS_DEBUG__ = DEBUG_OVERRIDE;
  }

  if (typeof debugFn === "function") {
    try {
      debugFn("debug override set to", DEBUG_OVERRIDE);
    } catch {
      // ignore
    }
  }
}

export function getDebugMode() {
  return getWindowDebugMode();
}

export function clearDebugOverride() {
  DEBUG_OVERRIDE = null;
}

export function createDebugger(source = "unknown") {
  const fileName = getFileNameFromUrl(source);
  const moduleName = getModuleName(source);

  const debug = (...args) => {
    if (!isDebugEnabled(moduleName, fileName)) return;

    let level = "log";
    let payload = args;

    if (
      args.length > 1 &&
      typeof args[0] === "string" &&
      Object.prototype.hasOwnProperty.call(LEVELS, args[0].toLowerCase())
    ) {
      level = args[0].toLowerCase();
      payload = args.slice(1);
    }

    consoleWrite(moduleName, level, payload);
    writeToDebugDiv(moduleName, level, payload);
  };

  debug.enabled = () => isDebugEnabled(moduleName, fileName);
  debug.moduleName = moduleName;
  debug.fileName = fileName;

  debug.log = (...args) => debug("log", ...args);
  debug.info = (...args) => debug("info", ...args);
  debug.warn = (...args) => debug("warn", ...args);
  debug.error = (...args) => debug("error", ...args);
  debug.debug = (...args) => debug("debug", ...args);

  return debug;
}

export default createDebugger;

export const UNKNOWN_STATES = new Set([
  "",
  "unknown",
  "unavailable",
  "none",
  "null",
  "nan",
  "undefined"
]);

export function isUnknown(value) {
  if (value === null || value === undefined) return true;
  return UNKNOWN_STATES.has(String(value).trim().toLowerCase());
}

export function normalizeText(value, fallback = "") {
  if (value === null || value === undefined) return fallback;

  if (typeof value === "string") {
    const text = value.trim();
    return text || fallback;
  }

  if (typeof value === "object") {
    const text =
      value.text ??
      value.message ??
      value.content ??
      value.speech?.plain?.speech ??
      value.response?.speech?.plain?.speech ??
      "";

    if (typeof text === "object") {
      try {
        return JSON.stringify(text);
      } catch {
        return fallback;
      }
    }

    return String(text || fallback).trim();
  }

  return String(value).trim() || fallback;
}

export function toNumber(value, fallback = null) {
  if (value === null || value === undefined) return fallback;

  if (typeof value === "number") {
    return Number.isFinite(value) ? value : fallback;
  }

  const raw = String(value).trim().toLowerCase();
  if (UNKNOWN_STATES.has(raw)) return fallback;

  const cleaned = raw
    .replace(",", ".")
    .replace(/[^\d.+-]/g, "");

  if (!cleaned) return fallback;

  const parsed = Number(cleaned);
  return Number.isFinite(parsed) ? parsed : fallback;
}

export function clampNumber(value, min, max, fallback = null) {
  const parsed = toNumber(value, fallback);

  if (parsed === null || parsed === undefined) {
    return fallback;
  }

  return Math.max(min, Math.min(max, parsed));
}

export function toBoolean(value, fallback = false) {
  if (value === null || value === undefined) return fallback;

  if (typeof value === "boolean") return value;

  if (typeof value === "number") {
    if (!Number.isFinite(value)) return fallback;
    return value !== 0;
  }

  const raw = String(value).trim().toLowerCase();
  if (UNKNOWN_STATES.has(raw)) return fallback;

  if (["on", "true", "yes", "1", "open", "home", "charging"].includes(raw)) {
    return true;
  }

  if (["off", "false", "no", "0", "closed", "not_home", "discharging"].includes(raw)) {
    return false;
  }

  return fallback;
}

export function normalizeEntityId(value) {
  const text = normalizeText(value, "");
  return text.includes(".") ? text : "";
}

export function getEntityState(hass, entityId) {
  if (!hass || !entityId) return null;
  return hass.states?.[entityId] ?? null;
}

export function getEntityNumericState(hass, entityId, fallback = null) {
  const entity = getEntityState(hass, entityId);
  return toNumber(entity?.state, fallback);
}

export function getEntityBooleanState(hass, entityId, fallback = false) {
  const entity = getEntityState(hass, entityId);
  return toBoolean(entity?.state, fallback);
}

export function getEntityAttribute(entity, attribute, fallback = null) {
  if (!entity || !attribute) return fallback;

  const value = entity.attributes?.[attribute];

  if (isUnknown(value)) {
    return fallback;
  }

  return value;
}

export function getEntityNumericAttribute(entity, attribute, fallback = null) {
  return toNumber(getEntityAttribute(entity, attribute, fallback), fallback);
}

export function getFriendlyName(hass, entityId) {
  const entity = getEntityState(hass, entityId);
  return entity?.attributes?.friendly_name || entityId || "";
}

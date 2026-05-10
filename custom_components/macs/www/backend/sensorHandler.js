// custom_components/macs/www/backend/sensorHandler.js

import {
  clampNumber,
  getEntityBooleanState,
  getEntityNumericAttribute,
  getEntityNumericState,
  getEntityState,
  normalizeEntityId,
  toBoolean,
  toNumber
} from "./validators.js";

export const DEFAULT_SENSOR_VALUES = Object.freeze({
  temperature: null,
  windspeed: null,
  precipitation: null,
  battery_charge: null,
  charging: false,

  snowy: false,
  cloudy: false,
  rainy: false,
  windy: false,
  sunny: false,
  stormy: false,
  foggy: false,
  hail: false,
  lightning: false,
  partlycloudy: false,
  pouring: false,
  clear_night: false,
  exceptional: false
});

const WEATHER_KEYS = [
  "snowy",
  "cloudy",
  "rainy",
  "windy",
  "sunny",
  "stormy",
  "foggy",
  "hail",
  "lightning",
  "partlycloudy",
  "pouring",
  "clear_night",
  "exceptional"
];

const WEATHER_MAP = {
  "clear-night": "clear_night",
  clear_night: "clear_night",
  cloudy: "cloudy",
  fog: "foggy",
  foggy: "foggy",
  hail: "hail",
  lightning: "lightning",
  "lightning-rainy": "stormy",
  partlycloudy: "partlycloudy",
  "partly-cloudy": "partlycloudy",
  pouring: "pouring",
  rainy: "rainy",
  rain: "rainy",
  snow: "snowy",
  snowy: "snowy",
  "snowy-rainy": "snowy",
  sunny: "sunny",
  windy: "windy",
  "windy-variant": "windy",
  exceptional: "exceptional",
  stormy: "stormy"
};

const INTERNAL_ENTITY_IDS = {
  temperature: "number.macs_temperature",
  windspeed: "number.macs_windspeed",
  precipitation: "number.macs_precipitation",
  battery_charge: "number.macs_battery_charge",
  charging: "switch.macs_charging",

  snowy: "switch.macs_weather_conditions_snowy",
  cloudy: "switch.macs_weather_conditions_cloudy",
  rainy: "switch.macs_weather_conditions_rainy",
  windy: "switch.macs_weather_conditions_windy",
  sunny: "switch.macs_weather_conditions_sunny",
  stormy: "switch.macs_weather_conditions_stormy",
  foggy: "switch.macs_weather_conditions_foggy",
  hail: "switch.macs_weather_conditions_hail",
  lightning: "switch.macs_weather_conditions_lightning",
  partlycloudy: "switch.macs_weather_conditions_partlycloudy",
  pouring: "switch.macs_weather_conditions_pouring",
  clear_night: "switch.macs_weather_conditions_clear_night",
  exceptional: "switch.macs_weather_conditions_exceptional"
};

function cloneDefaultValues() {
  return { ...DEFAULT_SENSOR_VALUES };
}

function sameValue(a, b) {
  return JSON.stringify(a) === JSON.stringify(b);
}

function normalizeUnit(value) {
  return String(value || "")
    .trim()
    .toLowerCase()
    .replace("°", "")
    .replace(" ", "");
}

function normalizeConfigBoolean(value) {
  return value === true || value === "true" || value === "on" || value === 1 || value === "1";
}

function getConfigNumber(config, key, fallback) {
  const value = toNumber(config?.[key], null);
  return value === null ? fallback : value;
}

function resolveEntityId(config, keys, fallback = "") {
  for (const key of keys) {
    const entityId = normalizeEntityId(config?.[key]);
    if (entityId) return entityId;
  }

  return fallback;
}

function convertTemperatureToCelsius(value, unit) {
  if (value === null) return null;

  const normalized = normalizeUnit(unit);

  if (normalized === "f" || normalized === "fahrenheit") {
    return (value - 32) * 5 / 9;
  }

  if (normalized === "k" || normalized === "kelvin") {
    return value - 273.15;
  }

  return value;
}

function convertWindSpeedToKmh(value, unit) {
  if (value === null) return null;

  const normalized = normalizeUnit(unit);

  if (
    normalized === "m/s" ||
    normalized === "ms" ||
    normalized === "mps" ||
    normalized === "meter/s" ||
    normalized === "meters/s"
  ) {
    return value * 3.6;
  }

  if (
    normalized === "mph" ||
    normalized === "mi/h" ||
    normalized === "mile/h" ||
    normalized === "miles/h"
  ) {
    return value * 1.609344;
  }

  if (
    normalized === "kn" ||
    normalized === "kt" ||
    normalized === "knot" ||
    normalized === "knots"
  ) {
    return value * 1.852;
  }

  return value;
}

function convertPrecipitationToMm(value, unit) {
  if (value === null) return null;

  const normalized = normalizeUnit(unit);

  if (normalized === "cm" || normalized === "centimeter" || normalized === "centimeters") {
    return value * 10;
  }

  if (normalized === "m" || normalized === "meter" || normalized === "meters") {
    return value * 1000;
  }

  if (
    normalized === "in" ||
    normalized === "inch" ||
    normalized === "inches"
  ) {
    return value * 25.4;
  }

  return value;
}

export class SensorHandler {
  constructor(hass = null, config = {}) {
    this.hass = hass;
    this.config = config || {};

    this._payload = cloneDefaultValues();
    this._sentPayload = {};
  }

  setHass(hass) {
    this.hass = hass || null;
  }

  setConfig(config) {
    this.config = config || {};
  }

  dispose() {
    this.hass = null;
    this.config = {};
    this._payload = cloneDefaultValues();
    this._sentPayload = {};
  }

  resetChangeTracking() {
    this._sentPayload = {};
  }

  syncChangeTracking() {
    this._sentPayload = { ...this._payload };
  }

  update(hass = null, config = null) {
    if (hass) {
      this.hass = hass;
    }

    if (config) {
      this.config = config;
    }

    const next = cloneDefaultValues();

    next.temperature = this.getTemperature();
    next.windspeed = this.getWindSpeed();
    next.precipitation = this.getPrecipitation();
    next.battery_charge = this.getBatteryCharge();
    next.charging = this.getCharging();

    const weather = this.getWeatherConditions();
    for (const key of WEATHER_KEYS) {
      next[key] = !!weather[key];
    }

    this._payload = next;
    return this.getPayload();
  }

  getPayload() {
    return { ...this._payload };
  }

  getTemperature() {
    const useCustomSensor = normalizeConfigBoolean(this.config.temperature_sensor_enabled);

    const entityId = useCustomSensor
      ? resolveEntityId(this.config, [
          "temperature_sensor_entity",
          "temperature_entity",
          "temperature_sensor"
        ])
      : INTERNAL_ENTITY_IDS.temperature;

    const entity = getEntityState(this.hass, entityId);
    let value = getEntityNumericState(this.hass, entityId, null);

    if (value === null) {
      return null;
    }

    const configUnit = this.config.temperature_sensor_unit;
    const entityUnit = entity?.attributes?.unit_of_measurement;
    value = convertTemperatureToCelsius(value, configUnit || entityUnit);

    const min = getConfigNumber(this.config, "temperature_sensor_min", -50);
    const max = getConfigNumber(this.config, "temperature_sensor_max", 80);

    return clampNumber(value, min, max, null);
  }

  getWindSpeed() {
    const useCustomSensor = normalizeConfigBoolean(this.config.wind_sensor_enabled);

    const entityId = useCustomSensor
      ? resolveEntityId(this.config, [
          "wind_sensor_entity",
          "windspeed_sensor_entity",
          "wind_speed_sensor_entity",
          "windspeed_entity",
          "wind_speed_entity"
        ])
      : INTERNAL_ENTITY_IDS.windspeed;

    const entity = getEntityState(this.hass, entityId);
    let value = getEntityNumericState(this.hass, entityId, null);

    if (value === null) {
      return null;
    }

    const configUnit = this.config.wind_sensor_unit;
    const entityUnit = entity?.attributes?.unit_of_measurement;
    value = convertWindSpeedToKmh(value, configUnit || entityUnit);

    const min = getConfigNumber(this.config, "wind_sensor_min", 0);
    const max = getConfigNumber(this.config, "wind_sensor_max", 300);

    return clampNumber(value, min, max, null);
  }

  getPrecipitation() {
    const useCustomSensor = normalizeConfigBoolean(this.config.precipitation_sensor_enabled);

    const entityId = useCustomSensor
      ? resolveEntityId(this.config, [
          "precipitation_sensor_entity",
          "rain_sensor_entity",
          "precipitation_entity"
        ])
      : INTERNAL_ENTITY_IDS.precipitation;

    const entity = getEntityState(this.hass, entityId);
    let value = getEntityNumericState(this.hass, entityId, null);

    if (value === null) {
      return null;
    }

    const configUnit = this.config.precipitation_sensor_unit;
    const entityUnit = entity?.attributes?.unit_of_measurement;
    value = convertPrecipitationToMm(value, configUnit || entityUnit);

    const min = getConfigNumber(this.config, "precipitation_sensor_min", 0);
    const max = getConfigNumber(this.config, "precipitation_sensor_max", 500);

    return clampNumber(value, min, max, null);
  }

  getBatteryCharge() {
    const useCustomSensor = normalizeConfigBoolean(this.config.battery_charge_sensor_enabled);

    const entityId = useCustomSensor
      ? resolveEntityId(this.config, [
          "battery_charge_sensor_entity",
          "battery_sensor_entity",
          "battery_entity"
        ])
      : INTERNAL_ENTITY_IDS.battery_charge;

    let value = getEntityNumericState(this.hass, entityId, null);

    if (value === null) {
      return null;
    }

    value = clampNumber(value, 0, 100, null);

    const min = getConfigNumber(this.config, "battery_charge_sensor_min", 0);
    const max = getConfigNumber(this.config, "battery_charge_sensor_max", 100);

    return clampNumber(value, min, max, null);
  }

  getCharging() {
    const useCustomSensor = normalizeConfigBoolean(this.config.battery_state_sensor_enabled);

    const entityId = useCustomSensor
      ? resolveEntityId(this.config, [
          "battery_state_sensor_entity",
          "charging_sensor_entity",
          "charging_binary_sensor_entity",
          "charging_entity"
        ])
      : INTERNAL_ENTITY_IDS.charging;

    if (!entityId) {
      return false;
    }

    return getEntityBooleanState(this.hass, entityId, false);
  }

  getWeatherConditions() {
    const result = {};

    for (const key of WEATHER_KEYS) {
      result[key] = false;
    }

    this.applyWeatherFromWeatherEntity(result);
    this.applyWeatherFromSwitches(result);
    this.applyWeatherFromSensorValues(result);

    return result;
  }

  applyWeatherFromWeatherEntity(result) {
    const useWeatherEntity = normalizeConfigBoolean(this.config.weather_conditions_enabled);

    if (!useWeatherEntity) {
      return;
    }

    const entityId = resolveEntityId(this.config, [
      "weather_conditions_entity",
      "weather_entity",
      "weather_sensor_entity"
    ]);

    const entity = getEntityState(this.hass, entityId);

    if (!entity) {
      return;
    }

    const state = String(entity.state || "").trim().toLowerCase();
    const mapped = WEATHER_MAP[state];

    if (mapped && mapped in result) {
      result[mapped] = true;
    }

    const windSpeed =
      getEntityNumericAttribute(entity, "wind_speed", null) ??
      getEntityNumericAttribute(entity, "wind_speed_km_h", null);

    const temperature =
      getEntityNumericAttribute(entity, "temperature", null) ??
      getEntityNumericAttribute(entity, "temperature_c", null);

    const precipitation =
      getEntityNumericAttribute(entity, "precipitation", null) ??
      getEntityNumericAttribute(entity, "precipitation_unit", null);

    if (windSpeed !== null && windSpeed >= 40) {
      result.windy = true;
    }

    if (temperature !== null && temperature <= 0) {
      result.snowy = true;
    }

    if (precipitation !== null && precipitation > 0) {
      result.rainy = true;
    }

    if (precipitation !== null && precipitation >= 10) {
      result.pouring = true;
    }
  }

  applyWeatherFromSwitches(result) {
    const useWeatherEntity = normalizeConfigBoolean(this.config.weather_conditions_enabled);

    if (useWeatherEntity) {
      return;
    }

    for (const key of WEATHER_KEYS) {
      const entityId = INTERNAL_ENTITY_IDS[key];

      if (!entityId) {
        continue;
      }

      result[key] = getEntityBooleanState(this.hass, entityId, false);
    }
  }

  applyWeatherFromSensorValues(result) {
    const temperature = this.getTemperature();
    const windspeed = this.getWindSpeed();
    const precipitation = this.getPrecipitation();

    if (temperature !== null && temperature <= 0) {
      result.snowy = true;
    }

    if (windspeed !== null && windspeed >= 40) {
      result.windy = true;
    }

    if (precipitation !== null && precipitation > 0) {
      result.rainy = true;
    }

    if (precipitation !== null && precipitation >= 10) {
      result.pouring = true;
    }
  }

  _hasChanged(key) {
    const current = this._payload?.[key];
    const previous = this._sentPayload?.[key];

    if (sameValue(current, previous)) {
      return false;
    }

    this._sentPayload[key] = current;
    return true;
  }

  getTemperatureHasChanged() {
    return this._hasChanged("temperature");
  }

  getWindSpeedHasChanged() {
    return this._hasChanged("windspeed");
  }

  getPrecipitationHasChanged() {
    return this._hasChanged("precipitation");
  }

  getBatteryChargeHasChanged() {
    return this._hasChanged("battery_charge");
  }

  getChargingHasChanged() {
    return this._hasChanged("charging");
  }

  getWeatherConditionsHasChanged() {
    const current = {};
    const previous = {};

    for (const key of WEATHER_KEYS) {
      current[key] = this._payload?.[key];
      previous[key] = this._sentPayload?.[key];
    }

    if (sameValue(current, previous)) {
      return false;
    }

    for (const key of WEATHER_KEYS) {
      this._sentPayload[key] = this._payload?.[key];
    }

    return true;
  }

  static fromHassEntity(hass, entityId, fallback = null) {
    const entity = getEntityState(hass, entityId);

    if (!entity) {
      return fallback;
    }

    const number = toNumber(entity.state, null);

    if (number !== null) {
      return number;
    }

    return toBoolean(entity.state, fallback);
  }
}

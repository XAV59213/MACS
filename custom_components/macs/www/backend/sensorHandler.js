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
  weather_conditions: {
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
  }
});

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
  pouring: "pouring",
  rainy: "rainy",
  snow: "snowy",
  snowy: "snowy",
  "snowy-rainy": "snowy",
  sunny: "sunny",
  windy: "windy",
  "windy-variant": "windy",
  exceptional: "exceptional"
};

export class SensorHandler {
  constructor(hass, config = {}) {
    this.hass = hass;
    this.config = config || {};
  }

  update(hass, config = null) {
    this.hass = hass;

    if (config) {
      this.config = config;
    }
  }

  getValues() {
    const values = structuredCloneSafe(DEFAULT_SENSOR_VALUES);

    values.temperature = this.getTemperature();
    values.windspeed = this.getWindSpeed();
    values.precipitation = this.getPrecipitation();
    values.battery_charge = this.getBatteryCharge();
    values.charging = this.getCharging();
    values.weather_conditions = this.getWeatherConditions();

    return values;
  }

  getTemperature() {
    const entityId =
      normalizeEntityId(this.config.temperature_sensor_entity) ||
      normalizeEntityId(this.config.temperature_entity) ||
      normalizeEntityId(this.config.temperature_sensor);

    const value = getEntityNumericState(this.hass, entityId, null);

    if (value === null) {
      return null;
    }

    return clampNumber(value, -50, 80, null);
  }

  getWindSpeed() {
    const entityId =
      normalizeEntityId(this.config.windspeed_sensor_entity) ||
      normalizeEntityId(this.config.wind_speed_sensor_entity) ||
      normalizeEntityId(this.config.windspeed_entity) ||
      normalizeEntityId(this.config.wind_speed_entity) ||
      normalizeEntityId(this.config.wind_sensor_entity);

    const value = getEntityNumericState(this.hass, entityId, null);

    if (value === null) {
      return null;
    }

    const entity = getEntityState(this.hass, entityId);
    const unit = String(entity?.attributes?.unit_of_measurement || "").toLowerCase();

    let kmh = value;

    if (unit.includes("m/s")) {
      kmh = value * 3.6;
    } else if (unit.includes("mph")) {
      kmh = value * 1.609344;
    } else if (unit.includes("kn") || unit.includes("kt")) {
      kmh = value * 1.852;
    }

    return clampNumber(kmh, 0, 300, null);
  }

  getPrecipitation() {
    const entityId =
      normalizeEntityId(this.config.precipitation_sensor_entity) ||
      normalizeEntityId(this.config.rain_sensor_entity) ||
      normalizeEntityId(this.config.precipitation_entity);

    const value = getEntityNumericState(this.hass, entityId, null);

    if (value === null) {
      return null;
    }

    return clampNumber(value, 0, 500, null);
  }

  getBatteryCharge() {
    const entityId =
      normalizeEntityId(this.config.battery_charge_sensor_entity) ||
      normalizeEntityId(this.config.battery_sensor_entity) ||
      normalizeEntityId(this.config.battery_entity);

    const value = getEntityNumericState(this.hass, entityId, null);

    if (value === null) {
      return null;
    }

    return clampNumber(value, 0, 100, null);
  }

  getCharging() {
    const entityId =
      normalizeEntityId(this.config.charging_sensor_entity) ||
      normalizeEntityId(this.config.charging_binary_sensor_entity) ||
      normalizeEntityId(this.config.charging_entity) ||
      normalizeEntityId(this.config.battery_state_sensor_entity);

    if (!entityId) {
      return false;
    }

    return getEntityBooleanState(this.hass, entityId, false);
  }

  getWeatherConditions() {
    const result = { ...DEFAULT_SENSOR_VALUES.weather_conditions };

    this.applyWeatherEntity(result);
    this.applyWeatherBooleans(result);
    this.applyWeatherFromSensorValues(result);

    return result;
  }

  applyWeatherEntity(result) {
    const entityId =
      normalizeEntityId(this.config.weather_entity) ||
      normalizeEntityId(this.config.weather_sensor_entity) ||
      normalizeEntityId(this.config.weather_conditions_entity);

    const entity = getEntityState(this.hass, entityId);

    if (!entity) {
      return;
    }

    const state = String(entity.state || "").toLowerCase().trim();
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
  }

  applyWeatherBooleans(result) {
    const configKeys = {
      snowy: ["snowy_entity", "weather_conditions_snowy_entity"],
      cloudy: ["cloudy_entity", "weather_conditions_cloudy_entity"],
      rainy: ["rainy_entity", "weather_conditions_rainy_entity"],
      windy: ["windy_entity", "weather_conditions_windy_entity"],
      sunny: ["sunny_entity", "weather_conditions_sunny_entity"],
      stormy: ["stormy_entity", "weather_conditions_stormy_entity"],
      foggy: ["foggy_entity", "weather_conditions_foggy_entity"],
      hail: ["hail_entity", "weather_conditions_hail_entity"],
      lightning: ["lightning_entity", "weather_conditions_lightning_entity"],
      partlycloudy: ["partlycloudy_entity", "weather_conditions_partlycloudy_entity"],
      pouring: ["pouring_entity", "weather_conditions_pouring_entity"],
      clear_night: ["clear_night_entity", "weather_conditions_clear_night_entity"],
      exceptional: ["exceptional_entity", "weather_conditions_exceptional_entity"]
    };

    for (const [condition, keys] of Object.entries(configKeys)) {
      for (const key of keys) {
        const entityId = normalizeEntityId(this.config[key]);

        if (!entityId) {
          continue;
        }

        result[condition] = getEntityBooleanState(this.hass, entityId, false);
        break;
      }
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

function structuredCloneSafe(value) {
  try {
    return structuredClone(value);
  } catch {
    return JSON.parse(JSON.stringify(value));
  }
}

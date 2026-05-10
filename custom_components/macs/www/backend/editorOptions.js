/**
 * Editor Options
 * --------------
 * Populates combo boxes for use by the card editor.
 * Obtains User Inputs with Fallbacks to Default Values
 * Syncs UI with Config
 */

import { DEFAULTS } from "../shared/constants.js";

//###############################################################################################
//                         Element / Config Keys
//###############################################################################################

// Assistant Satellite
const assistSatelitteKeys = {
	enabled: "assist_satellite_enabled",
	select: "assist_satellite_select",
	entity: "assist_satellite_entity",
	custom: "assist_satellite_custom"
};

// Assistant Pipeline
const assistPipelineKeys = {
	enabled: "assist_pipeline_enabled",
	select: "assist_pipeline_select",
	entity: "assist_pipeline_entity",
	custom: "assist_pipeline_custom"
};

// Temperature
const temperatureKeys = {
	enabled: "temperature_sensor_enabled",
	select: "temperature_sensor_select",
	entity: "temperature_sensor_entity",
	custom: "temperature_sensor_custom",
	unit: "temperature_sensor_unit",
	min: "temperature_sensor_min",
	max: "temperature_sensor_max"
};

// Windspeed
const windspeedKeys = {
	enabled: "wind_sensor_enabled",
	select: "wind_sensor_select",
	entity: "wind_sensor_entity",
	custom: "wind_sensor_custom",
	unit: "wind_sensor_unit",
	min: "wind_sensor_min",
	max: "wind_sensor_max"
};

// Rainfall
const precipitationKeys = {
	enabled: "precipitation_sensor_enabled",
	select: "precipitation_sensor_select",
	entity: "precipitation_sensor_entity",
	custom: "precipitation_sensor_custom",
	unit: "precipitation_sensor_unit",
	min: "precipitation_sensor_min",
	max: "precipitation_sensor_max"
};

// Weather Condition
const weatherConditionKeys = {
	enabled: "weather_conditions_enabled",
	select: "weather_conditions_select",
	entity: "weather_conditions_entity",
	custom: "weather_conditions_custom"
};

// Battery charge %
const batteryChargeKeys = {
	enabled: "battery_charge_sensor_enabled",
	select: "battery_charge_sensor_select",
	entity: "battery_charge_sensor_entity",
	custom: "battery_charge_sensor_custom",
	unit: "battery_charge_sensor_unit",
	min: "battery_charge_sensor_min",
	max: "battery_charge_sensor_max"
};

// Battery is Plugged in
const batteryStateKeys = {
	enabled: "battery_state_sensor_enabled",
	select: "battery_state_sensor_select",
	entity: "battery_state_sensor_entity",
	custom: "battery_state_sensor_custom"
};

// Kiosk Mode
const autoBrightnessKeys = {
	enabled: "auto_brightness_enabled",
	min: "auto_brightness_min",
	max: "auto_brightness_max",
	kioskAnimations: "auto_brightness_pause_animations",
	kioskTimeout: "auto_brightness_timeout_minutes"
};

//###############################################################################################
//                         Get lists for Combo Boxes
//###############################################################################################

export async function getComboboxItems(hass) {
	const comboxItems = {};

	comboxItems.satelliteItems = searchForEntities("assist_satellite", "keys", hass);

	const pipelineItems = await searchForPipelines(hass);
	comboxItems.preferred = pipelineItems.preferred;
	comboxItems.pipelineItems = pipelineItems.pipelineItems;

	comboxItems.temperatureItems = searchForEntities(
		"sensor",
		"entries",
		hass,
		["temperature"],
		["temp", "temperature"]
	);

	comboxItems.windItems = searchForEntities(
		"sensor",
		"entries",
		hass,
		["wind_speed"],
		["wind"]
	);

	comboxItems.precipitationItems = searchForEntities(
		"sensor",
		"entries",
		hass,
		["precipitation", "precipitation_intensity", "precipitation_probability"],
		["rain", "precip", "precipitation"]
	);

	comboxItems.weatherConditionItems = searchForEntities("weather", "entries", hass);

	comboxItems.batteryItems = searchForEntities(
		"sensor",
		"entries",
		hass,
		["battery"],
		["battery", "charge", "batt"]
	);

	const batteryStateSensors = searchForEntities(
		"sensor",
		"entries",
		hass,
		["battery", "battery_charging", "power", "plug"],
		[
			"battery_state",
			"battery state",
			"is_charging",
			"charging",
			"charge",
			"charge_state",
			"charger",
			"plugged",
			"ac power",
			"power"
		]
	);

	const batteryStateBinarySensors = searchForEntities(
		"binary_sensor",
		"entries",
		hass,
		["battery", "battery_charging", "power", "plug"],
		[
			"battery_state",
			"battery state",
			"is_charging",
			"charging",
			"charge",
			"charge_state",
			"charger",
			"plugged",
			"ac power",
			"power"
		]
	);

	comboxItems.batteryStateItems = mergeComboboxItems(
		batteryStateSensors,
		batteryStateBinarySensors
	);

	return comboxItems;
}

function searchForEntities(
	needle,
	haystack,
	hass,
	possibleDeviceClasses = null,
	possibleNames = null
) {
	if (!hass || !hass.states) {
		return [];
	}

	const list = [{ id: "custom", name: "Custom" }];
	let entities = [];

	if (haystack === "keys") {
		entities = Object.keys(hass.states);
	} else if (haystack === "entries") {
		entities = Object.entries(hass.states);
	}

	for (let i = 0; i < entities.length; i++) {
		let id;
		let state;

		if (haystack === "keys") {
			id = entities[i];
			state = hass.states[id];
		} else {
			id = entities[i][0];
			state = entities[i][1];
		}

		if (!id || id.indexOf(needle + ".") !== 0) {
			continue;
		}

		let include = false;

		if (possibleDeviceClasses === null && possibleNames === null) {
			include = true;
		} else {
			if (possibleDeviceClasses !== null && possibleDeviceClasses.length > 0) {
				const deviceClass = String(
					(state && state.attributes && state.attributes.device_class) || ""
				).toLowerCase();

				for (let c = 0; c < possibleDeviceClasses.length; c++) {
					if (deviceClass === possibleDeviceClasses[c].toLowerCase()) {
						include = true;
						break;
					}
				}
			}

			if (possibleNames !== null && possibleNames.length > 0 && include === false) {
				const name = (state && state.attributes && state.attributes.friendly_name) || "";
				const hay = (id + " " + name).toLowerCase();

				for (let c = 0; c < possibleNames.length; c++) {
					if (hay.indexOf(possibleNames[c].toLowerCase()) !== -1) {
						include = true;
						break;
					}
				}
			}
		}

		if (include) {
			const name = (state && state.attributes && state.attributes.friendly_name) || id;
			list.push({ id, name: String(name) });
		}
	}

	const custom = list.find((item) => item.id === "custom");
	const sorted = list.filter((item) => item.id !== "custom");

	sorted.sort((a, b) => {
		return a.name.localeCompare(b.name);
	});

	if (custom) {
		sorted.unshift(custom);
	}

	return sorted;
}

function mergeComboboxItems(...lists) {
	const byId = new Map();

	lists.forEach((items) => {
		(items || []).forEach((item) => {
			if (!item || typeof item.id === "undefined") return;
			if (item.id === "custom") return;

			if (!byId.has(item.id)) {
				byId.set(item.id, item);
			}
		});
	});

	const entries = Array.from(byId.values());

	entries.sort((a, b) => {
		return String(a.name || a.id).localeCompare(String(b.name || b.id));
	});

	return [{ id: "custom", name: "Custom" }, ...entries];
}

async function searchForPipelines(hass) {
	const result = {
		pipelineItems: [{ id: "custom", name: "Custom" }],
		preferred: ""
	};

	if (!hass) return result;

	try {
		const res = await hass.callWS({ type: "assist_pipeline/pipeline/list" });

		const pipelines = Array.isArray(res?.pipelines) ? res.pipelines : [];
		result.preferred = String(res?.preferred_pipeline || "");

		for (let i = 0; i < pipelines.length; i++) {
			const p = pipelines[i] || {};
			const id = String(p.id || "");

			if (!id) continue;

			const name = String(p.name || p.id || "Unnamed");
			result.pipelineItems.push({ id, name });
		}
	} catch (_) {
		// Do nothing, editor still works with Custom
	}

	return result;
}

//###############################################################################################
//                         Read Config from UI
//###############################################################################################

export function readInputs(shadowRoot, event, config) {
	if (!shadowRoot) {
		return {
			assist_satellite_enabled: !!(config && config.assist_satellite_enabled),
			assist_satellite_entity: String((config && config.assist_satellite_entity) || ""),
			assist_satellite_custom: !!(config && config.assist_satellite_custom),

			assist_pipeline_enabled: !!(config && config.assist_pipeline_enabled),
			assist_pipeline_entity: String((config && config.assist_pipeline_entity) || ""),
			assist_pipeline_custom: !!(config && config.assist_pipeline_custom),

			temperature_sensor_enabled: !!(config && config.temperature_sensor_enabled),
			temperature_sensor_entity: String((config && config.temperature_sensor_entity) ?? ""),
			temperature_sensor_custom: !!(config && config.temperature_sensor_custom),
			temperature_sensor_unit: String((config && config.temperature_sensor_unit) ?? ""),
			temperature_sensor_min: String((config && config.temperature_sensor_min) ?? ""),
			temperature_sensor_max: String((config && config.temperature_sensor_max) ?? ""),

			wind_sensor_enabled: !!(config && config.wind_sensor_enabled),
			wind_sensor_entity: String((config && config.wind_sensor_entity) ?? ""),
			wind_sensor_custom: !!(config && config.wind_sensor_custom),
			wind_sensor_unit: String((config && config.wind_sensor_unit) ?? ""),
			wind_sensor_min: String((config && config.wind_sensor_min) ?? ""),
			wind_sensor_max: String((config && config.wind_sensor_max) ?? ""),

			precipitation_sensor_enabled: !!(config && config.precipitation_sensor_enabled),
			precipitation_sensor_entity: String((config && config.precipitation_sensor_entity) ?? ""),
			precipitation_sensor_custom: !!(config && config.precipitation_sensor_custom),
			precipitation_sensor_unit: String((config && config.precipitation_sensor_unit) ?? ""),
			precipitation_sensor_min: String((config && config.precipitation_sensor_min) ?? ""),
			precipitation_sensor_max: String((config && config.precipitation_sensor_max) ?? ""),

			weather_conditions_enabled: !!(config && config.weather_conditions_enabled),
			weather_conditions_entity: String((config && config.weather_conditions_entity) ?? ""),
			weather_conditions_custom: !!(config && config.weather_conditions_custom),

			battery_charge_sensor_enabled: !!(config && config.battery_charge_sensor_enabled),
			battery_charge_sensor_entity: String((config && config.battery_charge_sensor_entity) ?? ""),
			battery_charge_sensor_custom: !!(config && config.battery_charge_sensor_custom),
			battery_charge_sensor_unit: String((config && config.battery_charge_sensor_unit) ?? "%"),
			battery_charge_sensor_min: String((config && config.battery_charge_sensor_min) ?? ""),
			battery_charge_sensor_max: String((config && config.battery_charge_sensor_max) ?? ""),

			battery_state_sensor_enabled: !!(config && config.battery_state_sensor_enabled),
			battery_state_sensor_entity: String((config && config.battery_state_sensor_entity) ?? ""),
			battery_state_sensor_custom: !!(config && config.battery_state_sensor_custom),

			auto_brightness_enabled: !!(config && config.auto_brightness_enabled),
			auto_brightness_timeout_minutes: String((config && config.auto_brightness_timeout_minutes) ?? ""),
			auto_brightness_min: String((config && config.auto_brightness_min) ?? ""),
			auto_brightness_max: String((config && config.auto_brightness_max) ?? ""),
			auto_brightness_pause_animations: !!(config && config.auto_brightness_pause_animations)
		};
	}

	return {
		...getUserInputs(shadowRoot, event, config, assistSatelitteKeys),
		...getUserInputs(shadowRoot, event, config, assistPipelineKeys),
		...getUserInputs(shadowRoot, event, config, temperatureKeys),
		...getUserInputs(shadowRoot, event, config, windspeedKeys),
		...getUserInputs(shadowRoot, event, config, precipitationKeys),
		...getUserInputs(shadowRoot, event, config, weatherConditionKeys),
		...getUserInputs(shadowRoot, event, config, batteryChargeKeys),
		...getUserInputs(shadowRoot, event, config, batteryStateKeys),
		...getUserInputs(shadowRoot, event, config, autoBrightnessKeys)
	};
}

function getUserInputs(shadowRoot, event, config, ids) {
	const enabledKey = ids.enabled || false;
	const selectKey = ids.select || false;
	const customKey = ids.custom || false;
	const entityKey = ids.entity || false;
	const unitKey = ids.unit || false;
	const minKey = ids.min || false;
	const maxKey = ids.max || false;
	const kioskAnimKey = ids.kioskAnimations || false;
	const kioskTimeoutKey = ids.kioskTimeout || false;

	const elemEnabled = enabledKey ? shadowRoot.getElementById(enabledKey) : null;
	const elemSelect = selectKey ? shadowRoot.getElementById(selectKey) : null;
	const elemEntityInput = entityKey ? shadowRoot.getElementById(entityKey) : null;
	const elemUnit = unitKey ? shadowRoot.getElementById(unitKey) : null;
	const elemMin = minKey ? shadowRoot.getElementById(minKey) : null;
	const elemMax = maxKey ? shadowRoot.getElementById(maxKey) : null;
	const elemKioskAnims = kioskAnimKey ? shadowRoot.getElementById(kioskAnimKey) : null;
	const elemKioskTimeout = kioskTimeoutKey ? shadowRoot.getElementById(kioskTimeoutKey) : null;

	const enabled = getToggleValue(elemEnabled, event, config && config[enabledKey]);

	const payload = {};

	if (enabledKey) {
		payload[enabledKey] = enabled;
	}

	if (selectKey && entityKey) {
		const selectValue = getComboboxValue(elemSelect, event);
		const isCustom = selectValue === "custom";
		const customEntityValue = elemEntityInput ? String(elemEntityInput.value || "").trim() : "";
		const entityVal = isCustom ? customEntityValue : selectValue;

		payload[entityKey] = entityVal;

		if (customKey) {
			payload[customKey] = isCustom;
		}

		if (customKey && entityVal === "") {
			payload[customKey] = false;
		}
	}

	if (unitKey) {
		payload[unitKey] = String(
			elemUnit ? getComboboxValue(elemUnit, event) : ((config && config[unitKey]) || "")
		);
	}

	if (minKey) {
		payload[minKey] = getNumberOrDefault(elemMin);
	}

	if (maxKey) {
		payload[maxKey] = getNumberOrDefault(elemMax);
	}

	if (kioskTimeoutKey) {
		payload[kioskTimeoutKey] = getNumberOrDefault(elemKioskTimeout);
	}

	if (kioskAnimKey) {
		payload[kioskAnimKey] = getToggleValue(
			elemKioskAnims,
			event,
			config && config[kioskAnimKey]
		);
	}

	Object.keys(payload).forEach((key) => {
		if (Object.prototype.hasOwnProperty.call(DEFAULTS, key) && payload[key] === "") {
			delete payload[key];
		}
	});

	return payload;
}

function getComboboxValue(el, e) {
	if (!el) return "";

	if (e && e.currentTarget === el && e.detail) {
		if (typeof e.detail.value !== "undefined") {
			return String(e.detail.value || "");
		}

		if (typeof e.detail.selected !== "undefined") {
			return String(e.detail.selected || "");
		}
	}

	if (el.selectedItem) {
		if (typeof el.selectedItem.value !== "undefined") {
			return String(el.selectedItem.value || "");
		}

		if (typeof el.selectedItem.id !== "undefined") {
			return String(el.selectedItem.id || "");
		}
	}

	if (typeof el.value !== "undefined") {
		return String(el.value || "");
	}

	return "";
}

function getToggleValue(elem, event, fallback) {
	if (elem) {
		if (event && event.currentTarget === elem) {
			if (event.detail && typeof event.detail.value !== "undefined") {
				return !!event.detail.value;
			}

			if (event.detail && typeof event.detail.checked !== "undefined") {
				return !!event.detail.checked;
			}
		}

		if (typeof elem.checked !== "undefined") {
			return !!elem.checked;
		}
	}

	return !!fallback;
}

function getNumberOrDefault(elem) {
	if (!elem) return "";

	const val = elem.value;

	if (val === "" || val === null || typeof val === "undefined") {
		return "";
	}

	const num = Number(val);

	return Number.isFinite(num) ? num : "";
}

//###############################################################################################
//                         Sync UI to Config
//###############################################################################################

export function syncInputs(
	shadowRoot,
	config,
	satelliteItems,
	pipelineItems,
	temperatureItems,
	windspeedItems,
	precipitationItems,
	weatherConditionItems,
	batteryChargeItems,
	batteryStateItems,
	autoBrightnessItems
) {
	syncInputGroup(shadowRoot, config, satelliteItems, assistSatelitteKeys);
	syncInputGroup(shadowRoot, config, pipelineItems, assistPipelineKeys);
	syncInputGroup(shadowRoot, config, temperatureItems, temperatureKeys);
	syncInputGroup(shadowRoot, config, windspeedItems, windspeedKeys);
	syncInputGroup(shadowRoot, config, precipitationItems, precipitationKeys);
	syncInputGroup(shadowRoot, config, weatherConditionItems, weatherConditionKeys);
	syncInputGroup(shadowRoot, config, batteryChargeItems, batteryChargeKeys);
	syncInputGroup(shadowRoot, config, batteryStateItems, batteryStateKeys);
	syncInputGroup(shadowRoot, config, autoBrightnessItems, autoBrightnessKeys);
}

export function syncInputGroup(shadowRoot, config, items, keys) {
	if (!shadowRoot) return;

	const enabledKey = keys.enabled || false;
	const selectKey = keys.select || false;
	const customKey = keys.custom || false;
	const entityKey = keys.entity || false;
	const unitKey = keys.unit || false;
	const minKey = keys.min || false;
	const maxKey = keys.max || false;
	const kioskAnimKey = keys.kioskAnimations || false;
	const kioskTimeoutKey = keys.kioskTimeout || false;

	const elemEnabled = enabledKey ? shadowRoot.getElementById(enabledKey) : null;
	const elemSelect = selectKey ? shadowRoot.getElementById(selectKey) : null;
	const elemEntity = entityKey ? shadowRoot.getElementById(entityKey) : null;
	const elemUnit = unitKey ? shadowRoot.getElementById(unitKey) : null;
	const elemMin = minKey ? shadowRoot.getElementById(minKey) : null;
	const elemMax = maxKey ? shadowRoot.getElementById(maxKey) : null;
	const elemKioskAnims = kioskAnimKey ? shadowRoot.getElementById(kioskAnimKey) : null;
	const elemKioskTimeout = kioskTimeoutKey ? shadowRoot.getElementById(kioskTimeoutKey) : null;

	const enabled = !!(config && config[enabledKey]);

	setToggleState(elemEnabled, enabledKey, config);
	setToggleState(elemKioskAnims, kioskAnimKey, config);

	setSelectedValue(elemUnit, unitKey, config);

	setNumericValue(elemMin, minKey, config);
	setNumericValue(elemMax, maxKey, config);
	setNumericValue(elemKioskTimeout, kioskTimeoutKey, config);

	setEnabledDisabled(elemSelect, selectKey, enabled);
	setEnabledDisabled(elemEntity, entityKey, enabled);
	setEnabledDisabled(elemUnit, unitKey, enabled);
	setEnabledDisabled(elemMin, minKey, enabled);
	setEnabledDisabled(elemMax, maxKey, enabled);
	setEnabledDisabled(elemKioskAnims, kioskAnimKey, enabled);
	setEnabledDisabled(elemKioskTimeout, kioskTimeoutKey, enabled);

	if (selectKey && elemSelect) {
		const entityId = String((config && config[entityKey]) || "");

		const knownSelect =
			Array.isArray(items) &&
			items.some((s) => s && s.id === entityId && s.id !== "custom");

		const hasEntity = entityId !== "";
		const isCustom = hasEntity && (!!(config && config[customKey]) || !knownSelect);
		const nextSelect = isCustom ? "custom" : entityId;

		if (elemSelect.value !== nextSelect) {
			elemSelect.value = nextSelect;
		}

		if (typeof elemSelect.requestUpdate === "function") {
			elemSelect.requestUpdate();
		}

		if (entityKey && elemEntity) {
			if (elemEntity.value !== entityId) {
				elemEntity.value = entityId;
			}

			const entityEnable = enabled && isCustom;
			elemEntity.disabled = !entityEnable;
		}
	}
}

function setToggleState(elem, key, config) {
	if (!key || !elem) return;

	const val = !!(config && config[key]);

	if (elem.checked !== val) {
		elem.checked = val;
	}
}

function setSelectedValue(elem, key, config) {
	if (!key || !elem) return;

	const val = String((config && config[key]) || "");

	if (elem.value !== val) {
		elem.value = val;
	}

	if (typeof elem.requestUpdate === "function") {
		elem.requestUpdate();
	}
}

function setNumericValue(elem, key, config) {
	if (!key || !elem) return;

	const val = config && config[key];

	if (val === null || typeof val === "undefined") {
		if (elem.value !== "") {
			elem.value = "";
		}
		return;
	}

	if (elem.value !== String(val)) {
		elem.value = String(val);
	}
}

function setEnabledDisabled(elem, key, enabled) {
	if (!key || !elem) return;

	const disabled = !enabled;

	if (elem.disabled !== disabled) {
		elem.disabled = disabled;
	}
}

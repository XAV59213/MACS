from __future__ import annotations

import json
from functools import partial
from pathlib import Path
from uuid import uuid4

import voluptuous as vol

from homeassistant.components.http import StaticPathConfig
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant, ServiceCall
from homeassistant.helpers import config_validation as cv
from homeassistant.helpers import entity_registry as er
from homeassistant.util import dt as dt_util

from .const import (
    ATTR_ANIMATIONS_ENABLED,
    ATTR_BATTERY_CHARGE,
    ATTR_BRIGHTNESS,
    ATTR_CHARGING,
    ATTR_MESSAGE,
    ATTR_MOOD,
    ATTR_PRECIPITATION,
    ATTR_TEMPERATURE,
    ATTR_WEATHER_CONDITIONS_CLEAR_NIGHT,
    ATTR_WEATHER_CONDITIONS_CLOUDY,
    ATTR_WEATHER_CONDITIONS_EXCEPTIONAL,
    ATTR_WEATHER_CONDITIONS_FOGGY,
    ATTR_WEATHER_CONDITIONS_HAIL,
    ATTR_WEATHER_CONDITIONS_LIGHTNING,
    ATTR_WEATHER_CONDITIONS_PARTLYCLOUDY,
    ATTR_WEATHER_CONDITIONS_POURING,
    ATTR_WEATHER_CONDITIONS_RAINY,
    ATTR_WEATHER_CONDITIONS_SNOWY,
    ATTR_WEATHER_CONDITIONS_STORMY,
    ATTR_WEATHER_CONDITIONS_SUNNY,
    ATTR_WEATHER_CONDITIONS_WINDY,
    ATTR_WINDSPEED,
    DEFAULT_ANIMATIONS_ENABLED,
    DEFAULT_BATTERY_CHARGE,
    DEFAULT_BRIGHTNESS,
    DEFAULT_CHARGING,
    DEFAULT_MOOD,
    DEFAULT_PRECIPITATION,
    DEFAULT_TEMPERATURE,
    DEFAULT_WINDSPEED,
    DOMAIN,
    EVENT_MESSAGE,
    MOODS,
    SERVICE_SEND_ASSISTANT_MESSAGE,
    SERVICE_SEND_USER_MESSAGE,
    SERVICE_SET_ANIMATIONS_ENABLED,
    SERVICE_SET_BATTERY_CHARGE,
    SERVICE_SET_BRIGHTNESS,
    SERVICE_SET_CHARGING,
    SERVICE_SET_MOOD,
    SERVICE_SET_PRECIPITATION,
    SERVICE_SET_TEMPERATURE,
    SERVICE_SET_WEATHER_CONDITIONS_CLEAR_NIGHT,
    SERVICE_SET_WEATHER_CONDITIONS_CLOUDY,
    SERVICE_SET_WEATHER_CONDITIONS_EXCEPTIONAL,
    SERVICE_SET_WEATHER_CONDITIONS_FOGGY,
    SERVICE_SET_WEATHER_CONDITIONS_HAIL,
    SERVICE_SET_WEATHER_CONDITIONS_LIGHTNING,
    SERVICE_SET_WEATHER_CONDITIONS_PARTLYCLOUDY,
    SERVICE_SET_WEATHER_CONDITIONS_POURING,
    SERVICE_SET_WEATHER_CONDITIONS_RAINY,
    SERVICE_SET_WEATHER_CONDITIONS_SNOWY,
    SERVICE_SET_WEATHER_CONDITIONS_STORMY,
    SERVICE_SET_WEATHER_CONDITIONS_SUNNY,
    SERVICE_SET_WEATHER_CONDITIONS_WINDY,
    SERVICE_SET_WINDSPEED,
)

CONFIG_SCHEMA = cv.config_entry_only_config_schema(DOMAIN)

PLATFORMS: list[str] = ["select", "number", "switch"]

RESOURCE_BASE_URL = "/hacsfiles/macs-xav/macs.js"
RESOURCE_TYPE = "module"


DEFAULT_ENTRY_STATE = {
    ATTR_MOOD: DEFAULT_MOOD,
    ATTR_BRIGHTNESS: DEFAULT_BRIGHTNESS,
    ATTR_TEMPERATURE: DEFAULT_TEMPERATURE,
    ATTR_WINDSPEED: DEFAULT_WINDSPEED,
    ATTR_PRECIPITATION: DEFAULT_PRECIPITATION,
    ATTR_BATTERY_CHARGE: DEFAULT_BATTERY_CHARGE,
    ATTR_ANIMATIONS_ENABLED: DEFAULT_ANIMATIONS_ENABLED,
    ATTR_CHARGING: DEFAULT_CHARGING,
    ATTR_WEATHER_CONDITIONS_SNOWY: False,
    ATTR_WEATHER_CONDITIONS_CLOUDY: False,
    ATTR_WEATHER_CONDITIONS_RAINY: False,
    ATTR_WEATHER_CONDITIONS_WINDY: False,
    ATTR_WEATHER_CONDITIONS_SUNNY: False,
    ATTR_WEATHER_CONDITIONS_STORMY: False,
    ATTR_WEATHER_CONDITIONS_FOGGY: False,
    ATTR_WEATHER_CONDITIONS_HAIL: False,
    ATTR_WEATHER_CONDITIONS_LIGHTNING: False,
    ATTR_WEATHER_CONDITIONS_PARTLYCLOUDY: False,
    ATTR_WEATHER_CONDITIONS_POURING: False,
    ATTR_WEATHER_CONDITIONS_CLEAR_NIGHT: False,
    ATTR_WEATHER_CONDITIONS_EXCEPTIONAL: False,
}


ENTITY_TARGETS = {
    "macs_mood": "select.macs_mood",
    "macs_debug": "select.macs_debug",
    "macs_brightness": "number.macs_brightness",
    "macs_battery_charge": "number.macs_battery_charge",
    "macs_temperature": "number.macs_temperature",
    "macs_windspeed": "number.macs_windspeed",
    "macs_precipitation": "number.macs_precipitation",
    "macs_animations_enabled": "switch.macs_animations_enabled",
    "macs_charging": "switch.macs_charging",
    "macs_weather_conditions_snowy": "switch.macs_weather_conditions_snowy",
    "macs_weather_conditions_cloudy": "switch.macs_weather_conditions_cloudy",
    "macs_weather_conditions_rainy": "switch.macs_weather_conditions_rainy",
    "macs_weather_conditions_windy": "switch.macs_weather_conditions_windy",
    "macs_weather_conditions_sunny": "switch.macs_weather_conditions_sunny",
    "macs_weather_conditions_stormy": "switch.macs_weather_conditions_stormy",
    "macs_weather_conditions_foggy": "switch.macs_weather_conditions_foggy",
    "macs_weather_conditions_hail": "switch.macs_weather_conditions_hail",
    "macs_weather_conditions_lightning": "switch.macs_weather_conditions_lightning",
    "macs_weather_conditions_partlycloudy": "switch.macs_weather_conditions_partlycloudy",
    "macs_weather_conditions_pouring": "switch.macs_weather_conditions_pouring",
    "macs_weather_conditions_clear_night": "switch.macs_weather_conditions_clear_night",
    "macs_weather_conditions_exceptional": "switch.macs_weather_conditions_exceptional",
}


async def _integration_version(hass: HomeAssistant) -> str:
    """Read integration version from manifest.json."""
    try:
        manifest_path = Path(__file__).parent / "manifest.json"
        read_manifest = partial(manifest_path.read_text, encoding="utf-8")
        manifest_text = await hass.async_add_executor_job(read_manifest)
        manifest = json.loads(manifest_text)
        return str(manifest.get("version", "0"))
    except Exception:
        return "0"


async def _ensure_lovelace_resource(hass: HomeAssistant) -> None:
    """Register or update the MACS Lovelace resource."""
    lovelace = hass.data.get("lovelace")
    resources = getattr(lovelace, "resources", None) if lovelace else None

    if not resources:
        return

    version = await _integration_version(hass)
    desired_url = f"{RESOURCE_BASE_URL}?v={version}"

    existing = None
    for item in resources.async_items():
        url = str(item.get("url", ""))
        if url.split("?", 1)[0] == RESOURCE_BASE_URL:
            existing = item
            break

    if existing:
        if existing.get("url") != desired_url or existing.get("res_type") != RESOURCE_TYPE:
            await resources.async_update_item(
                existing["id"],
                {
                    "res_type": RESOURCE_TYPE,
                    "url": desired_url,
                },
            )
    else:
        await resources.async_create_item(
            {
                    "res_type": RESOURCE_TYPE,
                    "url": desired_url,
            }
        )


async def async_setup(hass: HomeAssistant, config: dict) -> bool:
    """Set up MACS."""
    return True


def _ensure_entry_state(hass: HomeAssistant, entry: ConfigEntry) -> None:
    """Create the shared state store used by select/number/switch entities."""
    hass.data.setdefault(DOMAIN, {})
    hass.data[DOMAIN].setdefault(entry.entry_id, {})

    for key, default_value in DEFAULT_ENTRY_STATE.items():
        hass.data[DOMAIN][entry.entry_id].setdefault(key, default_value)


def _legacy_unique_ids_for(canonical_unique_id: str, entry: ConfigEntry) -> set[str]:
    """Return all possible old unique_id formats for a MACS entity."""
    if not canonical_unique_id.startswith("macs_"):
        return {canonical_unique_id}

    raw_key = canonical_unique_id.removeprefix("macs_")

    return {
        canonical_unique_id,
        raw_key,
        f"{entry.entry_id}_{raw_key}",
        f"{entry.entry_id}_{canonical_unique_id}",
    }


def _find_entity_id_by_unique_id(
    hass: HomeAssistant,
    unique_id: str,
    entry: ConfigEntry | None = None,
) -> str | None:
    """Find a MACS entity by current or legacy unique_id."""
    registry = er.async_get(hass)

    possible_ids = {unique_id}
    if entry is not None:
        possible_ids |= _legacy_unique_ids_for(unique_id, entry)

    for entity in registry.entities.values():
        if entity.platform != DOMAIN:
            continue

        if entry is not None and entity.config_entry_id != entry.entry_id:
            continue

        if entity.unique_id in possible_ids:
            return entity.entity_id

    # Fallback pour les anciennes installations :
    # si l'ancien unique_id finit par _animations_enabled, _brightness, etc.
    short_key = unique_id.removeprefix("macs_")

    for entity in registry.entities.values():
        if entity.platform != DOMAIN:
            continue

        if entry is not None and entity.config_entry_id != entry.entry_id:
            continue

        entity_unique_id = str(entity.unique_id or "")

        if entity_unique_id.endswith(f"_{short_key}") or entity_unique_id.endswith(unique_id):
            return entity.entity_id

    return None


def _migrate_entity_id(
    hass: HomeAssistant,
    entry: ConfigEntry,
    canonical_unique_id: str,
    desired_entity_id: str,
) -> None:
    """Rename old generated entity ids to clean MACS entity ids."""
    registry = er.async_get(hass)

    possible_ids = _legacy_unique_ids_for(canonical_unique_id, entry)

    entry_obj = None
    for entity in registry.entities.values():
        if entity.platform != DOMAIN:
            continue

        if entity.config_entry_id != entry.entry_id:
            continue

        entity_unique_id = str(entity.unique_id or "")
        short_key = canonical_unique_id.removeprefix("macs_")

        if (
            entity_unique_id in possible_ids
            or entity_unique_id.endswith(f"_{short_key}")
            or entity_unique_id.endswith(canonical_unique_id)
        ):
            entry_obj = entity
            break

    if not entry_obj:
        return

    if entry_obj.entity_id == desired_entity_id:
        return

    if desired_entity_id in registry.entities:
        return

    registry.async_update_entity(
        entry_obj.entity_id,
        new_entity_id=desired_entity_id,
    )


def _remove_legacy_debug_switch(hass: HomeAssistant, entry: ConfigEntry) -> None:
    """Remove old debug switch if it exists."""
    registry = er.async_get(hass)

    legacy_debug = next(
        (
            entity
            for entity in registry.entities.values()
            if entity.platform == DOMAIN
            and entity.config_entry_id == entry.entry_id
            and entity.unique_id in {"macs_debug", f"{entry.entry_id}_debug"}
            and entity.domain == "switch"
        ),
        None,
    )

    if legacy_debug:
        registry.async_remove(legacy_debug.entity_id)


def _hide_entities_from_assist(hass: HomeAssistant, entry: ConfigEntry) -> None:
    """Hide MACS entities from Assist exposure by default."""
    if entry.options.get("assist_exposure_initialized"):
        return

    registry = er.async_get(hass)

    for entity in list(registry.entities.values()):
        if entity.platform != DOMAIN or entity.config_entry_id != entry.entry_id:
            continue

        options = dict(entity.options)
        conversation = dict(options.get("conversation", {}))

        if conversation.get("should_expose") is False:
            continue

        conversation["should_expose"] = False
        options["conversation"] = conversation

        try:
            registry.async_update_entity_options(entity.entity_id, DOMAIN, options)
        except AttributeError:
            try:
                registry.async_update_entity(entity.entity_id, options=options)
            except TypeError:
                pass

    hass.config_entries.async_update_entry(
        entry,
        options={**entry.options, "assist_exposure_initialized": True},
    )


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up MACS from a config entry."""
    hass.data.setdefault(DOMAIN, {})

    _ensure_entry_state(hass, entry)

    # Removed legacy static path registration for /macs
    # HACS now handles the frontend files via /hacsfiles/macs-xav/
    # No need to register static paths anymore for the card

    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)

    for unique_id, desired_entity_id in ENTITY_TARGETS.items():
        _migrate_entity_id(hass, entry, unique_id, desired_entity_id)

    _remove_legacy_debug_switch(hass, entry)
    _hide_entities_from_assist(hass, entry)

    async def handle_set_mood(call: ServiceCall) -> None:
        mood = str(call.data.get(ATTR_MOOD, "")).strip().lower()

        if mood not in MOODS:
            raise vol.Invalid(f"Invalid mood '{mood}'. Must be one of: {', '.join(MOODS)}")

        entity_id = _find_entity_id_by_unique_id(hass, "macs_mood", entry)

        if not entity_id:
            raise vol.Invalid("MACS mood entity not found. Entity select.macs_mood is missing.")

        await hass.services.async_call(
            "select",
            "select_option",
            {
                "entity_id": entity_id,
                "option": mood,
            },
            blocking=True,
        )

        hass.data[DOMAIN][entry.entry_id][ATTR_MOOD] = mood
        hass.bus.async_fire(f"{DOMAIN}_state_updated", {"entry_id": entry.entry_id, "key": ATTR_MOOD})

    async def _set_number_entity(
        call: ServiceCall,
        attr_name: str,
        unique_id: str,
        label: str,
        min_value: float,
        max_value: float,
    ) -> None:
        raw = call.data.get(attr_name, None)

        try:
            value = float(raw)
        except (TypeError, ValueError):
            raise vol.Invalid(f"Invalid {label} '{raw}'. Must be a number.")

        if value < min_value or value > max_value:
            raise vol.Invalid(f"Invalid {label} '{value}'. Must be between {min_value} and {max_value}.")

        entity_id = _find_entity_id_by_unique_id(hass, unique_id, entry)

        if not entity_id:
            raise vol.Invalid(f"MACS {label} entity not found. unique_id={unique_id} is missing.")

        await hass.services.async_call(
            "number",
            "set_value",
            {
                "entity_id": entity_id,
                "value": value,
            },
            blocking=True,
        )

        hass.data[DOMAIN][entry.entry_id][attr_name] = value
        hass.bus.async_fire(f"{DOMAIN}_state_updated", {"entry_id": entry.entry_id, "key": attr_name})

    async def handle_set_brightness(call: ServiceCall) -> None:
        await _set_number_entity(call, ATTR_BRIGHTNESS, "macs_brightness", "brightness", 0, 100)

    async def handle_set_temperature(call: ServiceCall) -> None:
        await _set_number_entity(call, ATTR_TEMPERATURE, "macs_temperature", "temperature", -30, 50)

    async def handle_set_windspeed(call: ServiceCall) -> None:
        await _set_number_entity(call, ATTR_WINDSPEED, "macs_windspeed", "windspeed", 0, 200)

    async def handle_set_precipitation(call: ServiceCall) -> None:
        await _set_number_entity(call, ATTR_PRECIPITATION, "macs_precipitation", "precipitation", 0, 200)

    async def handle_set_battery_charge(call: ServiceCall) -> None:
        await _set_number_entity(call, ATTR_BATTERY_CHARGE, "macs_battery_charge", "battery charge", 0, 100)

    async def _set_switch_entity(
        call: ServiceCall,
        attr_name: str,
        unique_id: str,
        label: str,
    ) -> None:
        raw = call.data.get(attr_name, None)

        if isinstance(raw, bool):
            is_on = raw
        elif isinstance(raw, (int, float)):
            is_on = bool(raw)
        elif isinstance(raw, str):
            value = raw.strip().lower()
            if value in ("1", "true", "on", "yes", "y"):
                is_on = True
            elif value in ("0", "false", "off", "no", "n"):
                is_on = False
            else:
                raise vol.Invalid(f"Invalid {label} '{raw}'. Must be true or false.")
        else:
            raise vol.Invalid(f"Invalid {label} '{raw}'. Must be true or false.")

        entity_id = _find_entity_id_by_unique_id(hass, unique_id, entry)

        if not entity_id:
            raise vol.Invalid(f"MACS {label} entity not found. unique_id={unique_id} is missing.")

        await hass.services.async_call(
            "switch",
            "turn_on" if is_on else "turn_off",
            {
                "entity_id": entity_id,
            },
            blocking=True,
        )

        hass.data[DOMAIN][entry.entry_id][attr_name] = is_on
        hass.bus.async_fire(f"{DOMAIN}_state_updated", {"entry_id": entry.entry_id, "key": attr_name})

    async def handle_set_animations_enabled(call: ServiceCall) -> None:
        await _set_switch_entity(
            call,
            ATTR_ANIMATIONS_ENABLED,
            "macs_animations_enabled",
            "animations enabled",
        )

    async def handle_set_charging(call: ServiceCall) -> None:
        await _set_switch_entity(
            call,
            ATTR_CHARGING,
            "macs_charging",
            "charging",
        )

    async def handle_set_weather_conditions_snowy(call: ServiceCall) -> None:
        await _set_switch_entity(call, ATTR_WEATHER_CONDITIONS_SNOWY, "macs_weather_conditions_snowy", "weather conditions snowy")

    async def handle_set_weather_conditions_cloudy(call: ServiceCall) -> None:
        await _set_switch_entity(call, ATTR_WEATHER_CONDITIONS_CLOUDY, "macs_weather_conditions_cloudy", "weather conditions cloudy")

    async def handle_set_weather_conditions_rainy(call: ServiceCall) -> None:
        await _set_switch_entity(call, ATTR_WEATHER_CONDITIONS_RAINY, "macs_weather_conditions_rainy", "weather conditions rainy")

    async def handle_set_weather_conditions_windy(call: ServiceCall) -> None:
        await _set_switch_entity(call, ATTR_WEATHER_CONDITIONS_WINDY, "macs_weather_conditions_windy", "weather conditions windy")

    async def handle_set_weather_conditions_sunny(call: ServiceCall) -> None:
        await _set_switch_entity(call, ATTR_WEATHER_CONDITIONS_SUNNY, "macs_weather_conditions_sunny", "weather conditions sunny")

    async def handle_set_weather_conditions_stormy(call: ServiceCall) -> None:
        await _set_switch_entity(call, ATTR_WEATHER_CONDITIONS_STORMY, "macs_weather_conditions_stormy", "weather conditions stormy")

    async def handle_set_weather_conditions_foggy(call: ServiceCall) -> None:
        await _set_switch_entity(call, ATTR_WEATHER_CONDITIONS_FOGGY, "macs_weather_conditions_foggy", "weather conditions foggy")

    async def handle_set_weather_conditions_hail(call: ServiceCall) -> None:
        await _set_switch_entity(call, ATTR_WEATHER_CONDITIONS_HAIL, "macs_weather_conditions_hail", "weather conditions hail")

    async def handle_set_weather_conditions_lightning(call: ServiceCall) -> None:
        await _set_switch_entity(call, ATTR_WEATHER_CONDITIONS_LIGHTNING, "macs_weather_conditions_lightning", "weather conditions lightning")

    async def handle_set_weather_conditions_partlycloudy(call: ServiceCall) -> None:
        await _set_switch_entity(call, ATTR_WEATHER_CONDITIONS_PARTLYCLOUDY, "macs_weather_conditions_partlycloudy", "weather conditions partly cloudy")

    async def handle_set_weather_conditions_pouring(call: ServiceCall) -> None:
        await _set_switch_entity(call, ATTR_WEATHER_CONDITIONS_POURING, "macs_weather_conditions_pouring", "weather conditions pouring")

    async def handle_set_weather_conditions_clear_night(call: ServiceCall) -> None:
        await _set_switch_entity(call, ATTR_WEATHER_CONDITIONS_CLEAR_NIGHT, "macs_weather_conditions_clear_night", "weather conditions clear night")

    async def handle_set_weather_conditions_exceptional(call: ServiceCall) -> None:
        await _set_switch_entity(call, ATTR_WEATHER_CONDITIONS_EXCEPTIONAL, "macs_weather_conditions_exceptional", "weather conditions exceptional")

    async def _handle_send_message(call: ServiceCall, role: str) -> None:
        raw = call.data.get(ATTR_MESSAGE, None)
        text = str(raw or "").strip()

        if not text:
            raise vol.Invalid("Message cannot be empty.")

        payload = {
            "id": uuid4().hex,
            "role": role,
            "text": text,
            "ts": dt_util.utcnow().isoformat(),
        }

        hass.bus.async_fire(EVENT_MESSAGE, payload)

    async def handle_send_user_message(call: ServiceCall) -> None:
        await _handle_send_message(call, "user")

    async def handle_send_assistant_message(call: ServiceCall) -> None:
        await _handle_send_message(call, "assistant")

    service_definitions = [
        (SERVICE_SET_MOOD, handle_set_mood, vol.Schema({vol.Required(ATTR_MOOD): vol.In(MOODS)})),
        (SERVICE_SET_BRIGHTNESS, handle_set_brightness, vol.Schema({vol.Required(ATTR_BRIGHTNESS): vol.Coerce(float)})),
        (SERVICE_SET_TEMPERATURE, handle_set_temperature, vol.Schema({vol.Required(ATTR_TEMPERATURE): vol.Coerce(float)})),
        (SERVICE_SET_WINDSPEED, handle_set_windspeed, vol.Schema({vol.Required(ATTR_WINDSPEED): vol.Coerce(float)})),
        (SERVICE_SET_PRECIPITATION, handle_set_precipitation, vol.Schema({vol.Required(ATTR_PRECIPITATION): vol.Coerce(float)})),
        (SERVICE_SET_BATTERY_CHARGE, handle_set_battery_charge, vol.Schema({vol.Required(ATTR_BATTERY_CHARGE): vol.Coerce(float)})),
        (SERVICE_SET_ANIMATIONS_ENABLED, handle_set_animations_enabled, vol.Schema({vol.Required(ATTR_ANIMATIONS_ENABLED): cv.boolean})),
        (SERVICE_SET_CHARGING, handle_set_charging, vol.Schema({vol.Required(ATTR_CHARGING): cv.boolean})),
        (SERVICE_SET_WEATHER_CONDITIONS_SNOWY, handle_set_weather_conditions_snowy, vol.Schema({vol.Required(ATTR_WEATHER_CONDITIONS_SNOWY): cv.boolean})),
        (SERVICE_SET_WEATHER_CONDITIONS_CLOUDY, handle_set_weather_conditions_cloudy, vol.Schema({vol.Required(ATTR_WEATHER_CONDITIONS_CLOUDY): cv.boolean})),
        (SERVICE_SET_WEATHER_CONDITIONS_RAINY, handle_set_weather_conditions_rainy, vol.Schema({vol.Required(ATTR_WEATHER_CONDITIONS_RAINY): cv.boolean})),
        (SERVICE_SET_WEATHER_CONDITIONS_WINDY, handle_set_weather_conditions_windy, vol.Schema({vol.Required(ATTR_WEATHER_CONDITIONS_WINDY): cv.boolean})),
        (SERVICE_SET_WEATHER_CONDITIONS_SUNNY, handle_set_weather_conditions_sunny, vol.Schema({vol.Required(ATTR_WEATHER_CONDITIONS_SUNNY): cv.boolean})),
        (SERVICE_SET_WEATHER_CONDITIONS_STORMY, handle_set_weather_conditions_stormy, vol.Schema({vol.Required(ATTR_WEATHER_CONDITIONS_STORMY): cv.boolean})),
        (SERVICE_SET_WEATHER_CONDITIONS_FOGGY, handle_set_weather_conditions_foggy, vol.Schema({vol.Required(ATTR_WEATHER_CONDITIONS_FOGGY): cv.boolean})),
        (SERVICE_SET_WEATHER_CONDITIONS_HAIL, handle_set_weather_conditions_hail, vol.Schema({vol.Required(ATTR_WEATHER_CONDITIONS_HAIL): cv.boolean})),
        (SERVICE_SET_WEATHER_CONDITIONS_LIGHTNING, handle_set_weather_conditions_lightning, vol.Schema({vol.Required(ATTR_WEATHER_CONDITIONS_LIGHTNING): cv.boolean})),
        (SERVICE_SET_WEATHER_CONDITIONS_PARTLYCLOUDY, handle_set_weather_conditions_partlycloudy, vol.Schema({vol.Required(ATTR_WEATHER_CONDITIONS_PARTLYCLOUDY): cv.boolean})),
        (SERVICE_SET_WEATHER_CONDITIONS_POURING, handle_set_weather_conditions_pouring, vol.Schema({vol.Required(ATTR_WEATHER_CONDITIONS_POURING): cv.boolean})),
        (SERVICE_SET_WEATHER_CONDITIONS_CLEAR_NIGHT, handle_set_weather_conditions_clear_night, vol.Schema({vol.Required(ATTR_WEATHER_CONDITIONS_CLEAR_NIGHT): cv.boolean})),
        (SERVICE_SET_WEATHER_CONDITIONS_EXCEPTIONAL, handle_set_weather_conditions_exceptional, vol.Schema({vol.Required(ATTR_WEATHER_CONDITIONS_EXCEPTIONAL): cv.boolean})),
        (SERVICE_SEND_USER_MESSAGE, handle_send_user_message, vol.Schema({vol.Required(ATTR_MESSAGE): cv.string})),
        (SERVICE_SEND_ASSISTANT_MESSAGE, handle_send_assistant_message, vol.Schema({vol.Required(ATTR_MESSAGE): cv.string})),
    ]

    for service_name, handler, schema in service_definitions:
        if not hass.services.has_service(DOMAIN, service_name):
            hass.services.async_register(
                DOMAIN,
                service_name,
                handler,
                schema=schema,
            )

    await _ensure_lovelace_resource(hass)

    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload MACS."""
    unload_ok = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)

    if unload_ok and not hass.config_entries.async_entries(DOMAIN):
        services = [
            SERVICE_SET_MOOD,
            SERVICE_SET_BRIGHTNESS,
            SERVICE_SET_TEMPERATURE,
            SERVICE_SET_WINDSPEED,
            SERVICE_SET_PRECIPITATION,
            SERVICE_SET_BATTERY_CHARGE,
            SERVICE_SET_ANIMATIONS_ENABLED,
            SERVICE_SET_CHARGING,
            SERVICE_SET_WEATHER_CONDITIONS_SNOWY,
            SERVICE_SET_WEATHER_CONDITIONS_CLOUDY,
            SERVICE_SET_WEATHER_CONDITIONS_RAINY,
            SERVICE_SET_WEATHER_CONDITIONS_WINDY,
            SERVICE_SET_WEATHER_CONDITIONS_SUNNY,
            SERVICE_SET_WEATHER_CONDITIONS_STORMY,
            SERVICE_SET_WEATHER_CONDITIONS_FOGGY,
            SERVICE_SET_WEATHER_CONDITIONS_HAIL,
            SERVICE_SET_WEATHER_CONDITIONS_LIGHTNING,
            SERVICE_SET_WEATHER_CONDITIONS_PARTLYCLOUDY,
            SERVICE_SET_WEATHER_CONDITIONS_POURING,
            SERVICE_SET_WEATHER_CONDITIONS_CLEAR_NIGHT,
            SERVICE_SET_WEATHER_CONDITIONS_EXCEPTIONAL,
            SERVICE_SEND_USER_MESSAGE,
            SERVICE_SEND_ASSISTANT_MESSAGE,
        ]

        for service in services:
            if hass.services.has_service(DOMAIN, service):
                hass.services.async_remove(DOMAIN, service)

        hass.data.get(DOMAIN, {}).pop("static_path_registered", None)

    if unload_ok:
        hass.data.get(DOMAIN, {}).pop(entry.entry_id, None)

    return unload_ok

"""M.A.C.S. integration for Home Assistant."""

from __future__ import annotations

import logging
from pathlib import Path
from typing import Any

from homeassistant.components import frontend
from homeassistant.components.http import StaticPathConfig
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import Platform
from homeassistant.core import HomeAssistant, ServiceCall
from homeassistant.helpers.typing import ConfigType

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

_LOGGER = logging.getLogger(__name__)

PLATFORMS: list[Platform] = [
    Platform.SELECT,
    Platform.NUMBER,
    Platform.SWITCH,
]

WWW_DIR = Path(__file__).parent / "www"
CARD_DIR_URL = "/macs"
CARD_URL = "/macs/macs.js"


async def async_setup(hass: HomeAssistant, config: ConfigType) -> bool:
    """Set up M.A.C.S. from YAML."""
    return True


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up M.A.C.S. from a config entry."""
    hass.data.setdefault(DOMAIN, {})
    hass.data[DOMAIN][entry.entry_id] = _default_state()

    await _register_frontend(hass)
    await _register_services(hass)
    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)

    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload M.A.C.S."""
    unload_ok = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)

    if unload_ok:
        hass.data.get(DOMAIN, {}).pop(entry.entry_id, None)

    return unload_ok


def _default_state() -> dict[str, Any]:
    """Return default runtime state for M.A.C.S."""
    return {
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


async def _register_frontend(hass: HomeAssistant) -> None:
    """Register the frontend JavaScript module directory."""
    if not WWW_DIR.exists():
        _LOGGER.warning("M.A.C.S. www directory not found: %s", WWW_DIR)
        return

    try:
        await hass.http.async_register_static_paths(
            [
                StaticPathConfig(
                    url_path=CARD_DIR_URL,
                    path=str(WWW_DIR),
                    cache_headers=False,
                )
            ]
        )
        _LOGGER.debug("Registered M.A.C.S. frontend directory at %s", CARD_DIR_URL)
    except RuntimeError:
        _LOGGER.debug("M.A.C.S. frontend already registered at %s", CARD_DIR_URL)
    except Exception as err:
        _LOGGER.warning("Unable to register M.A.C.S. frontend: %s", err)

    try:
        frontend.async_register_extra_js_url(hass, CARD_URL)
    except Exception as err:
        _LOGGER.debug("Unable to register extra JS URL for M.A.C.S.: %s", err)


async def _register_services(hass: HomeAssistant) -> None:
    """Register M.A.C.S. services once."""
    if hass.services.has_service(DOMAIN, SERVICE_SET_MOOD):
        return

    async def update_value(attr: str, value: Any) -> None:
        for entry_id in hass.data.get(DOMAIN, {}):
            hass.data[DOMAIN][entry_id][attr] = value
        _schedule_updates(hass)

    async def set_mood(call: ServiceCall) -> None:
        mood = str(call.data.get(ATTR_MOOD, DEFAULT_MOOD)).strip()
        if mood not in MOODS:
            mood = DEFAULT_MOOD
        await update_value(ATTR_MOOD, mood)

    async def set_brightness(call: ServiceCall) -> None:
        await update_value(
            ATTR_BRIGHTNESS,
            _clamp_number(call.data.get(ATTR_BRIGHTNESS), 0, 100, DEFAULT_BRIGHTNESS),
        )

    async def set_temperature(call: ServiceCall) -> None:
        await update_value(
            ATTR_TEMPERATURE,
            _safe_number(call.data.get(ATTR_TEMPERATURE), DEFAULT_TEMPERATURE),
        )

    async def set_windspeed(call: ServiceCall) -> None:
        await update_value(
            ATTR_WINDSPEED,
            _safe_number(call.data.get(ATTR_WINDSPEED), DEFAULT_WINDSPEED),
        )

    async def set_precipitation(call: ServiceCall) -> None:
        await update_value(
            ATTR_PRECIPITATION,
            _safe_number(call.data.get(ATTR_PRECIPITATION), DEFAULT_PRECIPITATION),
        )

    async def set_battery_charge(call: ServiceCall) -> None:
        await update_value(
            ATTR_BATTERY_CHARGE,
            _clamp_number(
                call.data.get(ATTR_BATTERY_CHARGE),
                0,
                100,
                DEFAULT_BATTERY_CHARGE,
            ),
        )

    async def set_animations_enabled(call: ServiceCall) -> None:
        await update_value(
            ATTR_ANIMATIONS_ENABLED,
            _safe_bool(
                call.data.get(ATTR_ANIMATIONS_ENABLED),
                DEFAULT_ANIMATIONS_ENABLED,
            ),
        )

    async def set_charging(call: ServiceCall) -> None:
        await update_value(
            ATTR_CHARGING,
            _safe_bool(call.data.get(ATTR_CHARGING), DEFAULT_CHARGING),
        )

    async def send_user_message(call: ServiceCall) -> None:
        _fire_message(hass, "user", call.data.get(ATTR_MESSAGE, ""))

    async def send_assistant_message(call: ServiceCall) -> None:
        _fire_message(hass, "assistant", call.data.get(ATTR_MESSAGE, ""))

    hass.services.async_register(DOMAIN, SERVICE_SET_MOOD, set_mood)
    hass.services.async_register(DOMAIN, SERVICE_SET_BRIGHTNESS, set_brightness)
    hass.services.async_register(DOMAIN, SERVICE_SET_TEMPERATURE, set_temperature)
    hass.services.async_register(DOMAIN, SERVICE_SET_WINDSPEED, set_windspeed)
    hass.services.async_register(DOMAIN, SERVICE_SET_PRECIPITATION, set_precipitation)
    hass.services.async_register(DOMAIN, SERVICE_SET_BATTERY_CHARGE, set_battery_charge)
    hass.services.async_register(DOMAIN, SERVICE_SET_ANIMATIONS_ENABLED, set_animations_enabled)
    hass.services.async_register(DOMAIN, SERVICE_SET_CHARGING, set_charging)
    hass.services.async_register(DOMAIN, SERVICE_SEND_USER_MESSAGE, send_user_message)
    hass.services.async_register(DOMAIN, SERVICE_SEND_ASSISTANT_MESSAGE, send_assistant_message)

    weather_services = {
        SERVICE_SET_WEATHER_CONDITIONS_SNOWY: ATTR_WEATHER_CONDITIONS_SNOWY,
        SERVICE_SET_WEATHER_CONDITIONS_CLOUDY: ATTR_WEATHER_CONDITIONS_CLOUDY,
        SERVICE_SET_WEATHER_CONDITIONS_RAINY: ATTR_WEATHER_CONDITIONS_RAINY,
        SERVICE_SET_WEATHER_CONDITIONS_WINDY: ATTR_WEATHER_CONDITIONS_WINDY,
        SERVICE_SET_WEATHER_CONDITIONS_SUNNY: ATTR_WEATHER_CONDITIONS_SUNNY,
        SERVICE_SET_WEATHER_CONDITIONS_STORMY: ATTR_WEATHER_CONDITIONS_STORMY,
        SERVICE_SET_WEATHER_CONDITIONS_FOGGY: ATTR_WEATHER_CONDITIONS_FOGGY,
        SERVICE_SET_WEATHER_CONDITIONS_HAIL: ATTR_WEATHER_CONDITIONS_HAIL,
        SERVICE_SET_WEATHER_CONDITIONS_LIGHTNING: ATTR_WEATHER_CONDITIONS_LIGHTNING,
        SERVICE_SET_WEATHER_CONDITIONS_PARTLYCLOUDY: ATTR_WEATHER_CONDITIONS_PARTLYCLOUDY,
        SERVICE_SET_WEATHER_CONDITIONS_POURING: ATTR_WEATHER_CONDITIONS_POURING,
        SERVICE_SET_WEATHER_CONDITIONS_CLEAR_NIGHT: ATTR_WEATHER_CONDITIONS_CLEAR_NIGHT,
        SERVICE_SET_WEATHER_CONDITIONS_EXCEPTIONAL: ATTR_WEATHER_CONDITIONS_EXCEPTIONAL,
    }

    for service_name, attr_name in weather_services.items():

        async def set_weather_condition(
            call: ServiceCall,
            attr: str = attr_name,
        ) -> None:
            await update_value(attr, _safe_bool(call.data.get(attr), False))

        hass.services.async_register(DOMAIN, service_name, set_weather_condition)


def _schedule_updates(hass: HomeAssistant) -> None:
    """Ask entities to refresh."""
    hass.bus.async_fire(f"{DOMAIN}_state_updated")


def _fire_message(hass: HomeAssistant, role: str, message: Any) -> None:
    """Fire a normalized M.A.C.S. message event."""
    text = _normalize_message(message)

    if not text:
        return

    hass.bus.async_fire(
        EVENT_MESSAGE,
        {
            "role": role,
            "text": text,
        },
    )


def _normalize_message(message: Any) -> str:
    """Normalize a message payload."""
    if message is None:
        return ""

    if isinstance(message, dict):
        speech = message.get("speech") or {}
        response = message.get("response") or {}
        response_speech = response.get("speech") if isinstance(response, dict) else {}

        value = (
            message.get("text")
            or message.get("message")
            or message.get("content")
            or speech.get("plain", {}).get("speech")
            or response_speech.get("plain", {}).get("speech")
            or ""
        )
        return str(value).strip()

    return str(message).strip()


def _safe_number(value: Any, fallback: float) -> float:
    """Return a safe numeric value."""
    try:
        if value in (None, "", "unknown", "unavailable"):
            return fallback
        return float(str(value).replace(",", "."))
    except (TypeError, ValueError):
        return fallback


def _clamp_number(value: Any, minimum: float, maximum: float, fallback: float) -> float:
    """Return a safe clamped numeric value."""
    number = _safe_number(value, fallback)
    return max(minimum, min(maximum, number))


def _safe_bool(value: Any, fallback: bool) -> bool:
    """Return a safe boolean value."""
    if isinstance(value, bool):
        return value

    if value is None:
        return fallback

    text = str(value).strip().lower()

    if text in {"true", "on", "yes", "1"}:
        return True

    if text in {"false", "off", "no", "0"}:
        return False

    return fallback

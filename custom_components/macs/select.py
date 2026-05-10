"""Select entities for the M.A.C.S. integration."""

from __future__ import annotations

import json
from pathlib import Path

from homeassistant.components.select import SelectEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import Event, HomeAssistant, callback
from homeassistant.helpers.entity import EntityCategory
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.restore_state import RestoreEntity

from .const import (
    ATTR_MOOD,
    DEFAULT_MOOD,
    DOMAIN,
    MACS_DEVICE,
    MOODS,
)

ATTR_DEBUG = "debug"
DEFAULT_DEBUG = "None"


def _load_debug_options() -> list[str]:
    """Load frontend debug targets from constants.json if available."""
    options: list[str] = ["None", "All"]

    path = Path(__file__).parent / "www" / "shared" / "constants.json"

    try:
        raw = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return options

    if not isinstance(raw, dict):
        return options

    debug_targets = raw.get("debugTargets", [])

    if not isinstance(debug_targets, list):
        return options

    for entry in debug_targets:
        label = ""

        if isinstance(entry, dict):
            label = str(entry.get("label", "")).strip()
        elif isinstance(entry, str):
            label = entry.strip()

        if label and label not in options:
            options.append(label)

    return options


DEBUG_OPTIONS = _load_debug_options()

if DEFAULT_DEBUG not in DEBUG_OPTIONS:
    DEBUG_OPTIONS.insert(0, DEFAULT_DEBUG)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up M.A.C.S. select entities."""
    hass.data.setdefault(DOMAIN, {})
    hass.data[DOMAIN].setdefault(entry.entry_id, {})
    hass.data[DOMAIN][entry.entry_id].setdefault(ATTR_MOOD, DEFAULT_MOOD)
    hass.data[DOMAIN][entry.entry_id].setdefault(ATTR_DEBUG, DEFAULT_DEBUG)

    async_add_entities(
        [
            MacsMoodSelect(hass, entry),
            MacsDebugSelect(hass, entry),
        ]
    )


class MacsMoodSelect(SelectEntity, RestoreEntity):
    """M.A.C.S. mood selector."""

    _attr_has_entity_name = True
    _attr_translation_key = "mood"
    _attr_icon = "mdi:emoticon-outline"

    def __init__(self, hass: HomeAssistant, entry: ConfigEntry) -> None:
        """Initialize the mood selector."""
        self.hass = hass
        self.entry = entry

        self._attr_unique_id = "macs_mood"
        self._attr_suggested_object_id = "macs_mood"

        self._attr_device_info = MACS_DEVICE
        self._attr_options = list(MOODS)
        self._attr_current_option = DEFAULT_MOOD

    @property
    def current_option(self) -> str:
        """Return the current selected mood."""
        return self._get_state_value()

    async def async_select_option(self, option: str) -> None:
        """Change the selected mood."""
        value = str(option or "").strip().lower()

        if value not in MOODS:
            value = DEFAULT_MOOD

        self.hass.data.setdefault(DOMAIN, {})
        self.hass.data[DOMAIN].setdefault(self.entry.entry_id, {})
        self.hass.data[DOMAIN][self.entry.entry_id][ATTR_MOOD] = value

        self._attr_current_option = value
        self.async_write_ha_state()

        self.hass.bus.async_fire(
            f"{DOMAIN}_state_updated",
            {
                "entry_id": self.entry.entry_id,
                "key": ATTR_MOOD,
                "value": value,
            },
        )

    async def async_added_to_hass(self) -> None:
        """Restore state and register update listener."""
        await super().async_added_to_hass()

        self.hass.data.setdefault(DOMAIN, {})
        self.hass.data[DOMAIN].setdefault(self.entry.entry_id, {})

        last_state = await self.async_get_last_state()

        if last_state is not None and last_state.state in MOODS:
            self.hass.data[DOMAIN][self.entry.entry_id][ATTR_MOOD] = last_state.state
            self._attr_current_option = last_state.state
        else:
            self.hass.data[DOMAIN][self.entry.entry_id].setdefault(
                ATTR_MOOD,
                DEFAULT_MOOD,
            )
            self._attr_current_option = self._get_state_value()

        @callback
        def _handle_update(event: Event) -> None:
            data = event.data or {}

            if data.get("entry_id") not in (None, self.entry.entry_id):
                return

            if data.get("key") not in (None, ATTR_MOOD):
                return

            self._attr_current_option = self._get_state_value()
            self.async_write_ha_state()

        self.async_on_remove(
            self.hass.bus.async_listen(
                f"{DOMAIN}_state_updated",
                _handle_update,
            )
        )

    def _get_state_value(self) -> str:
        """Get the current mood from hass data."""
        value = (
            self.hass.data
            .get(DOMAIN, {})
            .get(self.entry.entry_id, {})
            .get(ATTR_MOOD, DEFAULT_MOOD)
        )

        value = str(value or "").strip().lower()

        if value not in MOODS:
            return DEFAULT_MOOD

        return value


class MacsDebugSelect(SelectEntity, RestoreEntity):
    """M.A.C.S. debug selector."""

    _attr_has_entity_name = True
    _attr_translation_key = "debug"
    _attr_icon = "mdi:bug-outline"
    _attr_entity_category = EntityCategory.CONFIG

    def __init__(self, hass: HomeAssistant, entry: ConfigEntry) -> None:
        """Initialize the debug selector."""
        self.hass = hass
        self.entry = entry

        self._attr_unique_id = "macs_debug"
        self._attr_suggested_object_id = "macs_debug"

        self._attr_device_info = MACS_DEVICE
        self._attr_options = DEBUG_OPTIONS
        self._attr_current_option = DEFAULT_DEBUG

    @property
    def current_option(self) -> str:
        """Return the current selected debug option."""
        return self._get_state_value()

    async def async_select_option(self, option: str) -> None:
        """Change the selected debug option."""
        value = str(option or "").strip()

        if value not in DEBUG_OPTIONS:
            value = DEFAULT_DEBUG

        self.hass.data.setdefault(DOMAIN, {})
        self.hass.data[DOMAIN].setdefault(self.entry.entry_id, {})
        self.hass.data[DOMAIN][self.entry.entry_id][ATTR_DEBUG] = value

        self._attr_current_option = value
        self.async_write_ha_state()

        self.hass.bus.async_fire(
            f"{DOMAIN}_state_updated",
            {
                "entry_id": self.entry.entry_id,
                "key": ATTR_DEBUG,
                "value": value,
            },
        )

    async def async_added_to_hass(self) -> None:
        """Restore state and register update listener."""
        await super().async_added_to_hass()

        self.hass.data.setdefault(DOMAIN, {})
        self.hass.data[DOMAIN].setdefault(self.entry.entry_id, {})

        last_state = await self.async_get_last_state()

        if last_state is not None and last_state.state in DEBUG_OPTIONS:
            self.hass.data[DOMAIN][self.entry.entry_id][ATTR_DEBUG] = last_state.state
            self._attr_current_option = last_state.state
        else:
            self.hass.data[DOMAIN][self.entry.entry_id].setdefault(
                ATTR_DEBUG,
                DEFAULT_DEBUG,
            )
            self._attr_current_option = self._get_state_value()

        @callback
        def _handle_update(event: Event) -> None:
            data = event.data or {}

            if data.get("entry_id") not in (None, self.entry.entry_id):
                return

            if data.get("key") not in (None, ATTR_DEBUG):
                return

            self._attr_current_option = self._get_state_value()
            self.async_write_ha_state()

        self.async_on_remove(
            self.hass.bus.async_listen(
                f"{DOMAIN}_state_updated",
                _handle_update,
            )
        )

    def _get_state_value(self) -> str:
        """Get the current debug mode from hass data."""
        value = (
            self.hass.data
            .get(DOMAIN, {})
            .get(self.entry.entry_id, {})
            .get(ATTR_DEBUG, DEFAULT_DEBUG)
        )

        value = str(value or "").strip()

        if value not in DEBUG_OPTIONS:
            return DEFAULT_DEBUG

        return value

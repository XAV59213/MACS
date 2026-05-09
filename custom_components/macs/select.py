"""Select entities for the M.A.C.S. integration."""

from __future__ import annotations

from homeassistant.components.select import SelectEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import Event, HomeAssistant, callback
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import (
    ATTR_MOOD,
    DEFAULT_MOOD,
    DOMAIN,
    MACS_DEVICE,
    MOODS,
)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up M.A.C.S. select entities."""
    async_add_entities([MacsMoodSelect(hass, entry)])


class MacsMoodSelect(SelectEntity):
    """M.A.C.S. mood selector."""

    _attr_has_entity_name = True
    _attr_translation_key = "mood"
    _attr_icon = "mdi:emoticon-outline"

    def __init__(self, hass: HomeAssistant, entry: ConfigEntry) -> None:
        """Initialize the mood selector."""
        self.hass = hass
        self.entry = entry

        self._attr_unique_id = f"{entry.entry_id}_mood"
        self._attr_device_info = MACS_DEVICE
        self._attr_options = list(MOODS)
        self._attr_current_option = self._get_state_value()

    @property
    def current_option(self) -> str:
        """Return the current selected mood."""
        return self._get_state_value()

    async def async_select_option(self, option: str) -> None:
        """Change the selected mood."""
        if option not in MOODS:
            option = DEFAULT_MOOD

        self.hass.data[DOMAIN][self.entry.entry_id][ATTR_MOOD] = option
        self._attr_current_option = option
        self.async_write_ha_state()

    async def async_added_to_hass(self) -> None:
        """Register update listener."""

        @callback
        def _handle_update(event: Event) -> None:
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

        if value not in MOODS:
            return DEFAULT_MOOD

        return value

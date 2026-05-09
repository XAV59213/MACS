"""Number entities for the M.A.C.S. integration."""

from __future__ import annotations

from homeassistant.components.number import NumberEntity, NumberEntityDescription
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import PERCENTAGE, UnitOfSpeed, UnitOfTemperature
from homeassistant.core import Event, HomeAssistant, callback
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import (
    ATTR_BATTERY_CHARGE,
    ATTR_BRIGHTNESS,
    ATTR_PRECIPITATION,
    ATTR_TEMPERATURE,
    ATTR_WINDSPEED,
    DEFAULT_BATTERY_CHARGE,
    DEFAULT_BRIGHTNESS,
    DEFAULT_PRECIPITATION,
    DEFAULT_TEMPERATURE,
    DEFAULT_WINDSPEED,
    DOMAIN,
    MACS_DEVICE,
)


NUMBER_DESCRIPTIONS: tuple[NumberEntityDescription, ...] = (
    NumberEntityDescription(
        key=ATTR_BRIGHTNESS,
        translation_key="brightness",
        icon="mdi:brightness-6",
        native_min_value=0,
        native_max_value=100,
        native_step=1,
        native_unit_of_measurement=PERCENTAGE,
    ),
    NumberEntityDescription(
        key=ATTR_TEMPERATURE,
        translation_key="temperature",
        icon="mdi:thermometer",
        native_min_value=-30,
        native_max_value=50,
        native_step=0.1,
        native_unit_of_measurement=UnitOfTemperature.CELSIUS,
    ),
    NumberEntityDescription(
        key=ATTR_WINDSPEED,
        translation_key="windspeed",
        icon="mdi:weather-windy",
        native_min_value=0,
        native_max_value=200,
        native_step=0.1,
        native_unit_of_measurement=UnitOfSpeed.KILOMETERS_PER_HOUR,
    ),
    NumberEntityDescription(
        key=ATTR_PRECIPITATION,
        translation_key="precipitation",
        icon="mdi:weather-pouring",
        native_min_value=0,
        native_max_value=200,
        native_step=0.1,
        native_unit_of_measurement="mm",
    ),
    NumberEntityDescription(
        key=ATTR_BATTERY_CHARGE,
        translation_key="battery_charge",
        icon="mdi:battery",
        native_min_value=0,
        native_max_value=100,
        native_step=1,
        native_unit_of_measurement=PERCENTAGE,
    ),
)


DEFAULT_VALUES = {
    ATTR_BRIGHTNESS: DEFAULT_BRIGHTNESS,
    ATTR_TEMPERATURE: DEFAULT_TEMPERATURE,
    ATTR_WINDSPEED: DEFAULT_WINDSPEED,
    ATTR_PRECIPITATION: DEFAULT_PRECIPITATION,
    ATTR_BATTERY_CHARGE: DEFAULT_BATTERY_CHARGE,
}


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up M.A.C.S. number entities."""
    async_add_entities(
        [MacsNumber(hass, entry, description) for description in NUMBER_DESCRIPTIONS]
    )


class MacsNumber(NumberEntity):
    """M.A.C.S. number entity."""

    _attr_has_entity_name = True

    def __init__(
        self,
        hass: HomeAssistant,
        entry: ConfigEntry,
        description: NumberEntityDescription,
    ) -> None:
        """Initialize a M.A.C.S. number entity."""
        self.hass = hass
        self.entry = entry
        self.entity_description = description

        self._attr_unique_id = f"{entry.entry_id}_{description.key}"
        self._attr_translation_key = description.translation_key
        self._attr_icon = description.icon
        self._attr_device_info = MACS_DEVICE

    @property
    def native_value(self) -> float:
        """Return the current value."""
        return self._get_value()

    async def async_set_native_value(self, value: float) -> None:
        """Set native value."""
        safe_value = self._clamp(value)

        self.hass.data[DOMAIN][self.entry.entry_id][
            self.entity_description.key
        ] = safe_value

        self.async_write_ha_state()

    async def async_added_to_hass(self) -> None:
        """Register update listener."""

        @callback
        def _handle_update(event: Event) -> None:
            self.async_write_ha_state()

        self.async_on_remove(
            self.hass.bus.async_listen(
                f"{DOMAIN}_state_updated",
                _handle_update,
            )
        )

    def _get_value(self) -> float:
        """Get value from hass data."""
        fallback = DEFAULT_VALUES.get(self.entity_description.key, 0)

        value = (
            self.hass.data
            .get(DOMAIN, {})
            .get(self.entry.entry_id, {})
            .get(self.entity_description.key, fallback)
        )

        return self._clamp(value)

    def _clamp(self, value) -> float:
        """Clamp and sanitize a numeric value."""
        fallback = DEFAULT_VALUES.get(self.entity_description.key, 0)

        try:
            number = float(str(value).replace(",", "."))
        except (TypeError, ValueError):
            number = fallback

        min_value = self.entity_description.native_min_value
        max_value = self.entity_description.native_max_value

        if min_value is not None:
            number = max(min_value, number)

        if max_value is not None:
            number = min(max_value, number)

        return number

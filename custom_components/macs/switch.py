"""Switch entities for the M.A.C.S. integration."""

from __future__ import annotations

from homeassistant.components.switch import SwitchEntity, SwitchEntityDescription
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import Event, HomeAssistant, callback
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.restore_state import RestoreEntity

from .const import (
    ATTR_ANIMATIONS_ENABLED,
    ATTR_CHARGING,
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
    DEFAULT_ANIMATIONS_ENABLED,
    DEFAULT_CHARGING,
    DOMAIN,
    MACS_DEVICE,
)


SWITCH_DESCRIPTIONS: tuple[SwitchEntityDescription, ...] = (
    SwitchEntityDescription(
        key=ATTR_ANIMATIONS_ENABLED,
        translation_key="animations_enabled",
        icon="mdi:animation-play-outline",
    ),
    SwitchEntityDescription(
        key=ATTR_CHARGING,
        translation_key="charging",
        icon="mdi:battery-charging",
    ),
    SwitchEntityDescription(
        key=ATTR_WEATHER_CONDITIONS_SNOWY,
        translation_key="weather_conditions_snowy",
        icon="mdi:weather-snowy",
    ),
    SwitchEntityDescription(
        key=ATTR_WEATHER_CONDITIONS_CLOUDY,
        translation_key="weather_conditions_cloudy",
        icon="mdi:weather-cloudy",
    ),
    SwitchEntityDescription(
        key=ATTR_WEATHER_CONDITIONS_RAINY,
        translation_key="weather_conditions_rainy",
        icon="mdi:weather-rainy",
    ),
    SwitchEntityDescription(
        key=ATTR_WEATHER_CONDITIONS_WINDY,
        translation_key="weather_conditions_windy",
        icon="mdi:weather-windy",
    ),
    SwitchEntityDescription(
        key=ATTR_WEATHER_CONDITIONS_SUNNY,
        translation_key="weather_conditions_sunny",
        icon="mdi:weather-sunny",
    ),
    SwitchEntityDescription(
        key=ATTR_WEATHER_CONDITIONS_STORMY,
        translation_key="weather_conditions_stormy",
        icon="mdi:weather-lightning-rainy",
    ),
    SwitchEntityDescription(
        key=ATTR_WEATHER_CONDITIONS_FOGGY,
        translation_key="weather_conditions_foggy",
        icon="mdi:weather-fog",
    ),
    SwitchEntityDescription(
        key=ATTR_WEATHER_CONDITIONS_HAIL,
        translation_key="weather_conditions_hail",
        icon="mdi:weather-hail",
    ),
    SwitchEntityDescription(
        key=ATTR_WEATHER_CONDITIONS_LIGHTNING,
        translation_key="weather_conditions_lightning",
        icon="mdi:weather-lightning",
    ),
    SwitchEntityDescription(
        key=ATTR_WEATHER_CONDITIONS_PARTLYCLOUDY,
        translation_key="weather_conditions_partlycloudy",
        icon="mdi:weather-partly-cloudy",
    ),
    SwitchEntityDescription(
        key=ATTR_WEATHER_CONDITIONS_POURING,
        translation_key="weather_conditions_pouring",
        icon="mdi:weather-pouring",
    ),
    SwitchEntityDescription(
        key=ATTR_WEATHER_CONDITIONS_CLEAR_NIGHT,
        translation_key="weather_conditions_clear_night",
        icon="mdi:weather-night",
    ),
    SwitchEntityDescription(
        key=ATTR_WEATHER_CONDITIONS_EXCEPTIONAL,
        translation_key="weather_conditions_exceptional",
        icon="mdi:alert-circle-outline",
    ),
)


DEFAULT_VALUES: dict[str, bool] = {
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


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up M.A.C.S. switch entities."""
    hass.data.setdefault(DOMAIN, {})
    hass.data[DOMAIN].setdefault(entry.entry_id, {})

    for description in SWITCH_DESCRIPTIONS:
        hass.data[DOMAIN][entry.entry_id].setdefault(
            description.key,
            DEFAULT_VALUES.get(description.key, False),
        )

    async_add_entities(
        [
            MacsSwitch(hass, entry, description)
            for description in SWITCH_DESCRIPTIONS
        ]
    )


class MacsSwitch(SwitchEntity, RestoreEntity):
    """M.A.C.S. switch entity."""

    _attr_has_entity_name = True

    def __init__(
        self,
        hass: HomeAssistant,
        entry: ConfigEntry,
        description: SwitchEntityDescription,
    ) -> None:
        """Initialize a M.A.C.S. switch entity."""
        self.hass = hass
        self.entry = entry
        self.entity_description = description

        # IMPORTANT :
        # unique_id fixe et propre pour que __init__.py retrouve les entités.
        # Exemple attendu :
        # unique_id = macs_animations_enabled
        # entity_id = switch.macs_animations_enabled
        self._attr_unique_id = f"macs_{description.key}"
        self._attr_suggested_object_id = f"macs_{description.key}"

        self._attr_translation_key = description.translation_key
        self._attr_icon = description.icon
        self._attr_device_info = MACS_DEVICE

    @property
    def is_on(self) -> bool:
        """Return true if the switch is on."""
        return self._get_value()

    async def async_turn_on(self, **kwargs) -> None:
        """Turn on the switch."""
        await self._async_set_value(True)

    async def async_turn_off(self, **kwargs) -> None:
        """Turn off the switch."""
        await self._async_set_value(False)

    async def _async_set_value(self, value: bool) -> None:
        """Set switch value."""
        safe_value = bool(value)

        self.hass.data.setdefault(DOMAIN, {})
        self.hass.data[DOMAIN].setdefault(self.entry.entry_id, {})
        self.hass.data[DOMAIN][self.entry.entry_id][
            self.entity_description.key
        ] = safe_value

        self.async_write_ha_state()

        self.hass.bus.async_fire(
            f"{DOMAIN}_state_updated",
            {
                "entry_id": self.entry.entry_id,
                "key": self.entity_description.key,
                "value": safe_value,
            },
        )

    async def async_added_to_hass(self) -> None:
        """Restore state and register update listener."""
        await super().async_added_to_hass()

        self.hass.data.setdefault(DOMAIN, {})
        self.hass.data[DOMAIN].setdefault(self.entry.entry_id, {})

        last_state = await self.async_get_last_state()
        if last_state is not None:
            restored_value = last_state.state == "on"
            self.hass.data[DOMAIN][self.entry.entry_id][
                self.entity_description.key
            ] = restored_value
        else:
            self.hass.data[DOMAIN][self.entry.entry_id].setdefault(
                self.entity_description.key,
                DEFAULT_VALUES.get(self.entity_description.key, False),
            )

        @callback
        def _handle_update(event: Event) -> None:
            data = event.data or {}

            if data.get("entry_id") not in (None, self.entry.entry_id):
                return

            if data.get("key") not in (None, self.entity_description.key):
                return

            self.async_write_ha_state()

        self.async_on_remove(
            self.hass.bus.async_listen(
                f"{DOMAIN}_state_updated",
                _handle_update,
            )
        )

    def _get_value(self) -> bool:
        """Get the current boolean value."""
        fallback = DEFAULT_VALUES.get(self.entity_description.key, False)

        value = (
            self.hass.data
            .get(DOMAIN, {})
            .get(self.entry.entry_id, {})
            .get(self.entity_description.key, fallback)
        )

        if isinstance(value, bool):
            return value

        if isinstance(value, str):
            return value.strip().lower() in (
                "true",
                "on",
                "yes",
                "1",
                "enabled",
                "active",
            )

        if isinstance(value, (int, float)):
            return bool(value)

        return fallback

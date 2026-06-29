"""Climate platform for Compact 9000 BTU IR control."""

from __future__ import annotations

from typing import Any

from homeassistant.components.climate import (
    ATTR_FAN_MODE,
    ATTR_SWING_MODE,
    ATTR_TEMPERATURE,
    ClimateEntity,
    ClimateEntityFeature,
    HVACAction,
    HVACMode,
)
from homeassistant.components.climate.const import (
    FAN_HIGH,
    FAN_LOW,
    FAN_MEDIUM,
    SWING_OFF,
    SWING_VERTICAL,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import CONF_ENTITY_ID, UnitOfTemperature
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import HomeAssistantError, ServiceValidationError
from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.entity_platform import AddConfigEntryEntitiesCallback
from homeassistant.helpers.restore_state import RestoreEntity

from .const import (
    DEFAULT_EMITTER,
    DOMAIN,
    NAME,
    PICON_URL_PATH,
    TEMP_MAX_C,
    TEMP_MIN_C,
    TEMP_UNIT_CELSIUS,
)
from .ir import Compact9000BtuValidationError, async_send_compact_9000_btu, build_state

PARALLEL_UPDATES = 1

HVAC_TO_MODE = {
    HVACMode.AUTO: "auto",
    HVACMode.COOL: "cool",
    HVACMode.DRY: "dry",
    HVACMode.FAN_ONLY: "fan_only",
}

MODE_TO_HVAC = {value: key for key, value in HVAC_TO_MODE.items()}

HA_FAN_TO_PROTOCOL = {
    FAN_LOW: "low",
    FAN_MEDIUM: "mid",
    FAN_HIGH: "high",
}

PROTOCOL_FAN_TO_HA = {value: key for key, value in HA_FAN_TO_PROTOCOL.items()}


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddConfigEntryEntitiesCallback,
) -> None:
    """Set up the Compact 9000 BTU climate entity from a config entry."""
    async_add_entities([Compact9000BtuClimate(entry)])


class Compact9000BtuClimate(RestoreEntity, ClimateEntity):
    """Assumed-state climate entity for the IR-only Compact 9000 BTU AC."""

    _attr_assumed_state = True
    _attr_entity_picture = PICON_URL_PATH
    _attr_has_entity_name = True
    _attr_name = None
    _attr_should_poll = False
    _attr_supported_features = (
        ClimateEntityFeature.FAN_MODE
        | ClimateEntityFeature.SWING_MODE
        | ClimateEntityFeature.TARGET_TEMPERATURE
        | ClimateEntityFeature.TURN_OFF
        | ClimateEntityFeature.TURN_ON
    )
    _attr_temperature_unit = UnitOfTemperature.CELSIUS
    _attr_min_temp = TEMP_MIN_C
    _attr_max_temp = TEMP_MAX_C
    _attr_target_temperature_step = 1.0
    _attr_hvac_modes = [
        HVACMode.OFF,
        HVACMode.AUTO,
        HVACMode.COOL,
        HVACMode.DRY,
        HVACMode.FAN_ONLY,
    ]
    _attr_fan_modes = [FAN_LOW, FAN_MEDIUM, FAN_HIGH]
    _attr_swing_modes = [SWING_OFF, SWING_VERTICAL]

    def __init__(self, entry: ConfigEntry) -> None:
        """Initialize the Compact 9000 BTU climate entity."""
        self._attr_unique_id = "compact_9000_btu_ac"
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, "compact_9000_btu_ac")},
            manufacturer="Compact 9000 BTU platform",
            model="Tested: PEARL / Carlo Milano NX-7532-675",
            name=NAME,
        )
        self._emitter_entity_id = entry.data.get(CONF_ENTITY_ID, DEFAULT_EMITTER)
        self._attr_hvac_mode = HVACMode.OFF
        self._last_on_hvac_mode = HVACMode.COOL
        self._attr_hvac_action = HVACAction.OFF
        self._attr_target_temperature = 24
        self._attr_fan_mode = FAN_HIGH
        self._attr_swing_mode = SWING_OFF

    async def async_added_to_hass(self) -> None:
        """Restore the last optimistic AC state."""
        await super().async_added_to_hass()
        last_state = await self.async_get_last_state()
        if last_state is None:
            return

        try:
            restored_hvac_mode = HVACMode(last_state.state)
        except ValueError:
            restored_hvac_mode = None
        if restored_hvac_mode in self.hvac_modes:
            self._attr_hvac_mode = restored_hvac_mode
            if restored_hvac_mode != HVACMode.OFF:
                self._last_on_hvac_mode = restored_hvac_mode

        restored_temperature = last_state.attributes.get(ATTR_TEMPERATURE)
        if isinstance(restored_temperature, (int, float)):
            self._attr_target_temperature = int(round(restored_temperature))

        restored_fan = last_state.attributes.get(ATTR_FAN_MODE)
        if restored_fan in self.fan_modes:
            self._attr_fan_mode = restored_fan

        restored_swing = last_state.attributes.get(ATTR_SWING_MODE)
        if restored_swing in self.swing_modes:
            self._attr_swing_mode = restored_swing

        self._apply_mode_constraints()
        self._update_hvac_action()

    @property
    def hvac_mode(self) -> HVACMode:
        """Return the currently assumed HVAC mode."""
        return self._attr_hvac_mode

    @property
    def hvac_action(self) -> HVACAction:
        """Return the currently assumed HVAC action."""
        return self._attr_hvac_action

    @property
    def target_temperature(self) -> int:
        """Return the currently assumed target temperature."""
        return self._attr_target_temperature

    @property
    def fan_mode(self) -> str:
        """Return the currently assumed fan mode."""
        return self._attr_fan_mode

    @property
    def swing_mode(self) -> str:
        """Return the currently assumed swing mode."""
        return self._attr_swing_mode

    async def async_turn_on(self) -> None:
        """Turn the AC on using the last assumed on-state."""
        await self.async_set_hvac_mode(self._last_on_hvac_mode)

    async def async_turn_off(self) -> None:
        """Turn the AC off."""
        await self.async_set_hvac_mode(HVACMode.OFF)

    async def async_set_hvac_mode(self, hvac_mode: HVACMode) -> None:
        """Set the HVAC mode and send the full IR state."""
        if hvac_mode not in self.hvac_modes:
            raise ServiceValidationError(
                translation_domain=DOMAIN,
                translation_key="invalid_state",
                translation_placeholders={"error": f"unsupported hvac mode {hvac_mode}"},
            )

        self._attr_hvac_mode = hvac_mode
        if hvac_mode != HVACMode.OFF:
            self._last_on_hvac_mode = hvac_mode
        self._apply_mode_constraints()
        await self._async_send_current_state()

    async def async_set_temperature(self, **kwargs: Any) -> None:
        """Set target temperature and send the full IR state."""
        if (temperature := kwargs.get(ATTR_TEMPERATURE)) is None:
            return
        self._attr_target_temperature = int(round(float(temperature)))
        if self._attr_hvac_mode == HVACMode.OFF:
            self._attr_hvac_mode = self._last_on_hvac_mode
        self._apply_mode_constraints()
        await self._async_send_current_state()

    async def async_set_fan_mode(self, fan_mode: str) -> None:
        """Set fan mode where the captured AC mode allows it."""
        if fan_mode not in self.fan_modes:
            raise HomeAssistantError(f"Unsupported fan mode: {fan_mode}")
        if self._attr_hvac_mode in {HVACMode.AUTO, HVACMode.FAN_ONLY} and fan_mode != FAN_HIGH:
            raise ServiceValidationError(
                translation_domain=DOMAIN,
                translation_key="invalid_state",
                translation_placeholders={
                    "error": f"{self._attr_hvac_mode.value} is fixed to fan high"
                },
            )
        if self._attr_hvac_mode == HVACMode.DRY and fan_mode != FAN_LOW:
            raise ServiceValidationError(
                translation_domain=DOMAIN,
                translation_key="invalid_state",
                translation_placeholders={"error": "dry is fixed to fan low"},
            )

        self._attr_fan_mode = fan_mode
        if self._attr_hvac_mode == HVACMode.OFF:
            self._attr_hvac_mode = self._last_on_hvac_mode
        self._apply_mode_constraints()
        await self._async_send_current_state()

    async def async_set_swing_mode(self, swing_mode: str) -> None:
        """Set vertical swing mode and send the full IR state."""
        if swing_mode not in self.swing_modes:
            raise HomeAssistantError(f"Unsupported swing mode: {swing_mode}")
        self._attr_swing_mode = swing_mode
        if self._attr_hvac_mode == HVACMode.OFF:
            self._attr_hvac_mode = self._last_on_hvac_mode
        await self._async_send_current_state()

    async def _async_send_current_state(self) -> None:
        """Build and send the currently assumed state."""
        hvac_mode = self._attr_hvac_mode
        mode = "off" if hvac_mode == HVACMode.OFF else HVAC_TO_MODE[hvac_mode]
        try:
            state = build_state(
                power=hvac_mode != HVACMode.OFF,
                mode=mode,
                temperature=int(self._attr_target_temperature or 24),
                fan=HA_FAN_TO_PROTOCOL[self._attr_fan_mode or FAN_HIGH],
                swing=self._attr_swing_mode == SWING_VERTICAL,
                temperature_unit=TEMP_UNIT_CELSIUS,
            )
        except Compact9000BtuValidationError as err:
            raise ServiceValidationError(
                translation_domain=DOMAIN,
                translation_key="invalid_state",
                translation_placeholders={"error": str(err)},
            ) from err

        await async_send_compact_9000_btu(
            self.hass,
            self._emitter_entity_id,
            state,
            context=self._context,
        )
        self._update_hvac_action()
        self.async_write_ha_state()

    def _apply_mode_constraints(self) -> None:
        """Apply captured fixed fan constraints for non-cool modes."""
        if self._attr_hvac_mode == HVACMode.DRY:
            self._attr_fan_mode = FAN_LOW
        elif self._attr_hvac_mode in {HVACMode.AUTO, HVACMode.FAN_ONLY}:
            self._attr_fan_mode = FAN_HIGH

    def _update_hvac_action(self) -> None:
        """Update the optimistic HVAC action."""
        if self._attr_hvac_mode == HVACMode.OFF:
            self._attr_hvac_action = HVACAction.OFF
        elif self._attr_hvac_mode == HVACMode.DRY:
            self._attr_hvac_action = HVACAction.DRYING
        elif self._attr_hvac_mode == HVACMode.FAN_ONLY:
            self._attr_hvac_action = HVACAction.FAN
        else:
            self._attr_hvac_action = HVACAction.COOLING

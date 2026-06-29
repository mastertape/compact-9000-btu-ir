"""Compact 9000 BTU IR service integration."""

from __future__ import annotations

import logging
from pathlib import Path

import voluptuous as vol

from homeassistant.components.http import StaticPathConfig
from homeassistant.components.infrared import DOMAIN as INFRARED_DOMAIN
from homeassistant.config_entries import SOURCE_IMPORT, ConfigEntry
from homeassistant.const import CONF_ENTITY_ID, Platform
from homeassistant.core import HomeAssistant, ServiceCall
from homeassistant.exceptions import ServiceValidationError
from homeassistant.helpers import config_validation as cv
from homeassistant.helpers.typing import ConfigType

from .const import (
    CONF_CODE,
    CONF_FAN,
    CONF_MODE,
    CONF_POWER,
    CONF_REPEAT,
    CONF_SWING,
    CONF_TEMPERATURE,
    CONF_TEMPERATURE_UNIT,
    CONF_TIMER_HOURS,
    DEFAULT_EMITTER,
    DOMAIN,
    FANS,
    MAX_REPEAT,
    MODES,
    PICON_URL_PATH,
    TEMP_MAX_F,
    TEMP_MIN_C,
    TEMP_UNITS,
)
from .ir import (
    Compact9000BtuValidationError,
    async_send_compact_9000_btu,
    build_max_cool_state,
    build_state,
    parse_hex_code,
)

_LOGGER = logging.getLogger(__name__)

PLATFORMS: list[Platform] = [Platform.CLIMATE]


def _infrared_entity_id(value: str) -> str:
    """Validate an infrared entity ID."""
    entity_id = cv.entity_id(value)
    if entity_id.split(".", 1)[0] != INFRARED_DOMAIN:
        raise vol.Invalid("Entity must be an infrared entity")
    return entity_id


def _compact_9000_btu_hex_code(value: str) -> str:
    """Validate a Compact 9000 BTU capture hex code and keep the original string."""
    value = cv.string(value)
    try:
        parse_hex_code(value)
    except Compact9000BtuValidationError as err:
        raise vol.Invalid(str(err)) from err
    return value


SEND_HEX_SCHEMA = vol.Schema(
    {
        vol.Required(CONF_ENTITY_ID): _infrared_entity_id,
        vol.Required(CONF_CODE): _compact_9000_btu_hex_code,
        vol.Optional(CONF_REPEAT, default=0): vol.All(
            vol.Coerce(int), vol.Range(min=0, max=MAX_REPEAT)
        ),
    }
)

SEND_STATE_SCHEMA = vol.Schema(
    {
        vol.Required(CONF_ENTITY_ID): _infrared_entity_id,
        vol.Optional(CONF_POWER, default=True): cv.boolean,
        vol.Optional(CONF_MODE, default="cool"): vol.In(MODES),
        vol.Required(CONF_TEMPERATURE): vol.All(
            vol.Coerce(int), vol.Range(min=TEMP_MIN_C, max=TEMP_MAX_F)
        ),
        vol.Optional(CONF_TEMPERATURE_UNIT, default="celsius"): vol.In(TEMP_UNITS),
        vol.Optional(CONF_FAN, default="high"): vol.In(FANS),
        vol.Optional(CONF_SWING, default=False): cv.boolean,
        vol.Optional(CONF_TIMER_HOURS, default=None): vol.Any(
            None,
            vol.All(vol.Coerce(int), vol.Range(min=0, max=24)),
        ),
        vol.Optional(CONF_REPEAT, default=0): vol.All(
            vol.Coerce(int), vol.Range(min=0, max=MAX_REPEAT)
        ),
    }
)

SEND_MAX_COOL_SCHEMA = vol.Schema(
    {
        vol.Required(CONF_ENTITY_ID): _infrared_entity_id,
        vol.Optional(CONF_SWING, default=False): cv.boolean,
        vol.Optional(CONF_REPEAT, default=0): vol.All(
            vol.Coerce(int), vol.Range(min=0, max=MAX_REPEAT)
        ),
    }
)

CONFIG_SCHEMA = vol.Schema({DOMAIN: vol.Any(None, {})}, extra=vol.ALLOW_EXTRA)


async def async_setup(hass: HomeAssistant, config: ConfigType) -> bool:
    """Set up Compact 9000 BTU IR services."""
    _LOGGER.info("Setting up %s", DOMAIN)
    domain_config = config.get(DOMAIN) or {}
    await hass.http.async_register_static_paths(
        [
            StaticPathConfig(
                PICON_URL_PATH,
                str(Path(__file__).with_name("picon.png")),
                True,
            )
        ]
    )

    async def async_send_hex(call: ServiceCall) -> None:
        """Send a validated Compact 9000 BTU capture frame."""
        try:
            state = parse_hex_code(call.data[CONF_CODE])
        except Compact9000BtuValidationError as err:
            raise ServiceValidationError(
                translation_domain=DOMAIN,
                translation_key="invalid_hex_code",
                translation_placeholders={"error": str(err)},
            ) from err

        await async_send_compact_9000_btu(
            hass,
            call.data[CONF_ENTITY_ID],
            state,
            repeat=call.data[CONF_REPEAT],
            context=call.context,
        )

    async def async_send_max_cool(call: ServiceCall) -> None:
        """Send the strongest confirmed remote-sendable COOL state."""
        state = build_max_cool_state(swing=call.data[CONF_SWING])
        await async_send_compact_9000_btu(
            hass,
            call.data[CONF_ENTITY_ID],
            state,
            repeat=call.data[CONF_REPEAT],
            context=call.context,
        )

    async def async_send_state(call: ServiceCall) -> None:
        """Build and send a Compact 9000 BTU state frame."""
        try:
            state = build_state(
                power=call.data[CONF_POWER],
                mode=call.data[CONF_MODE],
                temperature=call.data[CONF_TEMPERATURE],
                temperature_unit=call.data[CONF_TEMPERATURE_UNIT],
                fan=call.data[CONF_FAN],
                swing=call.data[CONF_SWING],
                timer_hours=call.data[CONF_TIMER_HOURS],
            )
        except Compact9000BtuValidationError as err:
            raise ServiceValidationError(
                translation_domain=DOMAIN,
                translation_key="invalid_state",
                translation_placeholders={"error": str(err)},
            ) from err

        await async_send_compact_9000_btu(
            hass,
            call.data[CONF_ENTITY_ID],
            state,
            repeat=call.data[CONF_REPEAT],
            context=call.context,
        )

    if not hass.services.has_service(DOMAIN, "send_hex"):
        hass.services.async_register(
            DOMAIN,
            "send_hex",
            async_send_hex,
            schema=SEND_HEX_SCHEMA,
        )

    if not hass.services.has_service(DOMAIN, "send_state"):
        hass.services.async_register(
            DOMAIN,
            "send_state",
            async_send_state,
            schema=SEND_STATE_SCHEMA,
        )

    if not hass.services.has_service(DOMAIN, "send_max_cool"):
        hass.services.async_register(
            DOMAIN,
            "send_max_cool",
            async_send_max_cool,
            schema=SEND_MAX_COOL_SCHEMA,
        )

    _LOGGER.info("Registered %s service actions", DOMAIN)

    if DOMAIN in config:
        _LOGGER.info("Found YAML configuration for %s; importing config entry", DOMAIN)
        hass.async_create_task(
            hass.config_entries.flow.async_init(
                DOMAIN,
                context={"source": SOURCE_IMPORT},
                data=domain_config,
            )
        )
    else:
        _LOGGER.info("No YAML configuration found for %s", DOMAIN)

    return True


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up Compact 9000 BTU IR from a config entry."""
    _LOGGER.info("Setting up %s config entry %s", DOMAIN, entry.entry_id)
    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    _LOGGER.info("Forwarded %s platforms: %s", DOMAIN, PLATFORMS)
    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a config entry."""
    return await hass.config_entries.async_unload_platforms(entry, PLATFORMS)

"""Config flow for Compact 9000 BTU IR."""

from __future__ import annotations

import voluptuous as vol

from homeassistant import config_entries
from homeassistant.components.infrared import DOMAIN as INFRARED_DOMAIN
from homeassistant.const import CONF_ENTITY_ID
from homeassistant.helpers import config_validation as cv

from .const import DEFAULT_EMITTER, DOMAIN, NAME


def _infrared_entity_id(value: str) -> str:
    """Validate an infrared entity ID."""
    entity_id = cv.entity_id(value)
    if entity_id.split(".", 1)[0] != INFRARED_DOMAIN:
        raise vol.Invalid("Entity must be an infrared entity")
    return entity_id


class Compact9000BtuIrConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a config flow for Compact 9000 BTU IR."""

    VERSION = 1

    async def async_step_user(self, user_input=None):
        """Handle the initial step."""
        await self.async_set_unique_id(DOMAIN)
        self._abort_if_unique_id_configured()

        if user_input is not None:
            return self.async_create_entry(title=NAME, data=user_input)

        schema = vol.Schema(
            {
                vol.Optional(CONF_ENTITY_ID, default=DEFAULT_EMITTER): (
                    _infrared_entity_id
                )
            }
        )
        return self.async_show_form(step_id="user", data_schema=schema)

    async def async_step_import(self, import_config):
        """Import YAML configuration."""
        await self.async_set_unique_id(DOMAIN)
        self._abort_if_unique_id_configured()
        return self.async_create_entry(title=NAME, data=import_config)

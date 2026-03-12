"""Config flow for BlindCtrl integration."""
from __future__ import annotations

import logging
from typing import Any

import aiohttp
import voluptuous as vol

from homeassistant.config_entries import ConfigFlow, ConfigFlowResult, OptionsFlow
from homeassistant.helpers.aiohttp_client import async_get_clientsession

from .api import BlindCtrlApi
from .const import (
    CLOSE_DOWN,
    CLOSE_UP,
    CONF_CLOSE_DIRECTION,
    CONF_HOST,
    CONF_PORT,
    DEFAULT_PORT,
    DOMAIN,
)

_LOGGER = logging.getLogger(__name__)

STEP_USER_DATA_SCHEMA = vol.Schema(
    {
        vol.Required(CONF_HOST): str,
        vol.Optional(CONF_PORT, default=DEFAULT_PORT): int,
        vol.Optional(CONF_CLOSE_DIRECTION, default=CLOSE_UP): vol.In(
            {CLOSE_DOWN: "Close Down (0)", CLOSE_UP: "Close Up (200)"}
        ),
    }
)


class BlindCtrlConfigFlow(ConfigFlow, domain=DOMAIN):
    """Handle a config flow for BlindCtrl."""

    VERSION = 1

    @staticmethod
    def async_get_options_flow(config_entry):
        return BlindCtrlOptionsFlow(config_entry)

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Handle the initial step where the user enters the hub address."""
        errors: dict[str, str] = {}

        if user_input is not None:
            host = user_input[CONF_HOST]
            port = user_input.get(CONF_PORT, DEFAULT_PORT)

            await self.async_set_unique_id(f"{host}:{port}")
            self._abort_if_unique_id_configured()

            session = async_get_clientsession(self.hass)
            api = BlindCtrlApi(host, port, session)

            if await api.async_test_connection():
                return self.async_create_entry(
                    title=f"BlindCtrl ({host})",
                    data={
                        CONF_HOST: host,
                        CONF_PORT: port,
                        CONF_CLOSE_DIRECTION: user_input.get(
                            CONF_CLOSE_DIRECTION, CLOSE_UP
                        ),
                    },
                )
            else:
                errors["base"] = "cannot_connect"

        return self.async_show_form(
            step_id="user",
            data_schema=STEP_USER_DATA_SCHEMA,
            errors=errors,
        )


class BlindCtrlOptionsFlow(OptionsFlow):
    """Handle options for BlindCtrl."""

    def __init__(self, config_entry):
        self.config_entry = config_entry

    async def async_step_init(self, user_input=None):
        if user_input is not None:
            self.hass.config_entries.async_update_entry(
                self.config_entry,
                data={**self.config_entry.data, **user_input},
            )
            return self.async_create_entry(title="", data={})

        current = self.config_entry.data.get(CONF_CLOSE_DIRECTION, CLOSE_UP)
        schema = vol.Schema(
            {
                vol.Optional(CONF_CLOSE_DIRECTION, default=current): vol.In(
                    {CLOSE_DOWN: "Close Down (0)", CLOSE_UP: "Close Up (200)"}
                ),
            }
        )
        return self.async_show_form(step_id="init", data_schema=schema)

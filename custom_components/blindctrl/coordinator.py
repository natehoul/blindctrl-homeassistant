"""Data coordinator for BlindCtrl integration."""
from __future__ import annotations

from datetime import timedelta
import logging

import aiohttp
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.aiohttp_client import async_get_clientsession
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .api import BlindCtrlApi, BlindCtrlApiError
from .const import CONF_HOST, CONF_PORT, DEFAULT_PORT, DOMAIN, SCAN_INTERVAL_SECONDS

_LOGGER = logging.getLogger(__name__)


class BlindCtrlCoordinator(DataUpdateCoordinator):
    """Coordinator to manage fetching blind data from the API."""

    def __init__(self, hass: HomeAssistant, entry: ConfigEntry) -> None:
        super().__init__(
            hass,
            _LOGGER,
            name=DOMAIN,
            update_interval=timedelta(seconds=SCAN_INTERVAL_SECONDS),
        )
        session = async_get_clientsession(hass)
        self.api = BlindCtrlApi(
            host=entry.data[CONF_HOST],
            port=entry.data.get(CONF_PORT, DEFAULT_PORT),
            session=session,
        )
        self.entry = entry

    async def _async_update_data(self) -> list[dict]:
        try:
            return await self.api.async_get_blinds()
        except BlindCtrlApiError as err:
            raise UpdateFailed(f"Error communicating with BlindCtrl: {err}") from err

"""Cover platform for BlindCtrl integration."""
from __future__ import annotations

import logging
from typing import Any

from homeassistant.components.cover import (
    CoverDeviceClass,
    CoverEntity,
    CoverEntityFeature,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import BLIND_MAX_POSITION, DOMAIN
from .coordinator import BlindCtrlCoordinator

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up BlindCtrl covers from a config entry."""
    coordinator: BlindCtrlCoordinator = hass.data[DOMAIN][entry.entry_id]

    entities = []
    for blind in coordinator.data:
        if blind.get("isIdentified", False):
            entities.append(BlindCtrlCover(coordinator, blind))

    async_add_entities(entities, True)


class BlindCtrlCover(CoordinatorEntity, CoverEntity):
    """Representation of a BlindCtrl blind as a cover entity."""

    _attr_device_class = CoverDeviceClass.BLIND
    _attr_supported_features = (
        CoverEntityFeature.OPEN
        | CoverEntityFeature.CLOSE
        | CoverEntityFeature.SET_POSITION
        | CoverEntityFeature.STOP
    )
    _attr_has_entity_name = True

    def __init__(
        self, coordinator: BlindCtrlCoordinator, blind_data: dict
    ) -> None:
        super().__init__(coordinator)
        self._blind_id: int = blind_data["id"]
        self._attr_unique_id = f"blindctrl_{blind_data['macAddress']}"
        self._attr_name = blind_data.get("name", f"Blind {self._blind_id}")

        self._attr_device_info = {
            "identifiers": {(DOMAIN, blind_data["macAddress"])},
            "name": blind_data.get("name", f"Blind {self._blind_id}"),
            "manufacturer": "BlindCtrl",
            "model": "BLE Smart Blind",
            "sw_version": "1.0.0",
        }
        if blind_data.get("room"):
            self._attr_device_info["suggested_area"] = blind_data["room"]

    @property
    def _blind_data(self) -> dict | None:
        if self.coordinator.data:
            for blind in self.coordinator.data:
                if blind["id"] == self._blind_id:
                    return blind
        return None

    @property
    def available(self) -> bool:
        data = self._blind_data
        if data is None:
            return False
        return data.get("isOnline", False) and super().available

    @property
    def current_cover_position(self) -> int | None:
        data = self._blind_data
        if data is None:
            return None
        raw_position = data.get("position", 0)
        return round((raw_position / BLIND_MAX_POSITION) * 100)

    @property
    def is_closed(self) -> bool | None:
        pos = self.current_cover_position
        if pos is None:
            return None
        return pos == 0

    async def async_open_cover(self, **kwargs: Any) -> None:
        await self.coordinator.api.async_set_position(
            self._blind_id, BLIND_MAX_POSITION
        )
        await self.coordinator.async_request_refresh()

    async def async_close_cover(self, **kwargs: Any) -> None:
        await self.coordinator.api.async_set_position(self._blind_id, 0)
        await self.coordinator.async_request_refresh()

    async def async_set_cover_position(self, **kwargs: Any) -> None:
        ha_position = kwargs.get("position", 0)
        raw_position = round((ha_position / 100) * BLIND_MAX_POSITION)
        await self.coordinator.api.async_set_position(self._blind_id, raw_position)
        await self.coordinator.async_request_refresh()

    async def async_stop_cover(self, **kwargs: Any) -> None:
        pass

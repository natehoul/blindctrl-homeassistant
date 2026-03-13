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

from .const import (
    BLIND_MAX_POSITION,
    BLIND_OPEN_POSITION,
    CLOSE_DOWN,
    CLOSE_UP,
    CONF_CLOSE_DIRECTION,
    DOMAIN,
)
from .coordinator import BlindCtrlCoordinator

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up BlindCtrl covers from a config entry."""
    coordinator: BlindCtrlCoordinator = hass.data[DOMAIN][entry.entry_id]

    close_direction = entry.data.get(CONF_CLOSE_DIRECTION, CLOSE_UP)

    entities = []
    for blind in coordinator.data:
        if blind.get("isIdentified", False):
            entities.append(BlindCtrlCover(coordinator, blind, close_direction))

    async_add_entities(entities, True)


class BlindCtrlCover(CoordinatorEntity, CoverEntity):
    """Representation of a BlindCtrl blind as a cover entity.

    Blind has 3 positions: 0 (down), 100 (open), 200 (up).

    HA position mapping depends on close_direction config:

    close_direction = "up" (default):
      - HA 0%   = blind 200 (closed/up)
      - HA 100% = blind 0   (fully down)
      - Open button  → blind 100
      - Close button → blind 200

    close_direction = "down":
      - HA 0%   = blind 0   (closed/down)
      - HA 100% = blind 200 (fully up)
      - Open button  → blind 100
      - Close button → blind 0
    """

    _attr_device_class = CoverDeviceClass.BLIND
    _attr_supported_features = (
        CoverEntityFeature.OPEN
        | CoverEntityFeature.CLOSE
        | CoverEntityFeature.SET_POSITION
    )
    _attr_has_entity_name = True

    def __init__(
        self,
        coordinator: BlindCtrlCoordinator,
        blind_data: dict,
        close_direction: str,
    ) -> None:
        super().__init__(coordinator)
        self._blind_id: int = blind_data["id"]
        self._close_direction = close_direction
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
    def _close_position(self) -> int:
        return BLIND_MAX_POSITION if self._close_direction == CLOSE_UP else 0

    @property
    def _blind_data(self) -> dict | None:
        if self.coordinator.data:
            for blind in self.coordinator.data:
                if blind["id"] == self._blind_id:
                    return blind
        return None

    def _raw_to_ha(self, raw_position: int) -> int:
        """Convert blind position (0-200) to HA position (0-100).

        HA expects 0 = closed, 100 = open.
        When close_direction is "up": blind 200 is closed, so invert.
        When close_direction is "down": blind 0 is closed, so direct map.
        """
        if self._close_direction == CLOSE_UP:
            return round(((BLIND_MAX_POSITION - raw_position) / BLIND_MAX_POSITION) * 100)
        return round((raw_position / BLIND_MAX_POSITION) * 100)

    def _ha_to_raw(self, ha_position: int) -> int:
        """Convert HA position (0-100) to blind position (0-200)."""
        if self._close_direction == CLOSE_UP:
            return round(BLIND_MAX_POSITION - (ha_position / 100) * BLIND_MAX_POSITION)
        return round((ha_position / 100) * BLIND_MAX_POSITION)

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
        return self._raw_to_ha(raw_position)

    @property
    def is_closed(self) -> bool | None:
        data = self._blind_data
        if data is None:
            return None
        raw_position = data.get("position", 0)
        return raw_position == self._close_position

    async def async_open_cover(self, **kwargs: Any) -> None:
        """Open the blind (move to position 100)."""
        await self.coordinator.api.async_set_position(
            self._blind_id, BLIND_OPEN_POSITION
        )
        await self.coordinator.async_request_refresh()

    async def async_close_cover(self, **kwargs: Any) -> None:
        """Close the blind (move to configured close direction)."""
        await self.coordinator.api.async_set_position(
            self._blind_id, self._close_position
        )
        await self.coordinator.async_request_refresh()

    async def async_set_cover_position(self, **kwargs: Any) -> None:
        """Set blind position. Converts HA 0-100% to blind 0-200."""
        ha_position = kwargs.get("position", 0)
        raw_position = self._ha_to_raw(ha_position)
        await self.coordinator.api.async_set_position(self._blind_id, raw_position)
        await self.coordinator.async_request_refresh()

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
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import (
    BLIND_MAX_POSITION,
    BLIND_OPEN_POSITION,
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
    coordinator: BlindCtrlCoordinator = hass.data[DOMAIN][entry.entry_id]
    close_direction = entry.data.get(CONF_CLOSE_DIRECTION, CLOSE_UP)

    entities = []
    for blind in coordinator.data:
        if blind.get("isIdentified", False):
            entities.append(BlindCtrlCover(coordinator, blind, close_direction))

    async_add_entities(entities, True)


class BlindCtrlCover(CoordinatorEntity, CoverEntity):
    """Cover entity for a BlindCtrl blind.

    The blind has three positions: 0 (down), 100 (open), 200 (up).
    HA covers expect 0% = closed and 100% = fully open, and grey
    out the Close button at 0% and the Open button at 100%.

    To keep both buttons always active, we clamp the reported HA
    position to 1-99%. The actual state label (Open/Closed) is
    driven by is_closed, which checks the real blind position
    against the configured close direction.

    Open button  -> blind 100 (open)
    Close button -> blind 0 (down) or 200 (up) per close_direction
    Slider       -> full 0-200 range via set_position
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

    @property
    def _raw_position(self) -> int:
        data = self._blind_data
        if data is None:
            return 0
        return data.get("position", 0)

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
        ha_pos = round((self._raw_position / BLIND_MAX_POSITION) * 100)
        if ha_pos <= 0:
            return 1
        if ha_pos >= 100:
            return 99
        return ha_pos

    @property
    def is_closed(self) -> bool | None:
        data = self._blind_data
        if data is None:
            return None
        return self._raw_position == self._close_position

    @property
    def is_opening(self) -> bool:
        return False

    @property
    def is_closing(self) -> bool:
        return False

    async def async_open_cover(self, **kwargs: Any) -> None:
        await self.coordinator.api.async_set_position(
            self._blind_id, BLIND_OPEN_POSITION
        )
        await self.coordinator.async_request_refresh()

    async def async_close_cover(self, **kwargs: Any) -> None:
        await self.coordinator.api.async_set_position(
            self._blind_id, self._close_position
        )
        await self.coordinator.async_request_refresh()

    async def async_set_cover_position(self, **kwargs: Any) -> None:
        ha_position = kwargs.get("position", 0)
        raw_position = round((ha_position / 100) * BLIND_MAX_POSITION)
        await self.coordinator.api.async_set_position(self._blind_id, raw_position)
        await self.coordinator.async_request_refresh()

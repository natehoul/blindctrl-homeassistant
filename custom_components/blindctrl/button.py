"""Button platform for BlindCtrl integration.

Provides three always-available buttons per blind: Down, Open, Up.
These bypass HA's cover position logic so they never get greyed out.
"""
from __future__ import annotations

import logging
from typing import Any

from homeassistant.components.button import ButtonEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import BLIND_MAX_POSITION, BLIND_OPEN_POSITION, DOMAIN
from .coordinator import BlindCtrlCoordinator

_LOGGER = logging.getLogger(__name__)

BUTTON_DEFINITIONS = [
    {"key": "down", "label": "Down", "icon": "mdi:arrow-down", "position": 0},
    {"key": "open", "label": "Open", "icon": "mdi:blinds-open", "position": BLIND_OPEN_POSITION},
    {"key": "up", "label": "Up", "icon": "mdi:arrow-up", "position": BLIND_MAX_POSITION},
]


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    coordinator: BlindCtrlCoordinator = hass.data[DOMAIN][entry.entry_id]

    entities = []
    for blind in coordinator.data:
        if blind.get("isIdentified", False):
            for btn_def in BUTTON_DEFINITIONS:
                entities.append(
                    BlindCtrlButton(coordinator, blind, btn_def)
                )

    async_add_entities(entities, True)


class BlindCtrlButton(CoordinatorEntity, ButtonEntity):
    """A button that sends a specific position to a blind."""

    _attr_has_entity_name = True

    def __init__(
        self,
        coordinator: BlindCtrlCoordinator,
        blind_data: dict,
        btn_def: dict,
    ) -> None:
        super().__init__(coordinator)
        self._blind_id: int = blind_data["id"]
        self._position: int = btn_def["position"]
        self._attr_unique_id = f"blindctrl_{blind_data['macAddress']}_{btn_def['key']}"
        self._attr_name = f"{blind_data.get('name', f'Blind {self._blind_id}')} {btn_def['label']}"
        self._attr_icon = btn_def["icon"]

        self._attr_device_info = {
            "identifiers": {(DOMAIN, blind_data["macAddress"])},
            "name": blind_data.get("name", f"Blind {self._blind_id}"),
            "manufacturer": "BlindCtrl",
            "model": "BLE Smart Blind",
            "sw_version": "1.0.0",
        }

    async def async_press(self) -> None:
        await self.coordinator.api.async_set_position(
            self._blind_id, self._position
        )
        await self.coordinator.async_request_refresh()

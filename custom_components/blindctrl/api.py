"""API client for BlindCtrl hub."""
from __future__ import annotations

import asyncio
import logging
from typing import Any

import aiohttp

_LOGGER = logging.getLogger(__name__)


class BlindCtrlApiError(Exception):
    """Exception for API errors."""


class BlindCtrlApi:
    """Client to communicate with the BlindCtrl API."""

    def __init__(self, host: str, port: int, session: aiohttp.ClientSession) -> None:
        self._host = host
        self._port = port
        self._session = session
        self._base_url = f"http://{host}:{port}"

    @property
    def base_url(self) -> str:
        return self._base_url

    async def _request(
        self, method: str, path: str, json: dict | None = None
    ) -> Any:
        url = f"{self._base_url}{path}"
        try:
            async with self._session.request(
                method, url, json=json, timeout=aiohttp.ClientTimeout(total=10)
            ) as resp:
                if resp.status >= 400:
                    text = await resp.text()
                    raise BlindCtrlApiError(
                        f"{method} {path} returned {resp.status}: {text}"
                    )
                return await resp.json()
        except asyncio.TimeoutError as err:
            raise BlindCtrlApiError(f"Timeout connecting to {url}") from err
        except aiohttp.ClientError as err:
            raise BlindCtrlApiError(f"Error connecting to {url}: {err}") from err

    async def async_get_blinds(self) -> list[dict]:
        return await self._request("GET", "/api/blinds")

    async def async_get_blind(self, blind_id: int) -> dict:
        return await self._request("GET", f"/api/blinds/{blind_id}")

    async def async_set_position(self, blind_id: int, position: int) -> dict:
        return await self._request(
            "PATCH", f"/api/blinds/{blind_id}/position", json={"position": position}
        )

    async def async_test_connection(self) -> bool:
        try:
            await self._request("GET", "/api/blinds")
            return True
        except BlindCtrlApiError:
            return False

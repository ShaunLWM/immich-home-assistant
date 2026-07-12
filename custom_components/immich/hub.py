"""Hub for Immich integration."""
from __future__ import annotations

import logging
from urllib.parse import urljoin

import aiohttp

from homeassistant.exceptions import HomeAssistantError

_HEADER_API_KEY = "x-api-key"
_LOGGER = logging.getLogger(__name__)

_ALLOWED_MIME_TYPES = ["image/png", "image/jpeg"]
_REQUEST_TIMEOUT = aiohttp.ClientTimeout(total=30)


class ImmichHub:
    """Immich API hub."""

    def __init__(self, host: str, api_key: str) -> None:
        """Initialize."""
        self.host = host
        self.api_key = api_key
        self._session: aiohttp.ClientSession | None = None

    @property
    def _headers(self) -> dict[str, str]:
        """Return common headers."""
        return {"Accept": "application/json", _HEADER_API_KEY: self.api_key}

    async def _get_session(self) -> aiohttp.ClientSession:
        """Get or create a reusable client session."""
        if self._session is None or self._session.closed:
            self._session = aiohttp.ClientSession(timeout=_REQUEST_TIMEOUT)
        return self._session

    async def close(self) -> None:
        """Close the client session."""
        if self._session and not self._session.closed:
            await self._session.close()
            self._session = None

    async def authenticate(self) -> bool:
        """Test if we can authenticate with the host."""
        try:
            session = await self._get_session()
            url = urljoin(self.host, "/api/auth/validateToken")

            async with session.post(url=url, headers=self._headers) as response:
                if response.status != 200:
                    raw_result = await response.text()
                    _LOGGER.error("Error from API: body=%s", raw_result)
                    return False

                auth_result = await response.json()

                if not auth_result.get("authStatus"):
                    _LOGGER.error("Auth failed: body=%s", auth_result)
                    return False

                return True
        except aiohttp.ClientError as exception:
            _LOGGER.error("Error connecting to the API: %s", exception)
            raise CannotConnect from exception

    async def get_my_user_info(self) -> dict:
        """Get user info."""
        try:
            session = await self._get_session()
            url = urljoin(self.host, "/api/users/me")

            async with session.get(url=url, headers=self._headers) as response:
                if response.status != 200:
                    raw_result = await response.text()
                    _LOGGER.error("Error from API: body=%s", raw_result)
                    raise ApiError()

                user_info: dict = await response.json()

                return user_info
        except aiohttp.ClientError as exception:
            _LOGGER.error("Error connecting to the API: %s", exception)
            raise CannotConnect from exception

    async def get_asset_info(self, asset_id: str) -> dict | None:
        """Get asset info."""
        try:
            session = await self._get_session()
            url = urljoin(self.host, f"/api/assets/{asset_id}")

            async with session.get(url=url, headers=self._headers) as response:
                if response.status != 200:
                    raw_result = await response.text()
                    _LOGGER.error("Error from API: body=%s", raw_result)
                    raise ApiError()

                asset_info: dict = await response.json()

                return asset_info
        except aiohttp.ClientError as exception:
            _LOGGER.error("Error connecting to the API: %s", exception)
            raise CannotConnect from exception

    async def download_asset(self, asset_id: str) -> bytes | None:
        """Download the asset."""
        try:
            session = await self._get_session()
            url = urljoin(self.host, f"/api/assets/{asset_id}/original")
            headers = {_HEADER_API_KEY: self.api_key}

            async with session.get(url=url, headers=headers) as response:
                if response.status != 200:
                    _LOGGER.error("Error from API: status=%d", response.status)
                    return None

                if response.content_type not in _ALLOWED_MIME_TYPES:
                    _LOGGER.error(
                        "MIME type is not supported: %s", response.content_type
                    )
                    return None

                return await response.read()
        except aiohttp.ClientError as exception:
            _LOGGER.error("Error connecting to the API: %s", exception)
            raise CannotConnect from exception

    async def list_favorite_images(self) -> list[dict]:
        """List all favorite images."""
        try:
            session = await self._get_session()
            url = urljoin(self.host, "/api/search/metadata")

            async with session.post(
                url=url,
                headers=self._headers,
                json={"isFavorite": True, "type": "IMAGE"},
            ) as response:
                if response.status != 200:
                    raw_result = await response.text()
                    _LOGGER.error("Error from API: body=%s", raw_result)
                    raise ApiError()

                favorites = await response.json()
                assets: list[dict] = favorites["assets"]["items"]

                return assets
        except aiohttp.ClientError as exception:
            _LOGGER.error("Error connecting to the API: %s", exception)
            raise CannotConnect from exception

    async def list_all_albums(self) -> list[dict]:
        """List all albums."""
        try:
            session = await self._get_session()
            url = urljoin(self.host, "/api/albums")

            async with session.get(url=url, headers=self._headers) as response:
                if response.status != 200:
                    raw_result = await response.text()
                    _LOGGER.error("Error from API: body=%s", raw_result)
                    raise ApiError()

                album_list: list[dict] = await response.json()

                return album_list
        except aiohttp.ClientError as exception:
            _LOGGER.error("Error connecting to the API: %s", exception)
            raise CannotConnect from exception

    async def list_album_images(self, album_id: str) -> list[dict]:
        """List all images in an album."""
        try:
            session = await self._get_session()
            url = urljoin(self.host, f"/api/albums/{album_id}")

            async with session.get(url=url, headers=self._headers) as response:
                if response.status != 200:
                    raw_result = await response.text()
                    _LOGGER.error("Error from API: body=%s", raw_result)
                    raise ApiError()

                album_info: dict = await response.json()
                assets: list[dict] = album_info["assets"]

                filtered_assets: list[dict] = [
                    asset for asset in assets if asset["type"] == "IMAGE"
                ]

                return filtered_assets
        except aiohttp.ClientError as exception:
            _LOGGER.error("Error connecting to the API: %s", exception)
            raise CannotConnect from exception


class CannotConnect(HomeAssistantError):
    """Error to indicate we cannot connect."""


class InvalidAuth(HomeAssistantError):
    """Error to indicate there is invalid auth."""


class ApiError(HomeAssistantError):
    """Error to indicate that the API returned an error."""

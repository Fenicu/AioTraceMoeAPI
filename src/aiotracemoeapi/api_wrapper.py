import asyncio
import io
import os
from typing import Any, Union
from urllib.parse import urljoin

import httpx

from . import exceptions as errors
from .types import AnimeResponse, BotMe, RateLimit

LIMIT_HEADERS = ["x-ratelimit-limit", "x-ratelimit-remaining", "x-ratelimit-reset"]


class TraceMoe:
    """Async wrapper for Trace.moe API."""

    def __init__(self, token: str | None = None, timeout: float = 60.0) -> None:
        """
        Initialize the TraceMoe client.

        :param token: API Key from https://trace.moe/account (Developer's Zone)
        :param timeout: Request timeout in seconds
        """
        self.api_url = "https://api.trace.moe"
        self.headers: dict[str, str] = {}
        self.timeout = timeout
        if token is not None:
            self.headers["x-trace-key"] = token
        self._session: httpx.AsyncClient | None = None

    async def __aenter__(self) -> "TraceMoe":
        self._session = httpx.AsyncClient(headers=self.headers, timeout=self.timeout)
        return self

    async def __aexit__(self, exc_type: Any, exc_val: Any, exc_tb: Any) -> None:
        await self.close()

    async def close(self) -> None:
        """Close the client session."""
        if self._session and not self._session.is_closed:
            await self._session.aclose()
            self._session = None

    def _process_response(self, response: httpx.Response, url: str) -> tuple[dict[str, Any], RateLimit]:
        """Process the response from the API."""
        limit_data = {
            key.lower(): value
            for key, value in response.headers.items()
            if key.lower() in LIMIT_HEADERS
        }

        # Ensure required fields are present
        if "x-ratelimit-limit" not in limit_data:
            limit_data["x-ratelimit-limit"] = 0
        if "x-ratelimit-remaining" not in limit_data:
            limit_data["x-ratelimit-remaining"] = 0
        if "x-ratelimit-reset" not in limit_data:
            limit_data["x-ratelimit-reset"] = 0

        limit = RateLimit(**limit_data)

        if response.status_code == 200:
            return response.json(), limit

        error_cls = errors.ERRORS_STATUS_MAPPING.get(response.status_code, errors.TraceMoeAPIError)

        try:
            resp_json = response.json()
            error_text = resp_json.get("error", response.text)
        except Exception:
            error_text = response.text

        raise error_cls(url=url, text=f"{error_text} (Status: {response.status_code})", raw_response=response)

    async def make_request(
        self,
        method: str,
        url: str,
        params: dict[str, Any] | None = None,
        data: dict[str, Any] | None = None,
        files: dict[str, Any] | None = None,
    ) -> tuple[dict[str, Any], RateLimit]:
        """
        Make an HTTP request to the API.

        :param method: HTTP method (GET, POST)
        :param url: URL to request
        :param params: Query parameters
        :param data: Form data
        :param files: Files to upload
        :return: Tuple of (response_json, limit_headers)
        :raises TraceMoeAPIError: If the request fails
        """
        if self._session and not self._session.is_closed:
            response = await self._session.request(method, url, params=params, data=data, files=files)
            return self._process_response(response, url)

        async with httpx.AsyncClient(headers=self.headers, timeout=self.timeout) as client:
            response = await client.request(method, url, params=params, data=data, files=files)
            return self._process_response(response, url)

    async def me(self) -> BotMe:
        """
        Check the search quota and limit for your account.

        :return: BotMe object containing quota and limit info
        """
        url = urljoin(self.api_url, "me")
        response, limit = await self.make_request("GET", url)
        return await self._to_me_object(response, limit)

    async def search(
        self,
        path: Union[str, io.BytesIO],
        ani_list_id: int = 0,
        cut_borders: bool = True,
        anilist_info: bool = True,
        is_url: bool = False,
    ) -> AnimeResponse:
        """
        Search for an anime scene.

        :param path: URL string or file-like object (BytesIO) or file path
        :param ani_list_id: Filter by Anilist ID
        :param cut_borders: Cut black borders (default: True)
        :param anilist_info: Include Anilist info (default: True)
        :param is_url: Set to True if path is a URL
        :return: AnimeResponse object
        """
        url = urljoin(self.api_url, "search")
        params: dict[str, Any] = {}

        if ani_list_id:
            params["anilistID"] = ani_list_id
        if cut_borders:
            params["cutBorders"] = ""
        if anilist_info:
            params["anilistInfo"] = ""

        if is_url:
            if not isinstance(path, str):
                raise AttributeError(f"path must be str(url), not {type(path).__name__}")

            params["url"] = path
            response, limit = await self.make_request("GET", url, params=params)

        elif isinstance(path, io.BytesIO):
            files = {"image": path}
            response, limit = await self.make_request("POST", url, params=params, files=files)

        elif isinstance(path, str) and os.path.isfile(path):

            def _read_file() -> bytes:
                with open(path, "rb") as f:
                    return f.read()

            content = await asyncio.to_thread(_read_file)
            files = {"image": (os.path.basename(path), content)}
            response, limit = await self.make_request("POST", url, params=params, files=files)
        else:
            raise AttributeError("path must be a valid URL string, file path, or io.BytesIO object")

        return await self._to_search_object(response, limit, url)

    async def _to_search_object(self, response_json: dict[str, Any], limit: RateLimit, url: str) -> AnimeResponse:
        """Convert response JSON to AnimeResponse object and handle API-specific errors."""
        anime = AnimeResponse(**response_json, limits=limit)

        if anime.error:
            kwargs = {
                "url": url,
                "text": anime.error,
                "anime_response_object": anime,
            }
            if anime.error == "Invalid API key":
                raise errors.InvalidAPIKey(**kwargs)
            if anime.error == "Search quota depleted":
                raise errors.SearchQuotaDepleted(**kwargs)
            if anime.error == "Concurrency limit exceeded":
                raise errors.ConcurrencyLimitExceeded(**kwargs)
            if anime.error == "Error: Search queue is full":
                raise errors.SearchQueueFull(**kwargs)
            if anime.error == "Invalid image url":
                raise errors.InvalidImageUrl(**kwargs)
            if "Failed to fetch image" in anime.error:
                raise errors.FailedFetchImage(**kwargs)
            if anime.error == "Failed to process image":
                raise errors.FailedProcessImage(**kwargs)
            if anime.error == "OpenCV: Failed to detect and cut borders":
                raise errors.FailedDetectAndCutBorders(**kwargs)

            raise errors.TraceMoeAPIError(**kwargs)

        return anime

    async def _to_me_object(self, response_json: dict[str, Any], limit: RateLimit) -> BotMe:
        """Convert response JSON to BotMe object."""
        return BotMe(**response_json, limits=limit)

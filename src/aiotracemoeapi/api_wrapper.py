import io
import os
from typing import Any, Dict, Optional, Tuple, Union
from urllib.parse import urljoin

import httpx

from . import exceptions as errors
from .types import AnimeResponse, BotMe

LIMIT_HEADERS = ["x-ratelimit-limit", "x-ratelimit-remaining", "x-ratelimit-reset"]


class TraceMoe:
    """Async wrapper for Trace.moe API."""

    def __init__(self, token: Optional[str] = None, timeout: float = 60.0) -> None:
        """
        Initialize the TraceMoe client.

        :param token: API Key from https://trace.moe/account (Developer's Zone)
        :param timeout: Request timeout in seconds
        """
        self.api_url = "https://api.trace.moe"
        self.headers: Dict[str, str] = {}
        self.timeout = timeout
        if token is not None:
            self.headers["x-trace-key"] = token

    async def make_request(
        self,
        method: str,
        url: str,
        params: Optional[Dict[str, Any]] = None,
        data: Optional[Dict[str, Any]] = None,
        files: Optional[Dict[str, Any]] = None,
    ) -> Tuple[Dict[str, Any], Dict[str, Any]]:
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
        async with httpx.AsyncClient(headers=self.headers, timeout=self.timeout) as client:
            response = await client.request(method, url, params=params, data=data, files=files)

            limit = {
                key.lower(): value
                for key, value in response.headers.items()
                if key.lower() in LIMIT_HEADERS
            }

            if response.status_code == 200:
                return response.json(), limit

            error_cls = errors.ERRORS_STATUS_MAPPING.get(response.status_code, errors.TraceMoeAPIError)

            try:
                resp_json = response.json()
                error_text = resp_json.get("error", response.text)
            except Exception:
                error_text = response.text

            raise error_cls(url=url, text=f"{error_text} (Status: {response.status_code})", raw_response=response)

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
        params: Dict[str, Any] = {}

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
            with open(path, "rb") as file:
                files = {"image": file}
                response, limit = await self.make_request("POST", url, params=params, files=files)
        else:
            raise AttributeError("path must be a valid URL string, file path, or io.BytesIO object")

        return await self._to_search_object(response, limit, url)

    async def _to_search_object(self, response_json: Dict[str, Any], limit: Dict[str, Any], url: str) -> AnimeResponse:
        """Convert response JSON to AnimeResponse object and handle API-specific errors."""
        response_json["limits"] = limit
        anime = AnimeResponse(**response_json)

        if anime.error:
            kwargs = dict(
                url=url,
                text=anime.error,
                anime_response_object=anime,
            )
            if anime.error == "Invalid API key":
                raise errors.InvalidAPIKey(**kwargs)
            elif anime.error == "Search quota depleted":
                raise errors.SearchQuotaDepleted(**kwargs)
            elif anime.error == "Concurrency limit exceeded":
                raise errors.ConcurrencyLimitExceeded(**kwargs)
            elif anime.error == "Error: Search queue is full":
                raise errors.SearchQueueFull(**kwargs)
            elif anime.error == "Invalid image url":
                raise errors.InvalidImageUrl(**kwargs)
            elif "Failed to fetch image" in anime.error:
                raise errors.FailedFetchImage(**kwargs)
            elif anime.error == "Failed to process image":
                raise errors.FailedProcessImage(**kwargs)
            elif anime.error == "OpenCV: Failed to detect and cut borders":
                raise errors.FailedDetectAndCutBorders(**kwargs)

            raise errors.TraceMoeAPIError(**kwargs)

        return anime

    async def _to_me_object(self, response_json: Dict[str, Any], limit: Dict[str, Any]) -> BotMe:
        """Convert response JSON to BotMe object."""
        response_json["limits"] = limit
        return BotMe(**response_json)

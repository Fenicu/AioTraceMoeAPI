from __future__ import annotations

import asyncio
import os
from collections.abc import Sequence
from pathlib import Path
from types import TracebackType
from typing import IO, Any
from urllib.parse import urlparse

import httpx

from . import exceptions as errors
from .types import AnimeBatchResponse, AnimeResponse, BotMe, CutBorders, RateLimit, UsagePeriod, UsageStats

DEFAULT_API_URL = "https://api.trace.moe"

SearchSource = str | bytes | bytearray | memoryview | os.PathLike[str] | IO[bytes]
Vector = str | Sequence[float]


def _read_file(path: Path) -> bytes:
    if not path.is_file():
        raise FileNotFoundError(f"File not found: {path}")
    return path.read_bytes()


class TraceMoe:
    """Async wrapper for Trace.moe API."""

    def __init__(
        self,
        token: str | None = None,
        *,
        timeout: float = 60.0,
        base_url: str = DEFAULT_API_URL,
        client: httpx.AsyncClient | None = None,
        max_retries: int = 0,
        retry_delay: float = 1.0,
    ) -> None:
        """
        Initialize the TraceMoe client.

        :param token: API Key from https://trace.moe/account, sent in the ``x-trace-key`` header
        :param timeout: Request timeout in seconds
        :param base_url: API URL, change it to use a self-hosted trace.moe server
        :param client: Your own ``httpx.AsyncClient``; it will not be closed by this wrapper
        :param max_retries: How many times to retry on concurrency limit, rate limit, full queue or overload errors
        :param retry_delay: Base delay between retries in seconds, doubled after every attempt
        """
        self.base_url = base_url.rstrip("/")
        self.headers: dict[str, str] = {}
        if token is not None:
            self.headers["x-trace-key"] = token
        self.timeout = timeout
        self.max_retries = max_retries
        self.retry_delay = retry_delay
        self._session: httpx.AsyncClient | None = client
        self._owns_session = client is None
        self._context_depth = 0

    def _check_external_client(self) -> None:
        if not self._owns_session and self._session is not None and self._session.is_closed:
            raise RuntimeError("The httpx.AsyncClient passed as `client` is closed")

    async def __aenter__(self) -> TraceMoe:
        self._check_external_client()
        if self._session is None or self._session.is_closed:
            self._session = httpx.AsyncClient(timeout=self.timeout)
            self._owns_session = True
        self._context_depth += 1
        return self

    async def __aexit__(
        self,
        exc_type: type[BaseException] | None,
        exc_val: BaseException | None,
        exc_tb: TracebackType | None,
    ) -> None:
        self._context_depth = max(self._context_depth - 1, 0)
        if self._context_depth == 0:
            await self.close()

    async def close(self) -> None:
        """Close the client session if it was created by this wrapper."""
        if self._session is not None and self._owns_session:
            await self._session.aclose()
            self._session = None

    def _url(self, endpoint: str) -> str:
        return f"{self.base_url}/{endpoint.lstrip('/')}"

    def _process_response(self, response: httpx.Response, url: str) -> tuple[Any, RateLimit]:
        """Process the response from the API and raise an exception on error."""
        limit = RateLimit.from_headers(response.headers)

        try:
            data = response.json()
        except ValueError:
            data = None

        error_text = data.get("error") if isinstance(data, dict) else None

        if response.status_code == 200 and not error_text:
            return data, limit

        if not error_text:
            error_text = response.text or response.reason_phrase
        error_cls = errors.get_error_class(response.status_code, error_text)
        raise error_cls(
            url=url,
            text=error_text,
            raw_response=response,
            status_code=response.status_code,
            data=data if isinstance(data, dict) else None,
        )

    async def _send(self, method: str, url: str, **kwargs: Any) -> httpx.Response:
        self._check_external_client()
        if self._session is not None and not self._session.is_closed:
            return await self._session.request(method, url, headers=self.headers, **kwargs)

        async with httpx.AsyncClient(timeout=self.timeout) as client:
            return await client.request(method, url, headers=self.headers, **kwargs)

    async def make_request(
        self,
        method: str,
        url: str,
        params: dict[str, Any] | None = None,
        files: dict[str, Any] | None = None,
        json: Any = None,
    ) -> tuple[Any, RateLimit]:
        """
        Make an HTTP request to the API, retrying on temporary errors if ``max_retries`` is set.

        :param method: HTTP method (GET, POST)
        :param url: URL to request
        :param params: Query parameters
        :param files: Files to upload
        :param json: JSON body
        :return: Tuple of (response_json, rate_limit)
        :raises TraceMoeAPIError: If the request fails
        """
        attempt = 0
        while True:
            response = await self._send(method, url, params=params, files=files, json=json)
            try:
                return self._process_response(response, url)
            except errors.TraceMoeAPIError as exc:
                if attempt >= self.max_retries or not errors.is_retryable(exc):
                    raise
                delay = self.retry_delay * 2**attempt
                if isinstance(exc, errors.TooManyRequests) and exc.retry_after is not None:
                    delay = max(delay, exc.retry_after)
                attempt += 1
                await asyncio.sleep(delay)

    async def me(self) -> BotMe:
        """
        Check the search quota and limits for your account (or IP address without an API key).

        :return: BotMe object containing quota and limit info
        """
        response, limit = await self.make_request("GET", self._url("me"))
        return BotMe.model_validate({**response, "limits": limit})

    async def usage(self, period: UsagePeriod = "hour") -> list[UsageStats]:
        """
        Get your search history broken down by time period.

        :param period: ``minute`` (past 60 minutes), ``hour`` (past 72 hours) or ``day`` (past 60 days)
        :return: List of UsageStats objects
        """
        response, _ = await self.make_request("GET", self._url("me"), params={"period": period})
        return [UsageStats.model_validate(item) for item in response]

    @staticmethod
    def _search_params(
        anilist_id: int | None,
        anilist_info: bool,
        cut_borders: bool | int | None = None,
    ) -> dict[str, Any]:
        params: dict[str, Any] = {}
        if anilist_id:
            params["anilistID"] = anilist_id
        if anilist_info:
            params["anilistInfo"] = ""
        if cut_borders is not None:
            mode = CutBorders(int(cut_borders))
            if mode is not CutBorders.NONE:
                params["cutBorders"] = int(mode)
        return params

    @staticmethod
    def _looks_like_url(source: str) -> bool:
        return urlparse(source).scheme in ("http", "https")

    @staticmethod
    async def _read_source(source: SearchSource) -> tuple[str, bytes]:
        """Read an upload source into (filename, content)."""
        if isinstance(source, (bytes, bytearray, memoryview)):
            return "image", bytes(source)

        if isinstance(source, (str, os.PathLike)):
            path = Path(source)
            return path.name, await asyncio.to_thread(_read_file, path)

        if hasattr(source, "read"):
            content = await asyncio.to_thread(source.read)
            if not isinstance(content, bytes):
                raise TypeError("file-like object must be opened in binary mode")
            name = getattr(source, "name", None)
            return (os.path.basename(name) if isinstance(name, str) else "image"), content

        raise TypeError(f"Unsupported search source type: {type(source).__name__}")

    async def search(
        self,
        source: SearchSource,
        *,
        anilist_id: int | None = None,
        cut_borders: bool | CutBorders = True,
        anilist_info: bool = True,
        is_url: bool | None = None,
    ) -> AnimeResponse:
        """
        Search for an anime scene by image (or the 1st frame of a video / gif).

        :param source: Image URL, file path, ``bytes`` or a binary file-like object
        :param anilist_id: Search only within this AniList ID
        :param cut_borders: Cut black borders: ``True``/``CutBorders.CUT``, ``False``/``CutBorders.NONE``
            or ``CutBorders.BOTH`` to search with both images (may cost 2 search credits)
        :param anilist_info: Include AniList info in results instead of a bare ID
        :param is_url: Force treating a string ``source`` as URL (``True``) or file path (``False``);
            by default strings starting with ``http://`` or ``https://`` are treated as URLs
        :return: AnimeResponse object
        """
        url = self._url("search")
        params = self._search_params(anilist_id, anilist_info, cut_borders)

        if is_url and not isinstance(source, str):
            raise TypeError(f"source must be a URL string when is_url=True, not {type(source).__name__}")

        if isinstance(source, str) and (is_url or (is_url is None and self._looks_like_url(source))):
            params["url"] = source
            response, limit = await self.make_request("GET", url, params=params)
        else:
            filename, content = await self._read_source(source)
            files = {"image": (filename, content)}
            response, limit = await self.make_request("POST", url, params=params, files=files)

        return AnimeResponse.model_validate({**response, "limits": limit})

    async def search_vector(
        self,
        vector: Vector,
        *,
        anilist_id: int | None = None,
        anilist_info: bool = True,
    ) -> AnimeResponse:
        """
        Search by a 33-dimensional MPEG-7 ColorLayout vector (see https://github.com/soruly/trace.moe-id).

        :param vector: Base64 hash string or a sequence of 33 numbers
        :param anilist_id: Search only within this AniList ID
        :param anilist_info: Include AniList info in results instead of a bare ID
        :return: AnimeResponse object
        """
        params = self._search_params(anilist_id, anilist_info)
        body = {"vector": vector if isinstance(vector, str) else list(vector)}
        response, limit = await self.make_request("POST", self._url("search"), params=params, json=body)
        return AnimeResponse.model_validate({**response, "limits": limit})

    async def search_vectors(
        self,
        vectors: Sequence[Vector],
        *,
        anilist_id: int | None = None,
        anilist_info: bool = True,
    ) -> AnimeBatchResponse:
        """
        Batch search by up to 10 ColorLayout vectors, each one costs 1 search credit.

        :param vectors: Base64 hash strings or sequences of 33 numbers
        :param anilist_id: Search only within this AniList ID
        :param anilist_info: Include AniList info in results instead of a bare ID
        :return: AnimeBatchResponse object with one result list per vector, in the same order
        """
        if isinstance(vectors, str) or not vectors:
            raise ValueError("vectors must be a non-empty sequence of vectors")

        params = self._search_params(anilist_id, anilist_info)
        body = {"vector": [vector if isinstance(vector, str) else list(vector) for vector in vectors]}
        response, limit = await self.make_request("POST", self._url("search"), params=params, json=body)
        return AnimeBatchResponse.model_validate({**response, "limits": limit})

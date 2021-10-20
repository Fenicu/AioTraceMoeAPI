import io
from typing import Optional, Union
from urllib.parse import quote_plus, urljoin

import aiohttp
from aiohttp.client_reqrep import ClientResponse

from . import exceptions as errors
from .types import AnimeResponse, BotMe

# API reference https://soruly.github.io/trace.moe-api/#/

LIMIT_HEADERS = ["X-RateLimit-Limit", "X-RateLimit-Remaining", "X-RateLimit-Reset"]


class TraceMoe:
    def __init__(self, token: Optional[str] = None, timeout: float = 60):
        """
        :param token: API Key from https://trace.moe/account (Developer's Zone)
        :type token: :obj:`str`
        :type timeout: :obj:`float`
        """
        self.api_url = "https://api.trace.moe"
        self.headers = None
        self.timeout = aiohttp.ClientTimeout(total=timeout)
        if token is not None:
            self.headers = {"x-trace-key": token}

    async def make_request(
        self, url: str, params: Optional[dict] = None, data: Optional[dict] = None
    ) -> ClientResponse:
        async with aiohttp.ClientSession(headers=self.headers) as session:
            async with session.request(
                "POST" if data else "GET", url, params=params, data=data, timeout=self.timeout
            ) as response:
                status = response.status
                if status == 200:
                    return response
                if status in errors.ERRORS_STATUS_MAPPING:
                    _error: errors.TraceMoeAPIError = errors.ERRORS_STATUS_MAPPING[status]
                    error = _error(url, text=f"status code: {status}", raw_response=response)
                else:
                    error = errors.TraceMoeAPIError(
                        url, text=f"status code: {status}", raw_response=response
                    )
                raise error

    async def me(self) -> BotMe:
        url = urljoin(self.api_url, "me")
        response = await self.make_request(url)
        _bot_me = await self._to_me_object(response)
        return _bot_me

    async def search(
        self,
        path: Union[str, io.BytesIO],
        ani_list_id: int = 0,
        cut_borders: int = 1,
        anilist_info: int = 1,
        is_url: bool = False,
    ) -> AnimeResponse:
        """
        Use this method to search anime.

        Source: https://soruly.github.io/trace.moe-api/#/docs?id=search

        :param path: path, url or BytesIO to send
        :type path: :obj:`typing.Union[str, io.BytesIO]`

        :param ani_list_id: You can search for a matching scene only in a particular anime by Anilist ID.
            This is useful when you are certain about the anime name but cannot remember which episode.
        :type ani_list_id: :obj:`typing.Optional[int]`

        :param cut_borders: trace.moe can detect black borders automatically and cut away unnecessary
            parts of the images that would affect search results accuracy.
            This is useful if your image is a screencap from a smartphone or iPad that contains black bars.
        :type cut_borders: :obj:`typing.Optional[int]`

        :param anilist_info: Asking for Anilist info would slow down your request because it takes additional query to Anilist,
            and may fail depending on their availability.
        :type anilist_info: :obj:`typing.Optional[int]`

        :param is_url: Is path a link to an image.
        :type is_url: :obj:`typing.Optional[bool]`

        :rtype: :obj:`types.AnimeResponse`
        """
        url = urljoin(self.api_url, "search")
        params = {
            "anilistID": ani_list_id,
            "cutBorders": cut_borders,
            "anilistInfo": anilist_info,
        }
        if is_url:
            if not isinstance(path, str):
                raise AttributeError("path must be str(url), not " f"{type(path).__name__}")

            params["url"] = quote_plus(path)
            response = await self.make_request(url, params)

        elif isinstance(path, io.BytesIO):
            data = {"image": path}
            response = await self.make_request(url, params, data)

        else:
            with open(path, "rb") as file:
                data = {"image": file}
                response = await self.make_request(url, params, data)

        return await self._to_search_object(response)

    async def _to_search_object(self, response_api: ClientResponse) -> AnimeResponse:
        try:
            response_json = await response_api.json()
        except Exception as error:
            raise error
        response_json["limits"] = {
            key: value for key, value in response_api.headers.items() if key in LIMIT_HEADERS
        }
        anime = AnimeResponse(**response_json)
        if anime.error is not None:
            kwargs = dict(
                url=response_api.url,
                text=anime.error,
                raw_response=response_api,
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

    async def _to_me_object(self, response_api: ClientResponse) -> BotMe:
        response_json = await response_api.json()
        response_json["limits"] = {
            key: value for key, value in response_api.headers.items() if key in LIMIT_HEADERS
        }
        return BotMe(**response_json)

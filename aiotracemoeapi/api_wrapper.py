import io
from json import loads
from urllib.parse import urljoin, quote_plus
from typing import Optional, Union

import aiohttp
from .types import AnimeResponse, AnimeSearch, BotMe, AniList

# API reference https://soruly.github.io/trace.moe-api/#/


class TraceMoe:

    def __init__(self, token: Optional[str] = None):
        """
        :param token: API Key from https://trace.moe/account (Developer's Zone)
        :type token: :obj:`str`
        """
        self.api_url = "https://api.trace.moe"
        self.headers = None
        if token is not None:
            self.headers = {"x-trace-key": token}

    async def me(self) -> BotMe:
        url = urljoin(self.api_url, "me")

        async with aiohttp.ClientSession(headers=self.headers) as session:
            async with session.get(url) as resp:
                r = await resp.json()
                r["quota_used"] = r["quotaUsed"]
                del r["quotaUsed"]
                return BotMe(r)

    async def search(self, path: Union[str, io.BytesIO],
                     ani_list_id: Optional[int] = 0,
                     cut_borders: Optional[int] = 1,
                     anilist_info: Optional[int] = 1,
                     is_url: bool = False
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
        if is_url:
            if not isinstance(path, str):
                raise AttributeError("path must be str(url), not "
                                     f"{type(path).__name__}")

            async with aiohttp.ClientSession(headers=self.headers) as session:
                async with session.get(url,
                                       params={
                                           "url": quote_plus(path),
                                           "anilistID": ani_list_id,
                                           "cutBorders": cut_borders,
                                           "anilistInfo": anilist_info}) as resp:
                    try:
                        prepare_response = await resp.text()
                        response = loads(prepare_response)
                    except Exception as error:
                        raise error
                    if response == "Error: Search queue is full":
                        raise Exception(response)
                    elif "error" in response:
                        if response["error"] != str():
                            raise Exception(response["error"])
                    for idx, _anime in enumerate(response["result"]):
                        _anime["afrom"] = _anime["from"]
                        del _anime["from"]
                        search = AnimeSearch(_anime)
                        if isinstance(search.anilist, dict):
                            _anime["anilist"]["id_mal"] = _anime["anilist"]["idMal"]
                            _anime["anilist"]["is_adult"] = _anime["anilist"]["isAdult"]
                            del _anime["anilist"]["isAdult"]
                            del _anime["anilist"]["idMal"]
                            search.anilist = AniList(_anime["anilist"])
                        response["result"][idx] = search
                    response["frame_count"] = response["frameCount"]
                    return AnimeResponse(response)

        elif isinstance(path, io.BytesIO):
            async with aiohttp.ClientSession(headers=self.headers) as session:
                async with session.post(url,
                                        params={
                                            "anilistID": ani_list_id,
                                            "cutBorders": cut_borders,
                                            "anilistInfo": anilist_info},
                                        data={
                                            "image": path}) as resp:
                    try:
                        prepare_response = await resp.text()
                        response = loads(prepare_response)
                    except Exception as error:
                        raise error
                    if response == "Error: Search queue is full":
                        raise Exception(response)
                    elif "error" in response:
                        if response["error"] != str():
                            raise Exception(response["error"])
                    for idx, _anime in enumerate(response["result"]):
                        _anime["afrom"] = _anime["from"]
                        del _anime["from"]
                        search = AnimeSearch(_anime)
                        if isinstance(search.anilist, dict):
                            _anime["anilist"]["id_mal"] = _anime["anilist"]["idMal"]
                            _anime["anilist"]["is_adult"] = _anime["anilist"]["isAdult"]
                            del _anime["anilist"]["isAdult"]
                            del _anime["anilist"]["idMal"]
                            search.anilist = AniList(_anime["anilist"])
                        response["result"][idx] = search
                    response["frame_count"] = response["frameCount"]
                    return AnimeResponse(response)

        else:
            with open(path, "rb") as file:
                async with aiohttp.ClientSession(headers=self.headers) as session:
                    async with session.post(url,
                                            params={
                                                "anilistID": ani_list_id,
                                                "cutBorders": cut_borders,
                                                "anilistInfo": anilist_info},
                                            data={
                                                "image": file}) as resp:
                        try:
                            prepare_response = await resp.text()
                            response = loads(prepare_response)
                        except Exception as error:
                            raise error
                        if response == "Error: Search queue is full":
                            raise Exception(response)
                        elif "error" in response:
                            if response["error"] != str():
                                raise Exception(response["error"])
                        for idx, _anime in enumerate(response["result"]):
                            _anime["afrom"] = _anime["from"]
                            del _anime["from"]
                            search = AnimeSearch(_anime)
                            if isinstance(search.anilist, dict):
                                _anime["anilist"]["id_mal"] = _anime["anilist"]["idMal"]
                                _anime["anilist"]["is_adult"] = _anime["anilist"]["isAdult"]
                                del _anime["anilist"]["isAdult"]
                                del _anime["anilist"]["idMal"]
                                search.anilist = AniList(_anime["anilist"])
                            response["result"][idx] = search
                        response["frame_count"] = response["frameCount"]
                        return AnimeResponse(response)

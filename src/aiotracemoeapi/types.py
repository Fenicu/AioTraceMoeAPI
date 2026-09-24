from __future__ import annotations

from datetime import datetime, timedelta, timezone
from enum import IntEnum
from typing import Any, Literal

import httpx
from pydantic import BaseModel, ConfigDict, Field, model_validator

from .utils import clamp

PreviewSize = Literal["s", "m", "l"]
UsagePeriod = Literal["minute", "hour", "day"]
Episode = int | float | str | list[int | float | str]


class CutBorders(IntEnum):
    """Modes of the ``cutBorders`` search parameter."""

    #: Search with the original image only
    NONE = 0
    #: Search with the image with black borders cut
    CUT = 1
    #: Search with both the original and the cut image, results are merged (may cost 2 search credits)
    BOTH = 2


class RateLimit(BaseModel):
    """HTTP rate limit information from response headers."""

    limit: int = Field(default=0, alias="x-ratelimit-limit")
    remaining: int = Field(default=0, alias="x-ratelimit-remaining")
    reset: int = Field(default=0, alias="x-ratelimit-reset")

    model_config = ConfigDict(populate_by_name=True)

    @classmethod
    def from_headers(cls, headers: httpx.Headers) -> RateLimit:
        """Build from ``X-RateLimit-*`` headers, falling back to the standard ``RateLimit-*`` ones."""

        def _int(value: str | None) -> int | None:
            try:
                return int(float(value)) if value is not None else None
            except ValueError:
                return None

        limit = _int(headers.get("x-ratelimit-limit"))
        if limit is None:
            limit = _int(headers.get("ratelimit-limit"))

        remaining = _int(headers.get("x-ratelimit-remaining"))
        if remaining is None:
            remaining = _int(headers.get("ratelimit-remaining"))

        reset = _int(headers.get("x-ratelimit-reset"))
        if reset is None:
            # Standard header holds seconds until reset instead of a unix timestamp
            seconds = _int(headers.get("ratelimit-reset"))
            if seconds is not None:
                reset = int(datetime.now(timezone.utc).timestamp()) + seconds

        return cls(limit=limit or 0, remaining=remaining or 0, reset=reset or 0)

    @property
    def reset_datetime(self) -> datetime:
        """Return the reset time as a timezone-aware (UTC) datetime."""
        return datetime.fromtimestamp(self.reset, tz=timezone.utc)

    @property
    def reset_timedelta(self) -> timedelta:
        """Return the time left until reset."""
        return self.reset_datetime - datetime.now(timezone.utc)


class BotMe(BaseModel):
    """Response model for the /me endpoint."""

    id: str
    priority: int
    concurrency: int
    quota: int
    quota_used: int = Field(alias="quotaUsed")
    limits: RateLimit | None = None

    model_config = ConfigDict(populate_by_name=True)

    @property
    def quota_left(self) -> int:
        """Return the quota left for the rolling 24-hour window."""
        return max(self.quota - self.quota_used, 0)


class UsageStats(BaseModel):
    """One time slot of the /me?period=... usage history."""

    time: datetime
    total: int = 0
    by_status: dict[int, int] = Field(default_factory=dict)

    @model_validator(mode="before")
    @classmethod
    def _collect_status_codes(cls, data: Any) -> Any:
        if not isinstance(data, dict) or "by_status" in data:
            return data
        by_status = {int(key): value for key, value in data.items() if str(key).isdigit()}
        return {"time": data.get("time"), "total": data.get("total", 0), "by_status": by_status}


class AnimeTitle(BaseModel):
    """Anime title in different languages."""

    native: str | None = None
    romaji: str | None = None
    english: str | None = None

    model_config = ConfigDict(extra="allow")


class AniList(BaseModel):
    """AniList information (unmodified AniList data, extra fields are kept)."""

    id: int
    id_mal: int | None = Field(default=None, alias="idMal")
    title: AnimeTitle = Field(default_factory=AnimeTitle)
    synonyms: list[str] = Field(default_factory=list)
    is_adult: bool = Field(default=False, alias="isAdult")

    model_config = ConfigDict(populate_by_name=True, extra="allow")

    @property
    def url(self) -> str:
        """Return the AniList URL."""
        return f"https://anilist.co/anime/{self.id}"

    @property
    def mal_url(self) -> str | None:
        """Return the MyAnimeList URL, if the MAL ID is known."""
        if self.id_mal is None:
            return None
        return f"https://myanimelist.net/anime/{self.id_mal}"


class AnimeSearch(BaseModel):
    """Search result item."""

    anilist: int | AniList
    filename: str
    episode: Episode | None = None
    episode_start: int | None = None
    episode_end: int | None = None
    duration: float | None = None
    anime_from: float = Field(alias="from")
    at: float | None = None
    anime_to: float = Field(alias="to")
    similarity: float
    video: str
    image: str

    model_config = ConfigDict(populate_by_name=True)

    @property
    def anilist_id(self) -> int:
        """Return the AniList ID regardless of whether AniList info was requested."""
        if isinstance(self.anilist, AniList):
            return self.anilist.id
        return self.anilist

    @property
    def anilist_info(self) -> AniList | None:
        """Return AniList info if it was requested with ``anilist_info=True``."""
        if isinstance(self.anilist, AniList):
            return self.anilist
        return None

    def short_similarity(self, formatting: str = "{:.1%}") -> str:
        """Return formatted similarity string."""
        return clamp(self.similarity, format=formatting) or ""

    def image_url(self, size: PreviewSize | None = None) -> str:
        """
        Return the preview image URL. The URL expires in 5 minutes.

        :param size: ``s`` (160px), ``m`` (320px, default) or ``l`` (640px)
        """
        params: dict[str, Any] = {}
        if size is not None:
            params["size"] = size
        return str(httpx.URL(self.image).copy_merge_params(params))

    def video_url(
        self,
        size: PreviewSize | None = None,
        mute: bool = False,
        min_duration: float | None = None,
        max_duration: float | None = None,
    ) -> str:
        """
        Return the preview video URL. The URL expires in 5 minutes.

        :param size: ``s`` (160px), ``m`` (320px, default) or ``l`` (640px)
        :param mute: Return a video without sound
        :param min_duration: Minimal scene duration, 0.5 to 2.0 seconds
        :param max_duration: Maximal scene duration, 0.5 to 5.0 seconds
        """
        params: dict[str, Any] = {}
        if size is not None:
            params["size"] = size
        if mute:
            params["mute"] = ""
        if min_duration is not None:
            params["minDuration"] = min_duration
        if max_duration is not None:
            params["maxDuration"] = max_duration
        return str(httpx.URL(self.video).copy_merge_params(params))


class AnimeResponse(BaseModel):
    """Response model for the /search endpoint."""

    frame_count: int | None = Field(default=None, alias="frameCount")
    quota: int | None = None
    quota_used: int | None = Field(default=None, alias="quotaUsed")
    error: str = ""
    result: list[AnimeSearch] = Field(default_factory=list)
    limits: RateLimit | None = None

    model_config = ConfigDict(populate_by_name=True)

    @property
    def best_result(self) -> AnimeSearch | None:
        """Return the best search result."""
        if self.result:
            return self.result[0]
        return None


class AnimeBatchResponse(BaseModel):
    """Response model for the batch vector search: one result list per input vector."""

    frame_count: int | None = Field(default=None, alias="frameCount")
    quota: int | None = None
    quota_used: int | None = Field(default=None, alias="quotaUsed")
    error: str = ""
    result: list[list[AnimeSearch]] = Field(default_factory=list)
    limits: RateLimit | None = None

    model_config = ConfigDict(populate_by_name=True)

    @property
    def best_results(self) -> list[AnimeSearch | None]:
        """Return the best search result for every input vector."""
        return [results[0] if results else None for results in self.result]

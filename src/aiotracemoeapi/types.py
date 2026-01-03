from datetime import datetime
from typing import Dict, List, Optional, Union

from pydantic import BaseModel, ConfigDict, Field, field_validator

from .utils import clamp


class RateLimit(BaseModel):
    """Rate limit information from headers."""

    limit: int = Field(alias="x-ratelimit-limit")
    remaining: int = Field(alias="x-ratelimit-remaining")
    reset: int = Field(alias="x-ratelimit-reset")

    model_config = ConfigDict(populate_by_name=True)

    @property
    def reset_datetime(self) -> datetime:
        """Return the reset time as a datetime object."""
        return datetime.fromtimestamp(self.reset)

    @property
    def reset_timedelta(self) -> datetime:
        """Return the time until reset."""
        return self.reset_datetime - datetime.now()


class BotMe(BaseModel):
    """Response model for /me endpoint."""

    id: str
    priority: int
    concurrency: int
    quota: int
    quota_used: int = Field(alias="quotaUsed")
    limits: Optional[RateLimit] = None

    model_config = ConfigDict(populate_by_name=True)


class AniList(BaseModel):
    """AniList information."""

    id: int
    id_mal: Optional[int] = Field(default=None, alias="idMal")
    title: Dict[str, Optional[str]]
    synonyms: List[str]
    is_adult: bool = Field(alias="isAdult")

    model_config = ConfigDict(populate_by_name=True)

    @property
    def mal_url(self) -> str:
        """Return the MyAnimeList URL."""
        return f"https://myanimelist.net/anime/{self.id_mal}"


class AnimeSearch(BaseModel):
    """Search result item."""

    anilist: Union[int, AniList]
    filename: str
    episode: Optional[Union[int, float, str, List[Union[int, float, str]]]] = None
    anime_from: float = Field(alias="from")
    anime_to: float = Field(alias="to")
    similarity: float
    video: str
    image: str

    model_config = ConfigDict(populate_by_name=True)

    def short_similarity(self, formatting: str = "{:.1%}", *args) -> str:
        """Return formatted similarity string."""
        return clamp(self.similarity, format=formatting, *args)


class AnimeResponse(BaseModel):
    """Response model for /search endpoint."""

    frame_count: Optional[int] = Field(default=None, alias="frameCount")
    error: Optional[str] = ""
    result: Optional[List[AnimeSearch]] = []
    limits: Optional[RateLimit] = None

    model_config = ConfigDict(populate_by_name=True)

    @field_validator("error")
    @classmethod
    def has_error(cls, error: str) -> str:
        """Validate error field."""
        if error:
            return error
        return ""

    @property
    def best_result(self) -> Optional[AnimeSearch]:
        """Return the best search result."""
        if self.result:
            return self.result[0]
        return None

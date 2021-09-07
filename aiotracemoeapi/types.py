from typing import Dict, List, Optional, Union
from datetime import datetime
from pydantic import BaseModel, Field, validator
from .utils import clamp


class RateLimit(BaseModel):
    limit: int = Field(alias="X-RateLimit-Limit")
    remaining: int = Field(alias="X-RateLimit-Remaining")
    reset: int = Field(alias="X-RateLimit-Reset")

    @property
    def reset_datetime(self):
        return datetime.fromtimestamp(self.reset)

    @property
    def reset_timedelta(self):
        return self.reset_datetime - datetime.now()


class BotMe(BaseModel):
    id: str
    priority: int
    concurrency: int
    quota: int
    quota_used: int = Field(alias="quotaUsed")
    limits: RateLimit


class AniList(BaseModel):
    id: int
    id_mal: Optional[int] = Field(alias="idMal")
    title: Dict[str, Optional[str]]
    synonyms: List[str]
    is_adult: bool = Field(alias="isAdult")

    @property
    def mal_url(self) -> str:
        return f"https://myanimelist.net/anime/{self.id_mal}"


class AnimeSearch(BaseModel):
    anilist: Union[int, AniList]
    filename: str
    episode: Union[int, str, None]
    anime_from: float = Field(alias="from")
    anime_to: float = Field(alias="to")
    similarity: float
    video: str
    image: str

    def short_similarity(self, formatting="{:.1%}", *args) -> str:
        return clamp(self.similarity, format=formatting, *args)


class AnimeResponse(BaseModel):
    frame_count: int = Field(alias="frameCount")
    error: Optional[str]
    result: List[AnimeSearch]
    limits: RateLimit

    @validator("error")
    def has_error(cls, error):
        if error != "":
            return error

    @property
    def best_result(self) -> AnimeSearch:
        return self.result[0]

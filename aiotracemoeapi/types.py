from typing import Dict, List, Union
from datetime import datetime


class RateLimit(dict):
    limit: int
    remaining: int
    reset: int

    def __init__(self, *args, **kwargs):
        super(RateLimit, self).__init__(*args, **kwargs)
        self.__dict__ = self

    @property
    def reset_datetime(self):
        return datetime.fromtimestamp(self.reset)

    @property
    def reset_timedelta(self):
        return self.reset_datetime - datetime.now()


class BotMe(dict):
    id: str
    priority: int
    concurrency: int
    quota: int
    quota_used: int
    limits: RateLimit

    def __init__(self, *args, **kwargs):
        super(BotMe, self).__init__(*args, **kwargs)
        self.__dict__ = self


class AniList(dict):
    id: int
    id_mal: int
    title: Dict[str, Union[str, None]]
    synonyms: List[str]
    is_adult: bool

    def __init__(self, *args, **kwargs):
        super(AniList, self).__init__(*args, **kwargs)
        self.__dict__ = self

    @property
    def mal_url(self) -> str:
        return f"https://myanimelist.net/anime/{self.id_mal}"


class AnimeSearch(dict):
    anilist: Union[int, AniList]
    filename: str
    episode: Union[int, None]
    afrom: float
    to: float
    similarity: float
    video: str
    image: str

    def __init__(self, *args, **kwargs):
        super(AnimeSearch, self).__init__(*args, **kwargs)
        self.__dict__ = self


class AnimeResponse(dict):
    frame_count: int
    error: str
    result: List[AnimeSearch]
    limits: RateLimit

    def __init__(self, *args, **kwargs):
        super(AnimeResponse, self).__init__(*args, **kwargs)
        self.__dict__ = self

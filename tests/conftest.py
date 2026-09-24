from __future__ import annotations

from typing import Any

import pytest

API = "https://api.trace.moe"

RATE_LIMIT_HEADERS = {
    "x-ratelimit-limit": "100",
    "x-ratelimit-remaining": "99",
    "x-ratelimit-reset": "1790248600",
}


def make_result(anilist: int | dict[str, Any] = 21034, similarity: float = 0.98) -> dict[str, Any]:
    return {
        "anilist": anilist,
        "filename": "Gochuumon wa Usagi Desuka 2 - 01 (BD 1280x720 x264 AAC).mp4",
        "episode": 1,
        "episode_start": 1,
        "episode_end": 1,
        "duration": 1422.0,
        "from": 288.0833,
        "at": 289.5,
        "to": 292.0833,
        "similarity": similarity,
        "video": f"{API}/video/abc",
        "image": f"{API}/image/abc",
    }


ANILIST_INFO = {
    "id": 21034,
    "idMal": 29787,
    "title": {"native": "ご注文はうさぎですか？？", "romaji": "Gochuumon wa Usagi desu ka??", "english": None},
    "synonyms": ["Gochiusa 2"],
    "isAdult": False,
}


@pytest.fixture
def search_response() -> dict[str, Any]:
    return {
        "quota": 100,
        "quotaUsed": 1,
        "frameCount": 745506,
        "error": "",
        "result": [make_result(ANILIST_INFO), make_result(ANILIST_INFO, similarity=0.8)],
    }

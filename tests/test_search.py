from __future__ import annotations

import io
import json
from pathlib import Path
from typing import Any

import httpx
import pytest
import respx

from aiotracemoeapi import AniList, AnimeSearch, CutBorders, TraceMoe

from .conftest import API, RATE_LIMIT_HEADERS, make_result


@respx.mock
async def test_search_by_url(search_response: dict[str, Any]) -> None:
    route = respx.get(f"{API}/search").respond(json=search_response, headers=RATE_LIMIT_HEADERS)

    response = await TraceMoe().search("https://example.com/image.jpg")

    params = route.calls.last.request.url.params
    assert params["url"] == "https://example.com/image.jpg"
    assert params["cutBorders"] == "1"
    assert "anilistInfo" in params
    assert "anilistID" not in params

    assert response.frame_count == 745506
    assert response.quota == 100
    assert response.quota_used == 1
    assert response.limits is not None
    assert response.limits.remaining == 99

    best = response.best_result
    assert best is not None
    assert best.at == 289.5
    assert best.duration == 1422.0
    assert best.episode_start == best.episode_end == 1
    assert best.anime_from == 288.0833
    assert best.anime_to == 292.0833
    assert isinstance(best.anilist, AniList)
    assert best.anilist_id == 21034
    assert best.anilist_info is best.anilist
    assert best.anilist.mal_url == "https://myanimelist.net/anime/29787"
    assert best.short_similarity() == "98.0%"


@respx.mock
async def test_search_is_url_true_is_still_supported(search_response: dict[str, Any]) -> None:
    route = respx.get(f"{API}/search").respond(json=search_response)
    await TraceMoe().search("https://example.com/image.jpg", is_url=True)
    assert route.called


async def test_search_is_url_requires_string() -> None:
    with pytest.raises(TypeError):
        await TraceMoe().search(b"data", is_url=True)


async def test_search_is_url_false_treats_string_as_path() -> None:
    with pytest.raises(FileNotFoundError):
        await TraceMoe().search("https://example.com/image.jpg", is_url=False)


async def test_search_missing_file() -> None:
    with pytest.raises(FileNotFoundError):
        await TraceMoe().search("does-not-exist.jpg")


async def test_search_unsupported_type() -> None:
    with pytest.raises(TypeError):
        await TraceMoe().search(123)  # type: ignore[arg-type]


@pytest.mark.parametrize(
    ("cut_borders", "expected"),
    [(True, "1"), (False, None), (CutBorders.NONE, None), (CutBorders.CUT, "1"), (CutBorders.BOTH, "2")],
)
@respx.mock
async def test_search_cut_borders(
    search_response: dict[str, Any], cut_borders: bool | CutBorders, expected: str | None
) -> None:
    route = respx.get(f"{API}/search").respond(json=search_response)
    await TraceMoe().search("https://example.com/a.jpg", cut_borders=cut_borders)
    assert route.calls.last.request.url.params.get("cutBorders") == expected


@respx.mock
async def test_search_filters(search_response: dict[str, Any]) -> None:
    search_response["result"] = [make_result()]
    route = respx.get(f"{API}/search").respond(json=search_response)

    response = await TraceMoe().search("https://example.com/a.jpg", anilist_id=21034, anilist_info=False)

    params = route.calls.last.request.url.params
    assert params["anilistID"] == "21034"
    assert "anilistInfo" not in params
    assert response.result[0].anilist == 21034
    assert response.result[0].anilist_info is None


@pytest.mark.parametrize(
    "make_source",
    [
        lambda path: path.read_bytes(),
        lambda path: io.BytesIO(path.read_bytes()),
        lambda path: path,
        str,
        lambda path: path.open("rb"),
    ],
    ids=["bytes", "BytesIO", "Path", "str path", "file object"],
)
@respx.mock
async def test_search_upload(search_response: dict[str, Any], tmp_path: Path, make_source: Any) -> None:
    image = tmp_path / "frame.jpg"
    image.write_bytes(b"\xff\xd8fake-jpeg")
    route = respx.post(f"{API}/search").respond(json=search_response)

    source = make_source(image)
    try:
        await TraceMoe().search(source)
    finally:
        if hasattr(source, "close"):
            source.close()

    request = route.calls.last.request
    assert request.headers["content-type"].startswith("multipart/form-data")
    assert b'name="image"' in request.content
    assert b"\xff\xd8fake-jpeg" in request.content
    assert "url" not in request.url.params


@respx.mock
async def test_search_vector() -> None:
    route = respx.post(f"{API}/search").respond(json={"error": "", "result": [make_result()]})

    response = await TraceMoe().search_vector("gwebWzth7oPe2UIubOJmozi1NDFp", anilist_info=False)

    assert json.loads(route.calls.last.request.content) == {"vector": "gwebWzth7oPe2UIubOJmozi1NDFp"}
    assert response.best_result is not None


@respx.mock
async def test_search_vectors_batch() -> None:
    route = respx.post(f"{API}/search").respond(
        json={"error": "", "result": [[make_result()], []]},
    )

    response = await TraceMoe().search_vectors(["aaa", (1.0,) * 33])

    body = json.loads(route.calls.last.request.content)
    assert body == {"vector": ["aaa", [1.0] * 33]}
    assert len(response.result) == 2
    assert response.best_results[0] is not None
    assert response.best_results[1] is None


async def test_search_vectors_requires_items() -> None:
    with pytest.raises(ValueError, match="non-empty"):
        await TraceMoe().search_vectors([])


def test_preview_urls() -> None:
    item = AnimeSearch.model_validate(make_result())
    assert item.image_url() == f"{API}/image/abc"
    assert item.image_url(size="l") == f"{API}/image/abc?size=l"
    video_url = httpx.URL(item.video_url(size="s", mute=True, min_duration=1, max_duration=4))
    assert dict(video_url.params) == {"size": "s", "mute": "", "minDuration": "1", "maxDuration": "4"}


def test_anilist_without_mal_id() -> None:
    anilist = AniList.model_validate({"id": 1, "title": {"romaji": "x"}, "extra": "kept"})
    assert anilist.mal_url is None
    assert anilist.url == "https://anilist.co/anime/1"
    assert anilist.model_extra == {"extra": "kept"}

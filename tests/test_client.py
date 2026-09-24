from __future__ import annotations

from datetime import datetime, timedelta, timezone

import httpx
import respx

import aiotracemoeapi
from aiotracemoeapi import RateLimit, TraceMoe

from .conftest import API, RATE_LIMIT_HEADERS

ME_RESPONSE = {"id": "127.0.0.1", "priority": 0, "concurrency": 1, "quota": 100, "quotaUsed": 7}


def test_version() -> None:
    assert aiotracemoeapi.__version__ != "0.0.0"


@respx.mock
async def test_me() -> None:
    respx.get(f"{API}/me").respond(json=ME_RESPONSE, headers=RATE_LIMIT_HEADERS)

    me = await TraceMoe().me()

    assert me.id == "127.0.0.1"
    assert me.quota_used == 7
    assert me.quota_left == 93
    assert me.limits == RateLimit(limit=100, remaining=99, reset=1790248600)


@respx.mock
async def test_usage() -> None:
    route = respx.get(f"{API}/me").respond(
        json=[
            {"time": "2026-09-24T10:00:00.000Z", "200": 5, "400": 1, "402": 0, "total": 6},
            {"time": "2026-09-24T11:00:00.000Z", "200": 2, "total": 2},
        ]
    )

    usage = await TraceMoe().usage("hour")

    assert route.calls.last.request.url.params["period"] == "hour"
    assert usage[0].time == datetime(2026, 9, 24, 10, tzinfo=timezone.utc)
    assert usage[0].total == 6
    assert usage[0].by_status == {200: 5, 400: 1, 402: 0}
    assert usage[1].by_status == {200: 2}


@respx.mock
async def test_token_header() -> None:
    route = respx.get(f"{API}/me").respond(json=ME_RESPONSE)

    async with TraceMoe(token="secret") as api:
        await api.me()

    assert route.calls.last.request.headers["x-trace-key"] == "secret"


@respx.mock
async def test_no_token_header() -> None:
    route = respx.get(f"{API}/me").respond(json=ME_RESPONSE)
    await TraceMoe().me()
    assert "x-trace-key" not in route.calls.last.request.headers


@respx.mock
async def test_custom_base_url() -> None:
    route = respx.get("https://trace.example.com/api/me").respond(json=ME_RESPONSE)
    await TraceMoe(base_url="https://trace.example.com/api/").me()
    assert route.called


async def test_context_manager_closes_own_client() -> None:
    api = TraceMoe()
    async with api:
        session = api._session
        assert session is not None
        assert not session.is_closed
    assert session.is_closed
    assert api._session is None


@respx.mock
async def test_external_client_is_not_closed() -> None:
    respx.get(f"{API}/me").respond(json=ME_RESPONSE)

    async with httpx.AsyncClient() as client:
        async with TraceMoe(token="secret", client=client) as api:
            await api.me()
        assert not client.is_closed


@respx.mock
async def test_context_manager_is_reusable() -> None:
    respx.get(f"{API}/me").respond(json=ME_RESPONSE)
    api = TraceMoe()
    async with api:
        await api.me()
    async with api:
        await api.me()


def test_rate_limit_from_legacy_headers() -> None:
    limit = RateLimit.from_headers(httpx.Headers(RATE_LIMIT_HEADERS))
    assert limit == RateLimit(limit=100, remaining=99, reset=1790248600)
    assert limit.reset_datetime == datetime.fromtimestamp(1790248600, tz=timezone.utc)
    assert isinstance(limit.reset_timedelta, timedelta)


def test_rate_limit_from_standard_headers() -> None:
    limit = RateLimit.from_headers(
        httpx.Headers({"ratelimit-limit": "100", "ratelimit-remaining": "42", "ratelimit-reset": "30"})
    )
    assert limit.limit == 100
    assert limit.remaining == 42
    assert timedelta(seconds=25) < limit.reset_timedelta <= timedelta(seconds=31)


def test_rate_limit_missing_headers() -> None:
    assert RateLimit.from_headers(httpx.Headers()) == RateLimit(limit=0, remaining=0, reset=0)

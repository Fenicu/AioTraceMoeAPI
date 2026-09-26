from __future__ import annotations

import asyncio
from datetime import datetime, timedelta, timezone
from email.utils import format_datetime
from typing import Any

import pytest
import respx

from aiotracemoeapi import (
    BadRequest,
    ConcurrencyLimitExceeded,
    FailedFetchImage,
    FailedProcessImage,
    ForbiddenError,
    GatewayTimeout,
    InternalServerError,
    InvalidAPIKey,
    InvalidImageUrl,
    InvalidVector,
    MethodNotAllowed,
    PayloadTooLarge,
    PaymentRequired,
    SearchQueueFull,
    SearchQuotaDepleted,
    ServiceUnavailable,
    TooManyRequests,
    TooManyVectors,
    TraceMoe,
    TraceMoeAPIError,
)

from .conftest import API


@pytest.mark.parametrize(
    ("status", "message", "error_cls", "parent_cls"),
    [
        (403, "Invalid API key", InvalidAPIKey, ForbiddenError),
        (
            402,
            "Search quota depleted (quota per 24 hours: 100, used: 100)",
            SearchQuotaDepleted,
            PaymentRequired,
        ),
        (402, "Concurrency limit exceeded", ConcurrencyLimitExceeded, PaymentRequired),
        (503, "Error: Search queue is full", SearchQueueFull, ServiceUnavailable),
        (400, "Invalid image url not-a-url", InvalidImageUrl, BadRequest),
        (404, "Failed to fetch image https://example.com/a.jpg", FailedFetchImage, TraceMoeAPIError),
        (400, "Failed to process image", FailedProcessImage, BadRequest),
        (400, "Failed to process file", FailedProcessImage, BadRequest),
        (400, "Invalid vector format", InvalidVector, BadRequest),
        (400, "Too many vectors (max 10)", TooManyVectors, BadRequest),
        (400, "Something new", BadRequest, TraceMoeAPIError),
        (405, "Method Not Allowed", MethodNotAllowed, TraceMoeAPIError),
        (500, "Search failed. Database temporarily unavailable.", InternalServerError, TraceMoeAPIError),
        (503, "Database is not responding", ServiceUnavailable, TraceMoeAPIError),
        (504, "Server is overloaded", GatewayTimeout, TraceMoeAPIError),
        (418, "I'm a teapot", TraceMoeAPIError, Exception),
    ],
)
@respx.mock
async def test_error_mapping(
    status: int, message: str, error_cls: type[TraceMoeAPIError], parent_cls: type[Exception]
) -> None:
    respx.get(f"{API}/search").respond(status, json={"error": message})

    with pytest.raises(error_cls) as exc_info:
        await TraceMoe().search("https://example.com/a.jpg")

    exc = exc_info.value
    assert type(exc) is error_cls
    assert isinstance(exc, parent_cls)
    assert exc.status_code == status
    assert exc.text == message
    assert exc.raw_response is not None
    assert str(exc) == f"{message} (Status: {status})"


@respx.mock
async def test_non_json_error() -> None:
    respx.post(f"{API}/search").respond(413, text="Payload Too Large")

    with pytest.raises(PayloadTooLarge, match="Payload Too Large"):
        await TraceMoe().search(b"x")


@respx.mock
async def test_quota_depleted_details() -> None:
    error = "Search quota depleted (quota per 24 hours: 100, used: 100)"
    respx.get(f"{API}/search").respond(402, json={"quota": 100, "quotaUsed": 100, "error": error})

    with pytest.raises(SearchQuotaDepleted) as exc_info:
        await TraceMoe().search("https://example.com/a.jpg")

    assert exc_info.value.quota == 100
    assert exc_info.value.quota_used == 100


@respx.mock
async def test_error_in_successful_response() -> None:
    respx.get(f"{API}/search").respond(200, json={"error": "Invalid image url", "result": []})

    with pytest.raises(InvalidImageUrl):
        await TraceMoe().search("https://example.com/a.jpg")


@pytest.fixture
def sleeps(monkeypatch: pytest.MonkeyPatch) -> list[float]:
    calls: list[float] = []

    async def fake_sleep(delay: float) -> None:
        calls.append(delay)

    monkeypatch.setattr(asyncio, "sleep", fake_sleep)
    return calls


@respx.mock
async def test_retry_on_concurrency_limit(search_response: dict[str, Any], sleeps: list[float]) -> None:
    route = respx.get(f"{API}/search")
    route.side_effect = [
        respx.MockResponse(402, json={"error": "Concurrency limit exceeded"}),
        respx.MockResponse(503, json={"error": "Error: Search queue is full"}),
        respx.MockResponse(200, json=search_response),
    ]

    response = await TraceMoe(max_retries=2, retry_delay=0.5).search("https://example.com/a.jpg")

    assert response.best_result is not None
    assert route.call_count == 3
    assert sleeps == [0.5, 1.0]


@respx.mock
async def test_retry_respects_retry_after(search_response: dict[str, Any], sleeps: list[float]) -> None:
    route = respx.get(f"{API}/search")
    route.side_effect = [
        respx.MockResponse(429, text="Too many requests", headers={"retry-after": "7"}),
        respx.MockResponse(200, json=search_response),
    ]

    await TraceMoe(max_retries=1).search("https://example.com/a.jpg")

    assert sleeps == [7.0]


@pytest.mark.usefixtures("sleeps")
@respx.mock
async def test_retry_gives_up() -> None:
    route = respx.get(f"{API}/search").respond(402, json={"error": "Concurrency limit exceeded"})

    with pytest.raises(ConcurrencyLimitExceeded):
        await TraceMoe(max_retries=2).search("https://example.com/a.jpg")

    assert route.call_count == 3


@respx.mock
async def test_no_retry_by_default(sleeps: list[float]) -> None:
    route = respx.get(f"{API}/search").respond(402, json={"error": "Concurrency limit exceeded"})

    with pytest.raises(ConcurrencyLimitExceeded):
        await TraceMoe().search("https://example.com/a.jpg")

    assert route.call_count == 1
    assert sleeps == []


@respx.mock
async def test_no_retry_on_quota_depleted(sleeps: list[float]) -> None:
    route = respx.get(f"{API}/search").respond(402, json={"error": "Search quota depleted"})

    with pytest.raises(SearchQuotaDepleted):
        await TraceMoe(max_retries=3).search("https://example.com/a.jpg")

    assert route.call_count == 1
    assert sleeps == []


@respx.mock
async def test_too_many_requests_retry_after() -> None:
    respx.get(f"{API}/me").respond(429, text="Too many requests", headers={"retry-after": "30"})

    with pytest.raises(TooManyRequests) as exc_info:
        await TraceMoe().me()

    assert exc_info.value.retry_after == 30.0


@respx.mock
async def test_retry_on_failed_fetch_with_503(search_response: dict[str, Any], sleeps: list[float]) -> None:
    route = respx.get(f"{API}/search")
    route.side_effect = [
        respx.MockResponse(503, json={"error": "Failed to fetch image https://example.com/a.jpg"}),
        respx.MockResponse(200, json=search_response),
    ]

    await TraceMoe(max_retries=1).search("https://example.com/a.jpg")

    assert route.call_count == 2
    assert len(sleeps) == 1


@respx.mock
async def test_no_retry_on_failed_fetch_with_404(sleeps: list[float]) -> None:
    route = respx.get(f"{API}/search").respond(404, json={"error": "Failed to fetch image https://example.com/a.jpg"})

    with pytest.raises(FailedFetchImage):
        await TraceMoe(max_retries=2).search("https://example.com/a.jpg")

    assert route.call_count == 1
    assert sleeps == []


@respx.mock
async def test_retry_after_http_date() -> None:
    retry_at = datetime.now(timezone.utc) + timedelta(seconds=120)
    headers = {"retry-after": format_datetime(retry_at, usegmt=True)}
    respx.get(f"{API}/me").respond(429, text="Too many requests", headers=headers)

    with pytest.raises(TooManyRequests) as exc_info:
        await TraceMoe().me()

    retry_after = exc_info.value.retry_after
    assert retry_after is not None
    assert 100 < retry_after <= 120


@respx.mock
async def test_retry_after_in_the_past_and_invalid() -> None:
    respx.get(f"{API}/me").side_effect = [
        respx.MockResponse(429, headers={"retry-after": "Sat, 01 Jan 2000 00:00:00 GMT"}),
        respx.MockResponse(429, headers={"retry-after": "soon"}),
    ]

    with pytest.raises(TooManyRequests) as exc_info:
        await TraceMoe().me()
    assert exc_info.value.retry_after == 0.0

    with pytest.raises(TooManyRequests) as exc_info:
        await TraceMoe().me()
    assert exc_info.value.retry_after is None

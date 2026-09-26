# AioTraceMoeAPI

[![CI](https://github.com/Fenicu/AioTraceMoeAPI/actions/workflows/ci.yml/badge.svg)](https://github.com/Fenicu/AioTraceMoeAPI/actions/workflows/ci.yml)
[![MIT License](https://img.shields.io/pypi/l/aiotracemoeapi)](https://opensource.org/licenses/MIT)
[![PyPi Package Version](https://img.shields.io/pypi/v/aiotracemoeapi)](https://pypi.python.org/pypi/aiotracemoeapi)
[![Downloads](https://img.shields.io/pypi/dm/aiotracemoeapi.svg)](https://pypi.python.org/pypi/aiotracemoeapi)
[![Supported python versions](https://img.shields.io/pypi/pyversions/aiotracemoeapi)](https://pypi.python.org/pypi/aiotracemoeapi)

A simple but extensible asynchronous Python wrapper for the [trace.moe](https://trace.moe) API.

## Key Features

*   **Async**: Built on top of `httpx`.
*   **Typed**: Fully typed (ships `py.typed`), with Pydantic v2 models for every response.
*   **Complete**: Search by URL, file, bytes or ColorLayout vector (including batch search), `/me` quota and usage history,
    preview URL helpers.
*   **Precise errors**: A dedicated exception for every API error, with optional automatic retries.

## Installation

Python 3.10+ is required.

```bash
uv add aiotracemoeapi
```

or

```bash
pip install aiotracemoeapi
```

## Usage

### Search by URL, file or bytes

```python
import asyncio

from aiotracemoeapi import TraceMoe


async def main():
    async with TraceMoe() as api:
        # URLs are detected automatically
        response = await api.search("https://images.plurk.com/32B15UXxymfSMwKGTObY5e.jpg")

        # A local file path, pathlib.Path, bytes or a binary file object work too
        # response = await api.search("image.jpg")
        # response = await api.search(open("image.jpg", "rb"))

    best = response.best_result
    if best is None:
        print("No results found.")
        return

    print(f"Anime: {best.anilist_info.title.romaji}")  # AniList info is included by default
    print(f"Episode: {best.episode_start}")
    print(f"Scene: {best.anime_from:.1f}s - {best.anime_to:.1f}s, best frame at {best.at:.1f}s")
    print(f"Similarity: {best.short_similarity()}")  # below 90% is most likely a wrong result
    print(f"Preview: {best.video_url(size='l', mute=True)}")  # preview URLs expire in 5 minutes
    print(f"Quota used: {response.quota_used}/{response.quota}")


if __name__ == "__main__":
    asyncio.run(main())
```

Search options:

```python
from aiotracemoeapi import CutBorders

await api.search(
    "image.jpg",
    anilist_id=21034,  # search only within one anime
    anilist_info=False,  # return only AniList IDs (faster)
    cut_borders=CutBorders.BOTH,  # search with both the original and the cut image (may cost 2 credits)
)
```

### Search by ColorLayout vector

If you already have the 33-dimensional MPEG-7 ColorLayout vector (see [trace.moe-id](https://github.com/soruly/trace.moe-id)),
search by the vector directly. This is faster and saves bandwidth:

```python
response = await api.search_vector("gwebWzth7oPe2UIubOJmozi1NDFp")  # base64 hash or 33 numbers

# Batch search: up to 10 vectors, each one costs 1 search credit
batch = await api.search_vectors([vector1, vector2])
for best in batch.best_results:
    print(best)
```

### Account quota and usage

```python
async def main():
    # Get your API key at https://trace.moe/account; without a key you are identified by your IP address
    async with TraceMoe(token="your_token_here") as api:
        me = await api.me()
        print(f"Priority: {me.priority}, concurrency: {me.concurrency}")
        print(f"Quota: {me.quota_used}/{me.quota} used in the last 24 hours, {me.quota_left} left")

        for slot in await api.usage("day"):
            print(slot.time, slot.total, slot.by_status)
```

### Error handling and retries

Every API error has its own exception. All of them subclass `TraceMoeAPIError`:

| Exception                                         | Parent                | When                                      |
| ------------------------------------------------- | --------------------- | ----------------------------------------- |
| `InvalidImageUrl`, `FailedProcessImage`           | `BadRequest`          | Bad URL or image that cannot be decoded   |
| `InvalidVector`, `TooManyVectors`                 | `BadRequest`          | Bad vector search input                   |
| `FailedFetchImage`                                | `TraceMoeAPIError`    | The server could not download the URL     |
| `SearchQuotaDepleted`, `ConcurrencyLimitExceeded` | `PaymentRequired`     | 24h quota depleted / too many parallel requests |
| `InvalidAPIKey`                                   | `ForbiddenError`      | Wrong API key                             |
| `PayloadTooLarge`                                 | `TraceMoeAPIError`    | File larger than 25MB                     |
| `TooManyRequests`                                 | `TraceMoeAPIError`    | More than 100 requests per minute         |
| `SearchQueueFull`                                 | `ServiceUnavailable`  | Server is busy                            |
| `InternalServerError`, `GatewayTimeout`           | `TraceMoeAPIError`    | Server errors                             |

```python
from aiotracemoeapi import SearchQuotaDepleted, TraceMoe, TraceMoeAPIError

# Retry up to 3 times on concurrency limit, rate limit, full queue or overload errors
async with TraceMoe(max_retries=3, retry_delay=1.0) as api:
    try:
        response = await api.search("image.jpg")
    except SearchQuotaDepleted as e:
        print(f"Quota depleted: {e.quota_used}/{e.quota}")
    except TraceMoeAPIError as e:
        print(f"API error {e.status_code}: {e.text}")
```

### Custom HTTP client or server

```python
import httpx

async with httpx.AsyncClient(proxy="http://localhost:8080") as client:
    api = TraceMoe(client=client)  # your client is not closed by the wrapper
    ...

api = TraceMoe(base_url="https://trace.example.com")  # self-hosted trace.moe-api
```

## Examples

The [examples](examples/) folder has ready-to-run scripts: a command-line search, quota and usage report,
searching a whole folder in parallel, vector search, downloading previews and a Telegram bot on aiogram 3.

```bash
uv run examples/console.py https://images.plurk.com/32B15UXxymfSMwKGTObY5e.jpg
uv run examples/batch_folder.py ./screenshots results.csv
BOT_TOKEN=123:abc uv run examples/telegram_bot.py
```

## Development

```bash
uv sync
make check  # ruff, mypy and pytest
```

See [CHANGELOG.md](CHANGELOG.md) for the list of changes, including how to migrate from 3.x.

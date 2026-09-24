# Changelog

## 4.0.0

Brings the wrapper up to date with the current [trace.moe API](https://soruly.github.io/trace.moe-api/).

### Breaking changes

- Python 3.10+ is required. 3.9 never actually worked with 3.x: the code uses `X | Y` annotations.
- `search()` parameters after `source` are keyword-only. The first parameter was renamed `path` → `source`,
  and `ani_list_id` was renamed `anilist_id`.
- `search()` now detects URLs itself: strings starting with `http://` or `https://` are searched by URL, other strings
  are treated as file paths. `is_url=True` still works; `is_url=False` forces a file path.
- A missing file raises `FileNotFoundError` and an unsupported source raises `TypeError` (was `AttributeError`).
- API errors now raise the specific exception. Before, only the status-based exception was raised, so
  `InvalidAPIKey`, `ConcurrencyLimitExceeded`, `SearchQueueFull`, `InvalidImageUrl`, `FailedFetchImage` and
  `FailedProcessImage` were never raised. Specific exceptions subclass the status-based ones
  (`InvalidAPIKey` → `ForbiddenError`, `SearchQueueFull` → `ServiceUnavailable`, and so on), so
  `except ForbiddenError` still catches them.
- A 402 status without a known message now raises the new `PaymentRequired`, the parent of `SearchQuotaDepleted`
  and `ConcurrencyLimitExceeded`. Before, it raised `SearchQuotaDepleted`.
- `FailedDetectAndCutBorders` was removed: the API no longer returns this error.
- `TraceMoeAPIError`: `_raw_response` was renamed `raw_response`. The exception now has `status_code`
  and `data` (the parsed error body).
- `TraceMoe(...)` options after `token` are keyword-only. The `api_url` attribute was renamed `base_url`
  (it is now also a constructor option).
- `RateLimit.reset_datetime` is timezone-aware (UTC), and `reset_timedelta` now returns `timedelta`.
- `AniList.mal_url` returns `None` when the MAL ID is unknown.
- `AnimeResponse.error` is always a `str`, and `AnimeResponse.result` is always a list.

### New

- New search result fields: `at`, `duration`, `episode_start`, `episode_end`.
- New search response fields: `quota` and `quota_used`.
- `CutBorders` enum; `cut_borders=CutBorders.BOTH` searches with both the original and the cut image.
- `search()` accepts `bytes`, `pathlib.Path` and any binary file object.
- Vector search: `search_vector()`, and batch search with `search_vectors()` (up to 10 vectors).
- `usage(period)` returns the search history from `/me?period=...`.
- Automatic retries: `TraceMoe(max_retries=3)` retries on concurrency limit, rate limit (honouring `Retry-After`),
  full queue and overload errors, with exponential backoff.
- `TraceMoe(client=httpx.AsyncClient(...))` uses your own HTTP client; `base_url` points to a self-hosted server.
- Preview helpers: `AnimeSearch.image_url(size=...)` and `AnimeSearch.video_url(size=..., mute=..., ...)`.
- `AnimeSearch.anilist_id`, `AnimeSearch.anilist_info`, `AniList.url` and `BotMe.quota_left` helpers.
- New exceptions: `PaymentRequired`, `InvalidVector`, `TooManyVectors`.
- `SearchQuotaDepleted.quota` / `.quota_used` and `TooManyRequests.retry_after`.
- Rate limit info falls back to the standard `RateLimit-*` headers.
- `py.typed` marker, so type checkers use the package's annotations.

### Internal

- Test suite (pytest and respx) and GitHub Actions CI for Python 3.10–3.14; mypy strict.
- PyPI publishing via Trusted Publishing on GitHub release.
- Full PyPI metadata (license, classifiers, URLs); `__version__` comes from the package metadata.
- Updated the `uv_build` range and the dependency bounds (`httpx<1`, `pydantic<3`).

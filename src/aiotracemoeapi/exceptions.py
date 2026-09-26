from __future__ import annotations

from datetime import datetime, timezone
from email.utils import parsedate_to_datetime
from typing import Any

import httpx


class TraceMoeAPIError(Exception):
    """Base exception for all TraceMoe API errors."""

    def __init__(
        self,
        url: str | None = None,
        text: str | None = None,
        raw_response: httpx.Response | None = None,
        status_code: int | None = None,
        data: dict[str, Any] | None = None,
    ) -> None:
        """
        Initialize the exception.

        :param url: Requested URL
        :param text: Error message returned by the API
        :param raw_response: Raw HTTP response
        :param status_code: HTTP status code
        :param data: Parsed JSON body of the error response
        """
        self.url = url
        self.text = text
        self.raw_response = raw_response
        self.status_code = status_code if status_code is not None else getattr(raw_response, "status_code", None)
        self.data = data or {}
        super().__init__(text)

    def __str__(self) -> str:
        if self.status_code is None:
            return str(self.text)
        return f"{self.text} (Status: {self.status_code})"


# --- Generic HTTP errors ---


class BadRequest(TraceMoeAPIError):
    """Raised when the request is invalid (400)."""


class PaymentRequired(TraceMoeAPIError):
    """Raised when the search quota or concurrency limit is exceeded (402)."""


class ForbiddenError(TraceMoeAPIError):
    """Raised when access is forbidden (403)."""


class MethodNotAllowed(TraceMoeAPIError):
    """Raised when the method is not allowed or no image was sent (405)."""


class PayloadTooLarge(TraceMoeAPIError):
    """Raised when the uploaded file is larger than 25MB (413)."""


class TooManyRequests(TraceMoeAPIError):
    """Raised when the HTTP rate limit is exceeded (429)."""

    @property
    def retry_after(self) -> float | None:
        """Seconds to wait before retrying, from the ``Retry-After`` header (seconds or HTTP date)."""
        if self.raw_response is None:
            return None
        value = self.raw_response.headers.get("retry-after")
        if value is None:
            return None
        try:
            return max(float(value), 0.0)
        except ValueError:
            pass
        try:
            retry_at = parsedate_to_datetime(value)
        except (TypeError, ValueError):
            return None
        if retry_at.tzinfo is None:
            retry_at = retry_at.replace(tzinfo=timezone.utc)
        return max((retry_at - datetime.now(timezone.utc)).total_seconds(), 0.0)


class InternalServerError(TraceMoeAPIError):
    """Raised when the server encounters an error (500)."""


class ServiceUnavailable(TraceMoeAPIError):
    """Raised when the service is unavailable (503)."""


class GatewayTimeout(TraceMoeAPIError):
    """Raised when the server is overloaded (504)."""


# --- Specific API errors ---


class InvalidAPIKey(ForbiddenError):
    """Raised when the API key is invalid (403)."""


class SearchQuotaDepleted(PaymentRequired):
    """Raised when the 24-hour search quota is depleted (402)."""

    @property
    def quota(self) -> int | None:
        """Max quota for the rolling 24-hour window."""
        return self.data.get("quota")

    @property
    def quota_used(self) -> int | None:
        """Quota used in the last 24 hours."""
        return self.data.get("quotaUsed")


class ConcurrencyLimitExceeded(PaymentRequired):
    """Raised when too many parallel search requests are made (402)."""


class SearchQueueFull(ServiceUnavailable):
    """Raised when the search queue is full (503)."""


class InvalidImageUrl(BadRequest):
    """Raised when the image URL is invalid (400)."""


class FailedFetchImage(TraceMoeAPIError):
    """Raised when the server cannot fetch the image by URL (status mirrors the remote server)."""


class FailedProcessImage(BadRequest):
    """Raised when the image or file cannot be processed (400)."""


class InvalidVector(BadRequest):
    """Raised when the color layout vector has an invalid format (400)."""


class TooManyVectors(BadRequest):
    """Raised when more than 10 vectors are sent in one batch search (400)."""


ERRORS_STATUS_MAPPING: dict[int, type[TraceMoeAPIError]] = {
    400: BadRequest,
    402: PaymentRequired,
    403: ForbiddenError,
    405: MethodNotAllowed,
    413: PayloadTooLarge,
    429: TooManyRequests,
    500: InternalServerError,
    503: ServiceUnavailable,
    504: GatewayTimeout,
}

# Error message prefix -> exception class. The server may append details to the message,
# e.g. "Search quota depleted (quota per 24 hours: 100, used: 100)" or "Invalid image url <url>".
ERRORS_MESSAGE_MAPPING: tuple[tuple[str, type[TraceMoeAPIError]], ...] = (
    ("Invalid API key", InvalidAPIKey),
    ("Search quota depleted", SearchQuotaDepleted),
    ("Concurrency limit exceeded", ConcurrencyLimitExceeded),
    ("Error: Search queue is full", SearchQueueFull),
    ("Search queue is full", SearchQueueFull),
    ("Invalid image url", InvalidImageUrl),
    ("Failed to fetch image", FailedFetchImage),
    ("Failed to process", FailedProcessImage),
    ("Invalid vector format", InvalidVector),
    ("Too many vectors", TooManyVectors),
)

# HTTP statuses that are worth retrying after a pause, whatever the error message is.
RETRYABLE_STATUS_CODES = frozenset({429, 503, 504})


def is_retryable(error: TraceMoeAPIError) -> bool:
    """Whether the request may succeed if repeated after a pause."""
    return isinstance(error, ConcurrencyLimitExceeded) or error.status_code in RETRYABLE_STATUS_CODES


def get_error_class(status_code: int, message: str | None) -> type[TraceMoeAPIError]:
    """Pick the most specific exception class for an error response."""
    if message:
        for prefix, error_cls in ERRORS_MESSAGE_MAPPING:
            if message.startswith(prefix):
                return error_cls
    return ERRORS_STATUS_MAPPING.get(status_code, TraceMoeAPIError)

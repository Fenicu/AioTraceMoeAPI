
import httpx


class TraceMoeAPIError(Exception):
    """Base exception for all TraceMoe API errors."""

    url: str | None
    text: str | None
    _raw_response: httpx.Response | None

    def __init__(
        self,
        url: str | None = None,
        text: str | None = None,
        raw_response: httpx.Response | None = None,
    ) -> None:
        """Initialize the exception."""
        self.url = url
        self.text = text
        self._raw_response = raw_response
        super().__init__(text)


class InvalidAPIKey(TraceMoeAPIError):
    """Raised when the API key is invalid (403)."""


class SearchQuotaDepleted(TraceMoeAPIError):
    """Raised when the search quota is depleted (402)."""


class ConcurrencyLimitExceeded(TraceMoeAPIError):
    """Raised when the concurrency limit is exceeded (402)."""


class SearchQueueFull(TraceMoeAPIError):
    """Raised when the search queue is full (503)."""


class InvalidImageUrl(TraceMoeAPIError):
    """Raised when the image URL is invalid (400)."""


class FailedFetchImage(TraceMoeAPIError):
    """Raised when the image cannot be fetched (400/500)."""


class FailedProcessImage(TraceMoeAPIError):
    """Raised when the image cannot be processed (400/500)."""


class FailedDetectAndCutBorders(TraceMoeAPIError):
    """Raised when border detection fails."""


class BadRequest(TraceMoeAPIError):
    """Raised when the request is invalid (400)."""


class ForbiddenError(TraceMoeAPIError):
    """Raised when access is forbidden (403)."""


class InternalServerError(TraceMoeAPIError):
    """Raised when the server encounters an error (500)."""


class ServiceUnavailable(TraceMoeAPIError):
    """Raised when the service is unavailable (503)."""


class GatewayTimeout(TraceMoeAPIError):
    """Raised when the gateway times out (504)."""


class TooManyRequests(TraceMoeAPIError):
    """Raised when the rate limit is exceeded (429)."""


class PayloadTooLarge(TraceMoeAPIError):
    """Raised when the payload is too large (413)."""


class MethodNotAllowed(TraceMoeAPIError):
    """Raised when the method is not allowed (405)."""


ERRORS_STATUS_MAPPING = {
    400: BadRequest,
    402: SearchQuotaDepleted,
    403: ForbiddenError,
    405: MethodNotAllowed,
    413: PayloadTooLarge,
    429: TooManyRequests,
    500: InternalServerError,
    503: ServiceUnavailable,
    504: GatewayTimeout,
}

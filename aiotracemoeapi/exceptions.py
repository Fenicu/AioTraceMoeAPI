from typing import Optional

from aiohttp import ClientResponse

from .types import AnimeResponse

# ERRORS reference https://github.com/soruly/trace.moe-api/blob/master/src/search.js


class TraceMoeAPIError(Exception):
    url: Optional[str]
    text: Optional[str]
    _raw_response: Optional[ClientResponse]
    anime_response_object: Optional[AnimeResponse]

    def __init__(
        self,
        url: str = None,
        text: str = None,
        raw_response: ClientResponse = None,
        anime_response_object: AnimeResponse = None,
    ) -> None:
        self.url = url
        self.text = text
        self._raw_response = raw_response
        self.anime_response_object = anime_response_object


class InvalidAPIKey(TraceMoeAPIError):
    pass


class SearchQuotaDepleted(TraceMoeAPIError):
    pass


class ConcurrencyLimitExceeded(TraceMoeAPIError):
    pass


class SearchQueueFull(TraceMoeAPIError):
    pass


class InvalidImageUrl(TraceMoeAPIError):
    pass


class FailedFetchImage(TraceMoeAPIError):
    pass


class FailedProcessImage(TraceMoeAPIError):
    pass


class FailedDetectAndCutBorders(TraceMoeAPIError):
    pass


class BadRequest(TraceMoeAPIError):
    pass


class ForbiddenError(TraceMoeAPIError):
    pass


class InternalServerError(TraceMoeAPIError):
    pass


class ServiceUnavailable(TraceMoeAPIError):
    pass


class GatewayTimeout(TraceMoeAPIError):
    pass


ERRORS_STATUS_MAPPING = {
    400: BadRequest,
    403: ForbiddenError,
    500: InternalServerError,
    503: ServiceUnavailable,
    504: GatewayTimeout,
}

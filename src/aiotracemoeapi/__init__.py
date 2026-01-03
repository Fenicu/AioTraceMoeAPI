from .api_wrapper import TraceMoe
from .exceptions import (
    BadRequest,
    ConcurrencyLimitExceeded,
    FailedDetectAndCutBorders,
    FailedFetchImage,
    FailedProcessImage,
    ForbiddenError,
    GatewayTimeout,
    InternalServerError,
    InvalidAPIKey,
    InvalidImageUrl,
    MethodNotAllowed,
    PayloadTooLarge,
    SearchQueueFull,
    SearchQuotaDepleted,
    ServiceUnavailable,
    TooManyRequests,
    TraceMoeAPIError,
)
from .types import AniList, AnimeResponse, AnimeSearch, BotMe, RateLimit

__all__ = (
    "AniList",
    "AnimeResponse",
    "AnimeSearch",
    "BadRequest",
    "BotMe",
    "ConcurrencyLimitExceeded",
    "FailedDetectAndCutBorders",
    "FailedFetchImage",
    "FailedProcessImage",
    "ForbiddenError",
    "GatewayTimeout",
    "InternalServerError",
    "InvalidAPIKey",
    "InvalidImageUrl",
    "MethodNotAllowed",
    "PayloadTooLarge",
    "RateLimit",
    "SearchQueueFull",
    "SearchQuotaDepleted",
    "ServiceUnavailable",
    "TooManyRequests",
    "TraceMoe",
    "TraceMoeAPIError",
)

__version__ = "3.1.2"

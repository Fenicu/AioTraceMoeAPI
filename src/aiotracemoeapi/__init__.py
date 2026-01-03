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
    SearchQuotaDepleted,
    SearchQueueFull,
    ServiceUnavailable,
    TooManyRequests,
    TraceMoeAPIError,
)
from .types import AniList, AnimeResponse, AnimeSearch, BotMe, RateLimit

__all__ = (
    "TraceMoe",
    "AniList",
    "AnimeResponse",
    "AnimeSearch",
    "BotMe",
    "RateLimit",
    "TraceMoeAPIError",
    "InvalidAPIKey",
    "SearchQuotaDepleted",
    "ConcurrencyLimitExceeded",
    "SearchQueueFull",
    "InvalidImageUrl",
    "FailedFetchImage",
    "FailedProcessImage",
    "FailedDetectAndCutBorders",
    "BadRequest",
    "ForbiddenError",
    "InternalServerError",
    "ServiceUnavailable",
    "GatewayTimeout",
    "TooManyRequests",
    "PayloadTooLarge",
    "MethodNotAllowed",
)

__version__ = "3.0.0"

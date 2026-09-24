from importlib.metadata import PackageNotFoundError, version

from .api_wrapper import TraceMoe
from .exceptions import (
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
    TraceMoeAPIError,
)
from .types import (
    AniList,
    AnimeBatchResponse,
    AnimeResponse,
    AnimeSearch,
    AnimeTitle,
    BotMe,
    CutBorders,
    RateLimit,
    UsageStats,
)

try:
    __version__ = version("aiotracemoeapi")
except PackageNotFoundError:  # pragma: no cover - running from a source tree without installation
    __version__ = "0.0.0"

__all__ = (
    "AniList",
    "AnimeBatchResponse",
    "AnimeResponse",
    "AnimeSearch",
    "AnimeTitle",
    "BadRequest",
    "BotMe",
    "ConcurrencyLimitExceeded",
    "CutBorders",
    "FailedFetchImage",
    "FailedProcessImage",
    "ForbiddenError",
    "GatewayTimeout",
    "InternalServerError",
    "InvalidAPIKey",
    "InvalidImageUrl",
    "InvalidVector",
    "MethodNotAllowed",
    "PayloadTooLarge",
    "PaymentRequired",
    "RateLimit",
    "SearchQueueFull",
    "SearchQuotaDepleted",
    "ServiceUnavailable",
    "TooManyRequests",
    "TooManyVectors",
    "TraceMoe",
    "TraceMoeAPIError",
    "UsageStats",
    "__version__",
)

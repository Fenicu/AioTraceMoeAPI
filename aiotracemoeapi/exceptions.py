from typing import Optional


class TraceMoeAPIError(Exception):
    url: Optional[str]
    text: Optional[str]

    def __init__(self, url: str = None, text: str = None) -> None:
        self.url = url
        self.text = text


class SearchQueueFull(TraceMoeAPIError):
    pass

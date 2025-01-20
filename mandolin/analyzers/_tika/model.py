from typing import Any

from pydantic import BaseModel


class TikaResult(BaseModel):
    content_length: int | None = None
    created: str | None = None
    title: str | None = None
    type: str | None = None
    language: str | None = None
    extra: dict[str, Any] | None = None

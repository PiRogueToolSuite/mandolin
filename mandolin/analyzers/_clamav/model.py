from typing import Any

from pydantic import BaseModel


class ClamAVResult(BaseModel):
    infected: bool = False
    description: str | None = None
    filename: str | None = None
    extra: dict[str, Any] | None = None

from enum import Enum
from typing import Generic, TypeVar

from pydantic import BaseModel


class ProcessorType(str, Enum):
    Analyzer = 'analyzer'
    Detector = 'detector'


T = TypeVar('T')


class AnalyzerResult(BaseModel, Generic[T]):
    success: bool = False
    processor_name: str
    processor_url: str
    processor_description: str | None = None
    error: str | None = None
    error_short: str | None = None
    metadata: dict | None = None
    analysis: T | None = None


class Analysis(BaseModel, Generic[T]):
    success: bool = False
    content: str | None = None
    processors: dict[str, AnalyzerResult[T]] | None = None

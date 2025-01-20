import traceback
from abc import ABCMeta, abstractmethod

from fastapi import UploadFile, APIRouter

from mandolin.analyzers import Analysis, AnalyzerResult


class FileProcessor(metaclass=ABCMeta):
    def __init__(self, file: UploadFile, **kwargs):
        self._file: UploadFile = file
        self._filesize: int = file.size
        for key, value in kwargs.items():
            setattr(self, key, value)

    @staticmethod
    @abstractmethod
    def get_router() -> APIRouter:
        pass

    @abstractmethod
    def fail_fast(self) -> bool:
        pass

    @abstractmethod
    def ingest(self):
        pass

    @staticmethod
    def exception_to_string(exception):
        stack = traceback.extract_stack()[:-3] + traceback.extract_tb(exception.__traceback__)  # add limit=??
        pretty = traceback.format_list(stack)
        return ''.join(pretty) + '\n  {} {}'.format(exception.__class__, exception)

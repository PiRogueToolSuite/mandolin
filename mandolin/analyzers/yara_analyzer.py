import logging
from tempfile import NamedTemporaryFile
from typing import Annotated

import environ
import yara
from fastapi import UploadFile, APIRouter, Form, HTTPException

from mandolin.analyzers import Analysis, ProcessorType, AnalyzerResult
from ._yara.model import YaraResult
from .. import FileProcessor

env = environ.FileAwareEnv()


class Yara(FileProcessor):
    processor_name = 'yara'
    processor_url = '/analyzer/yara'
    processor_description = 'Yara - the pattern matching swiss knife'
    processor_type = ProcessorType.Detector
    max_file_size = env.int('MAX_FILE_SIZE', default=250_000_000)
    logger = logging.getLogger(processor_name)

    def __init__(self, file: UploadFile, **kwargs):
        super().__init__(file, **kwargs)
        self.compiled_rules = None

    @staticmethod
    def get_router() -> APIRouter:
        router = APIRouter()

        @router.post(Yara.processor_url, tags=['analyzers'])
        async def analyze_with_yara(
                file: UploadFile,
                rules: Annotated[str, Form()],
        ) -> Analysis[YaraResult]:
            y = Yara(file, rules=rules)
            ingestion_result = Analysis[YaraResult]()
            ingestion_result.success = True
            ingestion_result.processors = {Yara.processor_name: y.ingest()}
            return ingestion_result

        return router

    def fail_fast(self) -> bool:
        if not self.rules.strip():
            raise HTTPException(
                status_code=400,
                detail='No Yara rules provided'
            )
        if self._filesize > self.max_file_size:
            raise HTTPException(
                status_code=400,
                detail=f'The input file is too large [>{self.max_file_size}B]'
            )
        try:
            self.compiled_rules = yara.compile(source=self.rules)
        except Exception as e:
            raise HTTPException(
                status_code=400,
                detail='Invalid Yara rules'
            )
        return False

    def ingest(self) -> AnalyzerResult[YaraResult]:
        self.fail_fast()

        processor_result = AnalyzerResult[YaraResult](
            processor_type=Yara.processor_type,
            processor_name=Yara.processor_name,
            processor_description=Yara.processor_description,
        )

        with NamedTemporaryFile("wb", suffix=self._file.filename) as tmp:
            tmp.write(self._file.file.read())
            matches = self.compiled_rules.match(tmp.name)
            yara_result = YaraResult(
                rules=self.rules
            )
            yara_result.add_matches(matches)
            processor_result.success = True
            processor_result.analysis = yara_result
        return processor_result

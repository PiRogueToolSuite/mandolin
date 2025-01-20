import logging
from pathlib import Path
from tempfile import NamedTemporaryFile

import environ
import magic
from fastapi import UploadFile, APIRouter, HTTPException
from slugify import slugify
from tika_client import TikaClient
from tika_client.data_models import TikaResponse

from mandolin.analyzers import Analysis, AnalyzerResult
from ._tika.model import TikaResult
from .. import FileProcessor

env = environ.FileAwareEnv()


class Tika(FileProcessor):
    tika_url = env.str('TIKA_URL', default='http://localhost:9998')
    processor_name = 'tika'
    processor_url = '/analyzer/tika'
    processor_description = 'Tika engine'
    max_file_size = env.int('MAX_FILE_SIZE', default=250_000_000)
    logger = logging.getLogger(processor_name)

    def __init__(self, file: UploadFile, **kwargs):
        super().__init__(file, **kwargs)

    @staticmethod
    def get_router() -> APIRouter:
        router = APIRouter()

        @router.post(Tika.processor_url, tags=['analyzers'])
        async def analyze_with_tika(file: UploadFile) -> Analysis[TikaResult]:
            try:
                t = Tika(file)
                return t.ingest()
            finally:
                file.file.close()

        return router

    @staticmethod
    def _cleanup_tika_data(data: dict):
        cleaned_data: dict = {}
        for k, v in data.items():
            if k.startswith('X-TIKA'):
                continue
            elif ':' in k:
                key, child_key = k.split(':', maxsplit=1)
                key = slugify(key, separator='_')
                child_key.replace(':', '_')
                child_key = slugify(child_key, separator='_')
                if key not in cleaned_data:
                    cleaned_data[key] = {}
                cleaned_data[key][child_key] = v
            else:
                cleaned_data[slugify(k, separator='_')] = v
        return cleaned_data

    def fail_fast(self) -> bool:
        if self._filesize > self.max_file_size:
            raise HTTPException(
                status_code=400,
                detail=f'The input file is too large [>{self.max_file_size}B]'
            )
        return False

    def ingest(self) -> Analysis[TikaResult]:
        self.fail_fast()

        try:
            return self._invoke_tika()
        except Exception as e:
            Tika.logger.error(e)
            return Analysis[TikaResult](
                success=False,
                error=self.exception_to_string(e),
                error_short=str(e)
            )

    def _invoke_tika(self) -> Analysis[TikaResult]:
        processor_result = AnalyzerResult[TikaResult](
            processor_name=Tika.processor_name,
            processor_description=Tika.processor_description
        )
        ingestion_result = Analysis[TikaResult](
            processors={}
        )
        extra_headers = {}
        # Disable OCR if the file is too large
        if self._file.size >= 10_000_000:  # 10MB
            extra_headers['X-Tika-PDFOcrStrategy'] = 'no_ocr'
            extra_headers['X-Tika-OCRskipOcr'] = 'true'
        with NamedTemporaryFile("wb", suffix=self._file.filename) as tmp:
            tmp.write(self._file.file.read())
            with TikaClient(tika_url=Tika.tika_url, compress=True) as client:
                client.add_headers(extra_headers)
                data: TikaResponse = client.tika.as_text.from_file(
                    Path(tmp.name),
                    magic.from_file(str(tmp.name), mime=True)
                )
                ingestion_result.content = data.content.strip()
                processor_result.analysis = TikaResult(
                    content_length=data.content_length,
                    created=data.created,
                    title=data.title,
                    type=data.type,
                    language=data.language,
                    extra=Tika._cleanup_tika_data(data.data)
                )
                processor_result.success = True
        ingestion_result.processors[Tika.processor_name] = processor_result
        ingestion_result.success = processor_result.success
        return ingestion_result

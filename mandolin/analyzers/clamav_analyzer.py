import logging
from statistics import mode
from tempfile import NamedTemporaryFile

import environ
import httpx
from fastapi import UploadFile, APIRouter, HTTPException
from mandolin.analyzers import Analysis, AnalyzerResult

from ._clamav.model import ClamAVResult
from .. import FileProcessor

env = environ.FileAwareEnv()


class ClamAV(FileProcessor):
    clamav_url = env.str('CLAMAV_URL', default='http://clamav:9000')
    processor_name = 'clamav'
    processor_url = '/analyzer/clamav'
    processor_description = 'ClamAV engine'
    max_file_size = env.int('MAX_FILE_SIZE', default=250_000_000)
    logger = logging.getLogger(processor_name)

    def __init__(self, file: UploadFile, **kwargs):
        super().__init__(file, **kwargs)

    @staticmethod
    def get_router() -> APIRouter:
        router = APIRouter()

        @router.post(ClamAV.processor_url, tags=['analyzers'])
        async def analyze_with_clamav(file: UploadFile) -> Analysis[ClamAVResult]:
            try:
                t = ClamAV(file)
                return t.ingest()
            finally:
                file.file.close()

        return router

    def fail_fast(self) -> bool:
        if self._filesize > self.max_file_size:
            raise HTTPException(
                status_code=400,
                detail=f'The input file is too large [>{self.max_file_size}B]'
            )
        return False

    def ingest(self) -> Analysis[ClamAVResult]:
        self.fail_fast()

        try:
            return self._invoke_clamav()
        except Exception as e:
            ClamAV.logger.error(e)
            return Analysis[ClamAVResult](
                success=False,
                error=self.exception_to_string(e),
                error_short=str(e),
            )

    def _invoke_clamav(self) -> Analysis[ClamAVResult]:
        processor_result = AnalyzerResult[ClamAVResult](
            processor_name=ClamAV.processor_name,
            processor_url=ClamAV.processor_url,
            processor_description=ClamAV.processor_description,
        )
        ingestion_result = Analysis[ClamAVResult](
            processors={}
        )

        files = {
            "file": (self._file.filename, self._file.file, "application/octet-stream"),
        }

        with httpx.Client() as client:
            r = client.post(f"{ClamAV.clamav_url}/v2/scan", files=files, timeout=30)
            if r.status_code not in [200, 406]:
                raise Exception(r.text)
            else:
                data = r.json()[0]
                processor_result.success = True
                processor_result.analysis = ClamAVResult(
                    infected=bool(data.get("Status", "") == "FOUND"),
                    description=data.get("Description", ""),
                    filename=data.get("FileName", "")
                )

        ingestion_result.processors[ClamAV.processor_name] = processor_result
        ingestion_result.success = processor_result.success
        return ingestion_result

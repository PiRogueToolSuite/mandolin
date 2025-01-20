import logging
from enum import Enum
from io import BytesIO
from tempfile import NamedTemporaryFile
from typing import Annotated

import environ
from PIL import Image, ImageOps
from fastapi import APIRouter, UploadFile, Query, HTTPException
from pydantic import BaseModel, PositiveInt
from starlette.responses import StreamingResponse

from mandolin import FileProcessor

env = environ.FileAwareEnv()


class ThumbnailStrategy(str, Enum):
    Pad = 'pad'
    Fit = 'fit'
    Cover = 'cover'
    Contain = 'contain'

    @property
    def image_ops(self) -> ImageOps:
        ops = {
            ThumbnailStrategy.Pad: ImageOps.pad,
            ThumbnailStrategy.Fit: ImageOps.fit,
            ThumbnailStrategy.Cover: ImageOps.cover,
            ThumbnailStrategy.Contain: ImageOps.contain,
        }
        return ops.get(self, ImageOps.pad)


class ThumbnailParameters(BaseModel):
    width: PositiveInt = 300
    height: PositiveInt = 200
    # https://pillow.readthedocs.io/en/stable/reference/ImageColor.html#module-PIL.ImageColor
    color: str | None = None
    # https://pillow.readthedocs.io/en/stable/reference/ImageOps.html#resize-relative-to-a-given-size
    strategy: ThumbnailStrategy = ThumbnailStrategy.Pad


class Thumbnail(FileProcessor):
    processor_name = 'thumbnail'
    processor_url = '/converter/thumbnail'
    processor_description = 'Generate the thumbnail of the given image'
    max_file_size = env.int('MAX_FILE_SIZE', default=250_000_000)
    logger = logging.getLogger(processor_name)

    def __init__(self, file: UploadFile, parameters: ThumbnailParameters, **kwargs):
        super().__init__(file, **kwargs)
        self.parameters = parameters

    @staticmethod
    def get_router() -> APIRouter:
        router = APIRouter()

        @router.post(Thumbnail.processor_url, tags=['converters'], response_class=StreamingResponse)
        async def generate_thumbnail(
                file: UploadFile,
                parameters: Annotated[ThumbnailParameters, Query()]
        ) -> StreamingResponse:
            try:
                t = Thumbnail(file, parameters)
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
        cat, _ = self._file.content_type.split('/', maxsplit=1)
        if not cat.startswith('image'):
            raise HTTPException(
                status_code=400,
                detail=f'File type of {self._file.content_type} is not supported',
            )
        return False

    def ingest(self):
        self.fail_fast()

        image_ops: ImageOps = self.parameters.strategy.image_ops
        filtered_image = BytesIO()
        with NamedTemporaryFile("wb", suffix=self._file.filename) as tmp:
            tmp.write(self._file.file.read())
            with Image.open(tmp.name) as im:
                image_ops(
                    im,
                    (self.parameters.width, self.parameters.height),
                    color=self.parameters.color).save(filtered_image, format='PNG')
            filtered_image.seek(0)
            return StreamingResponse(filtered_image, media_type="image/png")

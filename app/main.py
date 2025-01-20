from fastapi import FastAPI

from mandolin.analyzers.tika_analyzer import Tika
from mandolin.analyzers.yara_analyzer import Yara
from mandolin.converters.thumbnail_converter import Thumbnail

app = FastAPI()

app.include_router(Tika.get_router())
app.include_router(Yara.get_router())
app.include_router(Thumbnail.get_router())


@app.get('/')
def read_root():
    return {'msg': 'Finely slice your files'}

from fastapi import FastAPI
from fastapi.openapi.utils import get_openapi

from mandolin.analyzers.tika_analyzer import Tika
from mandolin.analyzers.yara_analyzer import Yara
from mandolin.converters.thumbnail_converter import Thumbnail

app = FastAPI()

app.include_router(Tika.get_router())
app.include_router(Yara.get_router())
app.include_router(Thumbnail.get_router())


@app.get('/')
def root():
    return {'msg': 'Finely slice your files'}


def custom_openapi():
    if app.openapi_schema:
        return app.openapi_schema
    openapi_schema = get_openapi(
        title="Mandolin",
        version="1.0.0",
        summary="Micro-service to analyze and convert files",
        routes=app.routes,
    )
    openapi_schema["info"]["x-logo"] = {
        "url": "https://pts-project.org/android-chrome-512x512.png"
    }
    app.openapi_schema = openapi_schema
    return app.openapi_schema


app.openapi = custom_openapi

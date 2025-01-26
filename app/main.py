from fastapi import FastAPI
from fastapi.openapi.utils import get_openapi

from mandolin.analyzers.tika_analyzer import Tika
from mandolin.analyzers.yara_analyzer import Yara
from mandolin.converters.thumbnail_converter import Thumbnail

API_VERSION = "1.0.1"

app = FastAPI(
    title="Mandolin",
    description="Micro-service to analyze and convert files",
    summary="Micro-service to analyze and convert files",
    version=API_VERSION
)

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
        version=API_VERSION,
        description="Micro-service to analyze and convert files",
        license_info={
            "name": "GNU General Public License v3.0",
            "identifier": "GPL-3.0-or-later",
        },
        contact={
            "name": "U+039b",
            "url": "https://pts-project.org",
            "email": "contact@defensive-lab.agency",
        },
        routes=app.routes,
    )
    openapi_schema["info"]["x-logo"] = {
        "url": "https://pts-project.org/android-chrome-512x512.png"
    }
    app.openapi_schema = openapi_schema
    return app.openapi_schema


app.openapi = custom_openapi

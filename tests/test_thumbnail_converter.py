from fastapi.testclient import TestClient

from app.main import app
from mandolin.converters.thumbnail_converter import Thumbnail

client = TestClient(app)


def test_thumbnail_inputs():
    processor_url = Thumbnail.processor_url
    url = f'{processor_url}?width=300&height=-200&strategy=pad'
    response = client.post(url, files=None)
    assert response.status_code == 422
    assert response.json() == {"msg": "Hello World"}
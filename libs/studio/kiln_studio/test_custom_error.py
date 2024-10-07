import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from pydantic import BaseModel, Field

from libs.studio.kiln_studio.custom_errors import connect_custom_errors


@pytest.fixture
def app():
    app = FastAPI()
    connect_custom_errors(app)

    class Item(BaseModel):
        name: str = Field(..., min_length=3)
        price: float = Field(..., gt=0)

    @app.post("/items")
    async def create_item(item: Item):
        return item

    return app


@pytest.fixture
def client(app):
    return TestClient(app)


def test_validation_error_single_field(client):
    response = client.post("/items", json={"name": "ab", "price": 10})
    assert response.status_code == 422
    assert response.json() == {
        "message": "Name: String should have at least 3 characters",
        "source_errors": [
            {
                "type": "string_too_short",
                "loc": ["body", "name"],
                "msg": "String should have at least 3 characters",
                "input": "ab",
                "ctx": {"min_length": 3},
            }
        ],
    }


def test_validation_error_multiple_fields(client):
    response = client.post("/items", json={"name": "ab", "price": -5})
    assert response.status_code == 422
    assert response.json() == {
        "message": "Name: String should have at least 3 characters.\nPrice: Input should be greater than 0",
        "source_errors": [
            {
                "type": "string_too_short",
                "loc": ["body", "name"],
                "msg": "String should have at least 3 characters",
                "input": "ab",
                "ctx": {"min_length": 3},
            },
            {
                "type": "greater_than",
                "loc": ["body", "price"],
                "msg": "Input should be greater than 0",
                "input": -5,
                "ctx": {"gt": 0},
            },
        ],
    }


def test_valid_input(client):
    response = client.post("/items", json={"name": "abc", "price": 10})
    assert response.status_code == 200
    assert response.json() == {"name": "abc", "price": 10}

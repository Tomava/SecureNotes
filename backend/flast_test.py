import pytest
from config import *
import main

@pytest.fixture()
def app():
    app, _ = main.create_app()
    app.config.update({
        "TESTING": True,
    })

    yield app


@pytest.fixture()
def client(app):
    return app.test_client()


@pytest.fixture()
def runner(app):
    return app.test_cli_runner()


def test_request_example(client):
    response = client.get("/hash")
    assert b"<h2>Hello, World!</h2>" in response.data

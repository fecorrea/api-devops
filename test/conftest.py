import datetime

import jwt
import pytest
from fastapi.testclient import TestClient

from src.main import (
    SECRET_KEY,
    app,
    get_replay_store_connection,
    initialize_replay_store,
)


@pytest.fixture(scope="session")
def test_client():
    """Create a test client for the FastAPI app"""
    return TestClient(app)


@pytest.fixture(scope="function")
def client():
    """Create a test client for each test function"""
    return TestClient(app)


@pytest.fixture
def valid_api_key():
    """Provide a valid API key"""
    return "2f5ae96c-b558-4c7b-a590-a501ae1c3f6c"


@pytest.fixture
def invalid_api_key():
    """Provide an invalid API key"""
    return "invalid-api-key-123"


@pytest.fixture
def valid_jwt_token():
    """Generate a valid JWT token"""
    import uuid

    payload = {
        "user": "api_client",
        "exp": datetime.datetime.now(datetime.timezone.utc) + datetime.timedelta(seconds=3600),
        "iat": datetime.datetime.now(datetime.timezone.utc),
        "jti": str(uuid.uuid4()),
    }
    return jwt.encode(payload, SECRET_KEY, algorithm="HS256")


@pytest.fixture
def expired_jwt_token():
    """Generate an expired JWT token"""
    payload = {
        "user": "test_user",
        "exp": datetime.datetime.now(datetime.timezone.utc) - datetime.timedelta(seconds=10),
        "iat": datetime.datetime.now(datetime.timezone.utc) - datetime.timedelta(seconds=3610),
    }
    return jwt.encode(payload, SECRET_KEY, algorithm="HS256")


@pytest.fixture
def invalid_jwt_token():
    """Generate a JWT with invalid signature"""
    payload = {
        "user": "test_user",
        "exp": datetime.datetime.now(datetime.timezone.utc) + datetime.timedelta(seconds=3600),
        "iat": datetime.datetime.now(datetime.timezone.utc),
        "jti": "invalid-token-id",
    }
    return jwt.encode(payload, "wrong-secret-key", algorithm="HS256")


@pytest.fixture
def valid_payload():
    """Provide a valid request payload"""
    return {
        "message": "This is a test",
        "to": "Juan Perez",
        "from": "Rita Asturia",
        "timeToLifeSec": 45,
    }


@pytest.fixture
def headers_with_valid_credentials(valid_api_key, valid_jwt_token):
    """Create headers with valid credentials"""
    return {
        "X-Parse-REST-API-Key": valid_api_key,
        "X-JWT-KWY": valid_jwt_token,
        "Content-Type": "application/json",
    }


@pytest.fixture
def headers_missing_api_key(valid_jwt_token):
    """Create headers missing API key"""
    return {"X-JWT-KWY": valid_jwt_token, "Content-Type": "application/json"}


@pytest.fixture
def headers_missing_jwt(valid_api_key):
    """Create headers missing JWT"""
    return {"X-Parse-REST-API-Key": valid_api_key, "Content-Type": "application/json"}


@pytest.fixture
def headers_invalid_api_key(invalid_api_key, valid_jwt_token):
    """Create headers with invalid API key"""
    return {
        "X-Parse-REST-API-Key": invalid_api_key,
        "X-JWT-KWY": valid_jwt_token,
        "Content-Type": "application/json",
    }


@pytest.fixture
def headers_expired_jwt(valid_api_key, expired_jwt_token):
    """Create headers with expired JWT"""
    return {
        "X-Parse-REST-API-Key": valid_api_key,
        "X-JWT-KWY": expired_jwt_token,
        "Content-Type": "application/json",
    }


@pytest.fixture(autouse=True)
def clean_replay_store():
    """Clean replay store database before each test"""
    try:
        with get_replay_store_connection() as conn:
            conn.execute("DROP TABLE IF EXISTS used_tokens")
    except Exception:
        pass

    initialize_replay_store()

    yield

    try:
        with get_replay_store_connection() as conn:
            conn.execute("DELETE FROM used_tokens")
    except Exception:
        pass


def pytest_configure(config):
    """Configure pytest with custom markers"""
    config.addinivalue_line("markers", "unit: mark test as a unit test")
    config.addinivalue_line("markers", "integration: mark test as an integration test")
    config.addinivalue_line("markers", "slow: mark test as slow running")


def pytest_collection_modifyitems(config, items):
    """Modify test collection"""
    for item in items:
        # Add unit marker to all tests by default
        if "integration" not in item.keywords and "slow" not in item.keywords:
            item.add_marker(pytest.mark.unit)

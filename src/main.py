import datetime
import logging
import os
import sqlite3
import time
import uuid
from pathlib import Path
from typing import Optional

import jwt
from fastapi import FastAPI, Header, HTTPException, Request
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field

logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="DevOps API", version="1.0.0", description="Microservicio con seguridad JWT y API Key"
)

# Configuracion desde entorno o valores por defecto
API_KEY_REQUIRED = os.getenv("API_KEY", "2f5ae96c-b558-4c7b-a590-a501ae1c3f6c")
SECRET_KEY = os.getenv("SECRET_KEY", "devops-secret")
JWT_EXPIRATION_SECONDS = 3600
REPLAY_STORE_PATH = Path(os.getenv("REPLAY_STORE_PATH", "data/replay_store.db"))

REPLAY_STORE_PATH.parent.mkdir(parents=True, exist_ok=True)

# Token type returned on login responses
TOKEN_TYPE = os.getenv("TOKEN_TYPE", "bearer")


def get_replay_store_connection():
    """Crear conexion SQLite para almacenamiento de replay"""
    connection = sqlite3.connect(str(REPLAY_STORE_PATH), timeout=10)
    connection.execute("PRAGMA journal_mode=WAL;")
    connection.execute("PRAGMA synchronous=NORMAL;")
    return connection


def initialize_replay_store():
    """Crear la tabla usada para rastrear JWT ya consumidos"""
    with get_replay_store_connection() as connection:
        connection.execute(
            """
            CREATE TABLE IF NOT EXISTS used_tokens (
                token TEXT PRIMARY KEY,
                used_at INTEGER NOT NULL,
                expires_at INTEGER NOT NULL
            )
            """
        )


initialize_replay_store()


class LoginRequest(BaseModel):
    """Modelo de request para generar JWT"""

    api_key: str = Field(..., description="API Key for authentication")


class LoginResponse(BaseModel):
    """Modelo de respuesta para JWT"""

    access_token: str = Field(..., description="JWT token for API requests")
    token_type: str = Field(default="bearer", description="Token type")
    expires_in: int = Field(default=3600, description="Token expiration time in seconds")


class MessageRequest(BaseModel):
    message: str = Field(..., min_length=1)
    to: str = Field(..., min_length=1)
    to_field: str = Field(..., alias="from", min_length=1)
    timeToLifeSec: int = Field(..., ge=1, le=3600)


class MessageResponse(BaseModel):
    message: str


def generate_jwt_token() -> str:
    """Generar un JWT unico para la transaccion"""
    now = datetime.datetime.now(datetime.timezone.utc)
    payload = {
        "user": "api_client",
        "exp": now + datetime.timedelta(seconds=JWT_EXPIRATION_SECONDS),
        "iat": now,
        "jti": str(uuid.uuid4()),
    }
    token = jwt.encode(payload, SECRET_KEY, algorithm="HS256")
    logger.info(f"JWT token generated for transaction with jti={payload['jti']}")
    return token


def cleanup_expired_tokens():
    """Eliminar tokens expirados del cache used_tokens"""
    current_time = int(time.time())
    expired_count = 0
    with get_replay_store_connection() as connection:
        cursor = connection.execute(
            "DELETE FROM used_tokens WHERE expires_at <= ?", (current_time,)
        )
        expired_count = cursor.rowcount if cursor.rowcount != -1 else 0
    if expired_count:
        logger.info(f"Cleaned up {expired_count} expired tokens from replay store")


def is_token_reused(token: str) -> bool:
    """Verificar si un JWT ya fue usado en algun nodo."""
    with get_replay_store_connection() as connection:
        cursor = connection.execute("SELECT 1 FROM used_tokens WHERE token = ? LIMIT 1", (token,))
        return cursor.fetchone() is not None


def mark_token_used(token: str, expires_at: int) -> None:
    """Persistir un JWT como ya usado."""
    used_at = int(time.time())
    with get_replay_store_connection() as connection:
        connection.execute(
            "INSERT OR IGNORE INTO used_tokens (token, used_at, expires_at) VALUES (?, ?, ?)",
            (token, used_at, expires_at),
        )


def validate_jwt_token(token: Optional[str]) -> bool:
    """
    Validar token JWT desde el header de la request

    Args:
        token: token JWT a validar
    """
    if not token:
        logger.warning("Missing JWT token in request")
        return False

    if is_token_reused(token):
        logger.warning("JWT token already used in previous transaction")
        return False
    try:
        jwt.decode(token, SECRET_KEY, algorithms=["HS256"])
        logger.info("JWT token validated successfully")
        return True
    except jwt.ExpiredSignatureError:
        logger.error("JWT token has expired")
        return False
    except jwt.InvalidTokenError as e:
        logger.error(f"Invalid JWT token: {str(e)}")
        return False


@app.get("/health", tags=["Health"])
async def health_check():
    """Endpoint de salud para el load balancer"""
    return {"status": "healthy"}


@app.post("/auth/login", tags=["Authentication"], response_model=LoginResponse)
async def login(request_data: LoginRequest):
    """
    Generar endpoint de JWT

    Requiere:
    - api_key: API key valida

    Retorna:
    - access_token: token JWT para usar en header X-JWT-KWY
    - token_type: bearer
    - expires_in: segundos de expiracion (3600)
    """
    if request_data.api_key != API_KEY_REQUIRED:
        logger.warning(f"Invalid API Key attempt: {request_data.api_key}")
        raise HTTPException(status_code=403, detail="Invalid API Key")

    token = generate_jwt_token()
    logger.info("JWT token generated via /auth/login endpoint")

    return LoginResponse(
        access_token=token, token_type=TOKEN_TYPE, expires_in=JWT_EXPIRATION_SECONDS
    )


@app.api_route("/DevOps", methods=["POST", "GET", "PUT", "DELETE", "PATCH", "HEAD", "OPTIONS"])
async def devops_endpoint(
    request: Request,
    x_parse_rest_api_key: Optional[str] = Header(None),
    x_jwt_kwy: Optional[str] = Header(None),
):
    """
    Endpoint DevOps

    Solo POST permitido. Requiere:
    - header X-Parse-REST-API-Key con API key valida
    - header X-JWT-KWY con token JWT valido
    """
    if request.method != "POST":
        logger.warning(f"Rejected {request.method} request to /DevOps")
        return JSONResponse(content="ERROR", status_code=405)

    if not x_parse_rest_api_key or x_parse_rest_api_key != API_KEY_REQUIRED:
        logger.warning(f"Invalid API Key attempt: {x_parse_rest_api_key}")
        raise HTTPException(status_code=403, detail="Invalid or missing API Key")

    if not validate_jwt_token(x_jwt_kwy):
        logger.warning("JWT validation failed")
        raise HTTPException(status_code=401, detail="Invalid or missing JWT token")

    cleanup_expired_tokens()

    if x_jwt_kwy is None:
        logger.warning("Missing JWT token when checking for reuse")
        raise HTTPException(status_code=401, detail="Invalid or missing JWT token")

    if is_token_reused(x_jwt_kwy):
        logger.warning(
            "JWT token reuse attempt detected - token already used in previous transaction"
        )
        raise HTTPException(
            status_code=401,
            detail="JWT token has already been used in a previous transaction. Use a unique JWT for each transaction.",
        )

    decoded_token = jwt.decode(x_jwt_kwy, SECRET_KEY, algorithms=["HS256"])
    expires_at = int(decoded_token["exp"])
    mark_token_used(x_jwt_kwy, expires_at)
    logger.info("JWT token marked as used for transaction in shared replay store")

    try:
        data = await request.json()
        payload = MessageRequest(**data)
    except ValueError as e:
        logger.error(f"Invalid JSON payload: {str(e)}")
        raise HTTPException(status_code=400, detail="Invalid JSON payload") from e
    except Exception as e:
        logger.error(f"Validation error: {str(e)}")
        raise HTTPException(status_code=422, detail=f"Validation error: {str(e)}") from e

    response_data = MessageResponse(message=f"Hello {payload.to} your message will be sent")

    logger.info(f"Request processed successfully for {payload.to}")

    return JSONResponse(content=response_data.model_dump(), status_code=200)

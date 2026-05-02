import pytest
import jwt
import datetime
import time
import os

from fastapi import HTTPException

# Importar la aplicacion y sus funciones
import sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from main import (
    generate_jwt_token,
    validate_jwt_token,
    is_token_reused,
    mark_token_used,
    cleanup_expired_tokens,
    LoginRequest,
    LoginResponse,
    MessageRequest,
    MessageResponse,
    API_KEY_REQUIRED,
    SECRET_KEY,
    JWT_EXPIRATION_SECONDS
)


# ===== PRUEBAS DE FUNCIONES DE JWT =====

class TestJWTGeneration:
    """Pruebas para generacion de tokens JWT"""
    
    def test_generate_jwt_token_returns_string(self):
        """Verificar que generate_jwt_token retorna un string"""
        token = generate_jwt_token()
        assert isinstance(token, str)
        assert len(token) > 0
    
    def test_generate_jwt_token_is_valid(self):
        """Verificar que el token generado es valido"""
        token = generate_jwt_token()
        decoded = jwt.decode(token, SECRET_KEY, algorithms=["HS256"])
        assert decoded["user"] == "api_client"
        assert "exp" in decoded
        assert "iat" in decoded
        assert "jti" in decoded
    
    def test_generate_jwt_token_has_unique_jti(self):
        """Verificar que cada token generado tiene un jti unico"""
        token1 = generate_jwt_token()
        token2 = generate_jwt_token()
        
        decoded1 = jwt.decode(token1, SECRET_KEY, algorithms=["HS256"])
        decoded2 = jwt.decode(token2, SECRET_KEY, algorithms=["HS256"])
        
        assert decoded1["jti"] != decoded2["jti"]
    
    def test_generate_jwt_token_expiration(self):
        """Verificar que el token tiene duracion correcta"""
        now = datetime.datetime.now(datetime.timezone.utc)
        token = generate_jwt_token()
        decoded = jwt.decode(token, SECRET_KEY, algorithms=["HS256"])
        
        exp_time = datetime.datetime.fromtimestamp(decoded["exp"])
        duration = (exp_time - now).total_seconds()
        
        # Permitir 5 segundos de variacion
        assert JWT_EXPIRATION_SECONDS - 5 < duration < JWT_EXPIRATION_SECONDS + 5


class TestJWTValidation:
    """Pruebas para validacion de tokens JWT"""
    
    def test_validate_valid_jwt_token(self, valid_jwt_token):
        """Verificar que un JWT valido es aceptado"""
        assert validate_jwt_token(valid_jwt_token) is True
    
    def test_validate_missing_jwt_token(self):
        """Verificar que token ausente es rechazado"""
        assert validate_jwt_token(None) is False
        assert validate_jwt_token("") is False
    
    def test_validate_expired_jwt_token(self, expired_jwt_token):
        """Verificar que un JWT expirado es rechazado"""
        assert validate_jwt_token(expired_jwt_token) is False
    
    def test_validate_invalid_jwt_token(self, invalid_jwt_token):
        """Verificar que un JWT con firma invalida es rechazado"""
        assert validate_jwt_token(invalid_jwt_token) is False
    
    def test_validate_malformed_jwt_token(self):
        """Verificar que un JWT malformado es rechazado"""
        assert validate_jwt_token("not.a.valid.token") is False
        assert validate_jwt_token("invalid") is False


# ===== PRUEBAS DE PREVENCION DE REPLAY =====

class TestReplayPrevention:
    """Pruebas para prevencion de ataque de replay"""
    
    def test_mark_and_check_token_used(self, valid_jwt_token):
        """Verificar que un token puede ser marcado como usado"""
        expires_at = int(time.time()) + JWT_EXPIRATION_SECONDS
        
        assert is_token_reused(valid_jwt_token) is False
        mark_token_used(valid_jwt_token, expires_at)
        assert is_token_reused(valid_jwt_token) is True
    
    def test_same_token_cannot_be_used_twice(self, valid_jwt_token):
        """Verificar que el mismo token no puede ser usado dos veces"""
        expires_at = int(time.time()) + JWT_EXPIRATION_SECONDS
        
        mark_token_used(valid_jwt_token, expires_at)
        assert is_token_reused(valid_jwt_token) is True
        
        # Intentar marcar nuevamente no debe causar error
        mark_token_used(valid_jwt_token, expires_at)
        assert is_token_reused(valid_jwt_token) is True
    
    def test_different_tokens_are_tracked_separately(self):
        """Verificar que tokens diferentes son rastreados por separado"""
        token1 = generate_jwt_token()
        token2 = generate_jwt_token()
        
        expires_at = int(time.time()) + JWT_EXPIRATION_SECONDS
        
        mark_token_used(token1, expires_at)
        
        assert is_token_reused(token1) is True
        assert is_token_reused(token2) is False
    
    def test_cleanup_expired_tokens(self):
        """Verificar que tokens expirados son limpiados"""
        token1 = generate_jwt_token()
        token2 = generate_jwt_token()
        
        # Marcar token1 como expirado hace tiempo
        mark_token_used(token1, int(time.time()) - 1000)
        # Marcar token2 con expiracion futura
        mark_token_used(token2, int(time.time()) + JWT_EXPIRATION_SECONDS)
        
        assert is_token_reused(token1) is True
        assert is_token_reused(token2) is True
        
        # Limpiar tokens expirados
        cleanup_expired_tokens()
        
        assert is_token_reused(token1) is False
        assert is_token_reused(token2) is True


# ===== PRUEBAS DE MODELOS PYDANTIC =====

class TestPydanticModels:
    """Pruebas para validacion de modelos"""
    
    def test_login_request_valid(self):
        """Verificar que LoginRequest valida correctamente"""
        request = LoginRequest(api_key="test-key-123")
        assert request.api_key == "test-key-123"
    
    def test_login_response_structure(self):
        """Verificar estructura de LoginResponse"""
        response = LoginResponse(
            access_token="token123",
            token_type="bearer",
            expires_in=3600
        )
        assert response.access_token == "token123"
        assert response.token_type == "bearer"
        assert response.expires_in == 3600
    
    def test_message_request_valid(self):
        """Verificar que MessageRequest valida correctamente"""
        data = {
            "message": "Test message",
            "to": "user@example.com",
            "from": "system@example.com",
            "timeToLifeSec": 1800
        }
        request = MessageRequest(**data)
        assert request.message == "Test message"
        assert request.to == "user@example.com"
        assert request.to_field == "system@example.com"
        assert request.timeToLifeSec == 1800
    
    def test_message_request_invalid_empty_message(self):
        """Verificar que MessageRequest rechaza mensaje vacio"""
        data = {
            "message": "",
            "to": "user@example.com",
            "from": "system@example.com",
            "timeToLifeSec": 1800
        }
        with pytest.raises(ValueError):
            MessageRequest(**data)
    
    def test_message_request_invalid_ttl(self):
        """Verificar que MessageRequest valida timeToLifeSec"""
        # TTL muy bajo
        data = {
            "message": "Test",
            "to": "user@example.com",
            "from": "system@example.com",
            "timeToLifeSec": 0
        }
        with pytest.raises(ValueError):
            MessageRequest(**data)
        
        # TTL muy alto
        data["timeToLifeSec"] = 3601
        with pytest.raises(ValueError):
            MessageRequest(**data)


# ===== PRUEBAS DE ENDPOINTS =====

class TestHealthEndpoint:
    """Pruebas para el endpoint /health"""
    
    def test_health_check_returns_200(self, client):
        """Verificar que /health retorna 200"""
        response = client.get("/health")
        assert response.status_code == 200
    
    def test_health_check_returns_healthy_status(self, client):
        """Verificar que /health retorna status healthy"""
        response = client.get("/health")
        assert response.json() == {"status": "healthy"}


class TestLoginEndpoint:
    """Pruebas para el endpoint POST /auth/login"""
    
    def test_login_with_valid_api_key(self, client, valid_api_key):
        """Verificar login con API key valida"""
        response = client.post(
            "/auth/login",
            json={"api_key": valid_api_key}
        )
        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data
        assert data["token_type"] == "bearer"
        assert data["expires_in"] == JWT_EXPIRATION_SECONDS
    
    def test_login_returns_valid_jwt(self, client, valid_api_key):
        """Verificar que login retorna un JWT valido"""
        response = client.post(
            "/auth/login",
            json={"api_key": valid_api_key}
        )
        token = response.json()["access_token"]
        
        # Decodificar y verificar
        decoded = jwt.decode(token, SECRET_KEY, algorithms=["HS256"])
        assert decoded["user"] == "api_client"
        assert "jti" in decoded
        assert "exp" in decoded
        assert "iat" in decoded
    
    def test_login_with_invalid_api_key(self, client, invalid_api_key):
        """Verificar login con API key invalida"""
        response = client.post(
            "/auth/login",
            json={"api_key": invalid_api_key}
        )
        assert response.status_code == 403
        assert "Invalid API Key" in response.json()["detail"]
    
    def test_login_without_api_key(self, client):
        """Verificar login sin API key"""
        response = client.post("/auth/login", json={})
        assert response.status_code == 422  # Validacion fallida
    
    def test_multiple_logins_return_different_tokens(self, client, valid_api_key):
        """Verificar que multiples logins retornan tokens diferentes"""
        response1 = client.post(
            "/auth/login",
            json={"api_key": valid_api_key}
        )
        response2 = client.post(
            "/auth/login",
            json={"api_key": valid_api_key}
        )
        
        token1 = response1.json()["access_token"]
        token2 = response2.json()["access_token"]
        
        assert token1 != token2


class TestDevOpsEndpoint:
    """Pruebas para el endpoint /DevOps"""
    
    def test_devops_post_with_valid_credentials(self, client, headers_with_valid_credentials):
        """Verificar POST /DevOps con credenciales validas"""
        payload = {
            "message": "Test message",
            "to": "user@example.com",
            "from": "system@example.com",
            "timeToLifeSec": 1800
        }
        response = client.post(
            "/DevOps",
            json=payload,
            headers=headers_with_valid_credentials
        )
        assert response.status_code == 200
        data = response.json()
        assert "Hello user@example.com your message will be sent" in data["message"]
    
    def test_devops_get_not_allowed(self, client, headers_with_valid_credentials):
        """Verificar que GET /DevOps no es permitido"""
        response = client.get(
            "/DevOps",
            headers=headers_with_valid_credentials
        )
        assert response.status_code == 405
    
    def test_devops_put_not_allowed(self, client, headers_with_valid_credentials):
        """Verificar que PUT /DevOps no es permitido"""
        response = client.put(
            "/DevOps",
            json={"message": "test"},
            headers=headers_with_valid_credentials
        )
        assert response.status_code == 405
    
    def test_devops_delete_not_allowed(self, client, headers_with_valid_credentials):
        """Verificar que DELETE /DevOps no es permitido"""
        response = client.delete(
            "/DevOps",
            headers=headers_with_valid_credentials
        )
        assert response.status_code == 405
    
    def test_devops_missing_api_key(self, client, headers_missing_api_key):
        """Verificar que POST /DevOps requiere API Key"""
        payload = {
            "message": "Test",
            "to": "user@example.com",
            "from": "system@example.com",
            "timeToLifeSec": 1800
        }
        response = client.post(
            "/DevOps",
            json=payload,
            headers=headers_missing_api_key
        )
        assert response.status_code == 403
    
    def test_devops_invalid_api_key(self, client, headers_invalid_api_key):
        """Verificar que POST /DevOps rechaza API Key invalida"""
        payload = {
            "message": "Test",
            "to": "user@example.com",
            "from": "system@example.com",
            "timeToLifeSec": 1800
        }
        response = client.post(
            "/DevOps",
            json=payload,
            headers=headers_invalid_api_key
        )
        assert response.status_code == 403
    
    def test_devops_missing_jwt_token(self, client, headers_missing_jwt):
        """Verificar que POST /DevOps requiere JWT"""
        payload = {
            "message": "Test",
            "to": "user@example.com",
            "from": "system@example.com",
            "timeToLifeSec": 1800
        }
        response = client.post(
            "/DevOps",
            json=payload,
            headers=headers_missing_jwt
        )
        assert response.status_code == 401
    
    def test_devops_invalid_jwt_token(self, client, valid_api_key, invalid_jwt_token):
        """Verificar que POST /DevOps rechaza JWT invalido"""
        payload = {
            "message": "Test",
            "to": "user@example.com",
            "from": "system@example.com",
            "timeToLifeSec": 1800
        }
        headers = {
            "X-Parse-REST-API-Key": valid_api_key,
            "X-JWT-KWY": invalid_jwt_token,
            "Content-Type": "application/json"
        }
        response = client.post(
            "/DevOps",
            json=payload,
            headers=headers
        )
        assert response.status_code == 401
    
    def test_devops_expired_jwt_token(self, client, headers_expired_jwt):
        """Verificar que POST /DevOps rechaza JWT expirado"""
        payload = {
            "message": "Test",
            "to": "user@example.com",
            "from": "system@example.com",
            "timeToLifeSec": 1800
        }
        response = client.post(
            "/DevOps",
            json=payload,
            headers=headers_expired_jwt
        )
        assert response.status_code == 401
    
    def test_devops_token_reuse_prevention(self, client, headers_with_valid_credentials):
        """Verificar que reutilizar un token es rechazado"""
        payload = {
            "message": "Test",
            "to": "user@example.com",
            "from": "system@example.com",
            "timeToLifeSec": 1800
        }
        
        # Primer request con el token debe funcionar
        response1 = client.post(
            "/DevOps",
            json=payload,
            headers=headers_with_valid_credentials
        )
        assert response1.status_code == 200
        
        # Segundo request con el mismo token debe ser rechazado
        response2 = client.post(
            "/DevOps",
            json=payload,
            headers=headers_with_valid_credentials
        )
        assert response2.status_code == 401
        assert "already been used" in response2.json()["detail"]
    
    def test_devops_invalid_json_payload(self, client, headers_with_valid_credentials):
        """Verificar que JSON invalido es rechazado"""
        response = client.post(
            "/DevOps",
            data="not json",
            headers=headers_with_valid_credentials,
            content_type="application/json"
        )
        assert response.status_code == 400 or response.status_code == 422
    
    def test_devops_missing_required_fields(self, client, headers_with_valid_credentials):
        """Verificar que campos requeridos son validados"""
        payload = {"message": "Test"}  # Faltan to, from, timeToLifeSec
        
        response = client.post(
            "/DevOps",
            json=payload,
            headers=headers_with_valid_credentials
        )
        assert response.status_code == 422


# ===== PRUEBAS DE INTEGRACION =====

class TestIntegration:
    """Pruebas de integracion del flujo completo"""
    
    def test_complete_flow_login_and_devops(self, client, valid_api_key):
        """Verificar flujo completo: login -> /DevOps"""
        # Paso 1: Login
        login_response = client.post(
            "/auth/login",
            json={"api_key": valid_api_key}
        )
        assert login_response.status_code == 200
        token = login_response.json()["access_token"]
        
        # Paso 2: Usar token en /DevOps
        payload = {
            "message": "Integration test",
            "to": "user@example.com",
            "from": "system@example.com",
            "timeToLifeSec": 1800
        }
        devops_response = client.post(
            "/DevOps",
            json=payload,
            headers={
                "X-Parse-REST-API-Key": valid_api_key,
                "X-JWT-KWY": token
            }
        )
        assert devops_response.status_code == 200
    
    def test_multiple_requests_with_different_tokens(self, client, valid_api_key):
        """Verificar que se pueden hacer multiples requests con tokens diferentes"""
        payload = {
            "message": "Test",
            "to": "user@example.com",
            "from": "system@example.com",
            "timeToLifeSec": 1800
        }
        
        # Primer request con token 1
        login1 = client.post(
            "/auth/login",
            json={"api_key": valid_api_key}
        )
        token1 = login1.json()["access_token"]
        
        response1 = client.post(
            "/DevOps",
            json=payload,
            headers={
                "X-Parse-REST-API-Key": valid_api_key,
                "X-JWT-KWY": token1
            }
        )
        assert response1.status_code == 200
        
        # Segundo request con token 2
        login2 = client.post(
            "/auth/login",
            json={"api_key": valid_api_key}
        )
        token2 = login2.json()["access_token"]
        
        response2 = client.post(
            "/DevOps",
            json=payload,
            headers={
                "X-Parse-REST-API-Key": valid_api_key,
                "X-JWT-KWY": token2
            }
        )
        assert response2.status_code == 200
        
        # Ambos requests deben haber sido exitosos
        assert response1.json()["message"] == response2.json()["message"]


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--cov=src", "--cov-report=html"])

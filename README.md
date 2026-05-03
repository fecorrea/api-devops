# API DevOps - Microservicio Python

[![CI/CD Pipeline](https://dev.azure.com/fcf-devops/api-devops/_apis/build/status/azure-pipeline)](https://dev.azure.com/fcf-devops/)
[![Python 3.11+](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/downloads/)
[![Code Coverage](https://img.shields.io/badge/coverage-90%25-brightgreen.svg)](./htmlcov/index.html)

## 👤 Autor

Autor: Fressia Correa  
Email: fressiacorreaf@gmail.com  
Usuario Github: fecorrea

## 📋 Descripción del Proyecto

Microservicio REST seguro containerizado con FastAPI (en `src/main.py`), protegido con API Key y JWT, escalable horizontalmente con balanceador de carga Nginx, y con pipeline CI/CD completo. Cuenta con pruebas unitarias en `test/`. El proyecto incluye:

- `Dockerfile` para contenerizar la aplicación.
- `docker-compose.yml` para orquestación on-prem (junto con `infra/nginx.conf` para el balanceador NGINX).
- Infraestructura como código en `infra/` (Terraform) para despliegue en cloud.
- Un pipeline de CI/CD para Azure DevOps: `azure-pipeline.yml`.

### ✨ Características Principales

- ✅ **API REST Segura**: Validación de API Key y JWT en cada request
- ✅ **Containerización**: Docker multi-stage con optimización de seguridad
- ✅ **Alta Disponibilidad**: 2+ nodos con load balancer Nginx
- ✅ **Pipeline CI/CD**: GitHub Actions con Build, Test y Deploy automático
- ✅ **Pruebas Automatizadas**: 40+ test cases con cobertura >90%
- ✅ **Análisis Estático**: Pylint, Bandit, MyType, Ruff integrados
- ✅ **Escalabilidad Dinámica**: Docker Compose preparado para orquestación
- ✅ **Logging y Monitoreo**: JSON logging con structured data
- ✅ **Health Checks**: Endpoints de salud para load balancer
- ✅ **Documentación**: Swagger UI automático en `/docs`


## 📁 Estructura del Proyecto

```
azure-pipelines.yml               # Pipeline para despliegue en Cloud
docker-compose.yml                # Orquestación de contenedores
Dockerfile                        # Build de imagen
pyproject.toml                    # Configuración de herramientas
README.md                         # Este archivo
requirements.txt                  # Dependencias Python
.gitignore                        # Git ignore rules
infra/
  ├─ nginx.conf                   # Configuración del load balancer
  ├─ main.tf                      # Configuración de IaC con Terraform
  └─ (otros archivos de terraform)
src/
  └─ main.py                      # Aplicación FastAPI
test/
  ├─ conftest.py                  # Utils para uso en pruebas unitarias
  └─ test_main.py                 # Suite de pruebas unitarias
```

## 🚀 Quick Start


### Requisitos Previos

- Python >= 3.11 (local)
- Docker >= 20.10 (para contenerizar)
- Docker Compose >= 2.0 (para orquestar on-prem)
- Terraform >= 1.15.1 (para despliegues cloud)
- Azure CLI y permisos si se va a usar el pipeline/ACR/App Service
- Git

### 1️⃣ Clonar Repositorio

```bash
git clone https://github.com/fecorrea/api-devops.git
cd api-devops
```

### 2️⃣ Configuración del Ambiente en local

```bash
# Crear virtual environment (opcional para desarrollo local)
python -m venv venv
source venv/bin/activate  # En Windows: venv\Scripts\activate
python -m pip install --upgrade pip
pip install -r requirements.txt
# Ejecutar las pruebas unitarias
python -m pytest test/
# Ejecutar la aplicación localmente (módulo `src/main.py`)
python -m src.main
```

## 📊 Orquestación con Docker Compose

Este repositorio incluye `docker-compose.yml` en la raíz y la configuración de NGINX en `infra/nginx.conf`. Los pasos básicos para levantar la pila on-prem son:

1. (Opcional) Editar `infra/nginx.conf` para apuntar al puerto/servicio correcto.

2. Levantar con docker-compose (desde la raíz del repo):

```
docker-compose up --build -d
```

3. Verificar los contenedores y logs:

```
docker-compose ps
docker-compose logs -f
```

4. La entrada del balanceador (NGINX) expondrá la aplicación. Por defecto la app escucha en el puerto 8000 dentro del contenedor; NGINX hace el proxy desde el puerto 80 (revisar `infra/nginx.conf`). Se puede probar con el comando:

```bash
# Health check
curl http://localhost/health
```

### Servicios

**app-node-1 & app-node-2**
- FastAPI microservice
- Expuestos en :8001 y :8002 (internamente :8000)
- Health checks cada 10s
- Auto-restart

**balancer (Nginx)**
- Load balancer con least_conn
- Rate limiting: 100 req/s
- Logs centralizados
- Health checks

### 📝 Logging y Monitoreo


### Structured Logging
```python
logger.info("Request processed", extra={
    "user": "api_client",
    "endpoint": "/DevOps",
    "status": 200,
    "duration_ms": 45
})
```

### Logs Centralizados
```bash
# Ver logs en tiempo real
docker-compose logs -f app-node-1

# Logs filtrados
docker-compose logs app-node-1 | grep ERROR


# Guardar logs
docker-compose logs > app.log
```

## 📋 Especificaciones del Endpoint

#### Request
```json
{
  "message": "This is a test",
  "to": "Juan Perez",
  "from": "Rita Asturia",
  "timeToLifeSec": 45
}
```


#### Headers
```
X-Parse-REST-API-Key: <-reemplazar-api-key->
X-JWT-KWY: <-reemplazar-JWT->
Content-Type: application/json
```

#### Response (200 OK)
```json
{
  "message": "Hello Juan Perez your message will be sent"
}
```

Header de respuesta:
```
X-JWT-KWY: eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
```

#### Otros Métodos HTTP
Cualquier método diferente a POST devuelve:
```
Status: 405 Method Not Allowed
Content: "ERROR"
```

### 4️⃣ Probar el Endpoint

```bash
# Obtener JWT desde el endpoint de autenticación
JWT=$(curl -s -X POST http://localhost:8000/auth/login \
  -H "Content-Type: application/json" \
  -d '{"api_key":"${api-key}"}' | jq -r '.access_token')

# Realizar request al endpoint protegido
curl -X POST \
  -H "X-Parse-REST-API-Key: ${api-key}" \
  -H "X-JWT-KWY: ${JWT}" \
  -H "Content-Type: application/json" \
  -d '{
    "message": "This is a test",
    "to": "Juan Perez",
    "from": "Rita Asturia",
    "timeToLifeSec": 45
  }' \
  http://localhost/DevOps
```

**Respuesta esperada:**
```json
{
  "message": "Hello Juan Perez your message will be sent"
}
```

### Variables/Secretos en Cloud
------------------

Para despliegues (Azure o producción) asegúrate de definir las variables y secretos requeridos. En `azure-pipeline.yml` se referencian variables como:

- AZURE_CONTAINER_REGISTRY_NAME
- AZURE_RESOURCE_GROUP
- azureSubscription
- STAGING_APP_SERVICE_NAME
- PRODUCTION_APP_SERVICE_NAME
- api-key, secret-key (almacenadas en un variable group `api-devops-secrets`)

### Cloud (Terraform & Azure DevOps pipeline)
----------------------------------------

El directorio `infra/` contiene la configuración de Terraform usada para desplegar en cloud (recursos, outputs y variables). El pipeline `azure-pipeline.yml` realiza las siguientes etapas principales:

- Build & Test: instala dependencias, ejecuta pytest, publica reportes y chequeos (black, ruff, mypy, bandit).
- Docker Build & Push: construye la imagen Docker y la sube a Azure Container Registry.
- Deploy Staging / Production: despliega la imagen a Azure App Service según la rama (develop -> staging, main -> production) y configura variables de aplicación.

Para usar el pipeline en Azure DevOps:

1. Asegúrate de crear un Variable Group en el proyecto llamado `api-devops-secrets` con las variables `api-key`, `secret-key`, `AZURE_CONTAINER_REGISTRY_NAME`, `AZURE_RESOURCE_GROUP`, etc., o vincular los secretos necesarios.

2. Configura una Service Connection para Azure (nombre referido en `azure-pipeline.yml` como `api-devops-acr` o la variable `dockerRegistryServiceConnection`).

3. Ajusta los nombres de App Service (`STAGING_APP_SERVICE_NAME` y `PRODUCTION_APP_SERVICE_NAME`) y la suscripción (`azureSubscription`) en variables de pipeline.

Comandos útiles para Terraform (desde `infra/`)

```
cd infra
terraform init
terraform plan -out tfplan
terraform apply tfplan
```

### En el Pipeline
El pipeline CI/CD ejecuta automáticamente:
- Ruff linting y format check
- MyType type validation
- Bandit security scan
- Coverage report (mínimo 85%)
- Tests automatizados

## 🧪 Testing

### Ejecutar Tests Locales

```bash
# Instalar dependencias de desarrollo
pip install -r requirements.txt

# Ejecutar tests
pytest test/ -v

# Con cobertura
pytest test/ --cov=src --cov-report=html

# Tests específicos
pytest test/test_main.py::TestDevOpsPostSuccess::test_post_response_format -v
```

### Coverage Report
```bash
pytest --cov=src --cov-report=html
open htmlcov/index.html
```


### Tests Incluidos
- ✅ Health check endpoint
- ✅ POST requests exitosos
- ✅ Validación de métodos HTTP
- ✅ Validación de API Key
- ✅ Validación de JWT
- ✅ Validación de payload JSON
- ✅ Funciones de JWT helper
- ✅ +35 casos de prueba

## 🔍 Análisis Estático de Código

### Local

```bash
# Ruff - Linting
ruff check src/ test/

# Black - Formateo
black src/ test/

# isort - Import sorting
isort src/ test/

# MyType - Type checking
mypy src/

# Bandit - Security analysis
bandit -r src/

# Pylint - Code quality
pylint src/ test/
```

## 🔐 Seguridad

### API Key
- **Header requerido**: `X-Parse-REST-API-Key`
- **Valor**: <-reemplazar-api-key->
- **Validación**: Obligatorio en cada request

### JWT (JSON Web Tokens)
- **Header requerido**: `X-JWT-KWY`
- **Algoritmo**: HS256
- **Expiración**: 3600 segundos (1 hora)
- **Generación**: Los tokens se obtienen mediante `POST /auth/login` enviando la `API_KEY`. El endpoint `POST /DevOps` no emite nuevos tokens.

### Validaciones Adicionales
- Content-Type: `application/json`
- Validación de campos requeridos
- Límites de valores (ej: timeToLifeSec 1-3600)
- Rate limiting en Nginx (100 req/s)
- Headers de seguridad (CSP, XSS, Clickjacking)

### Notas de Seguridad

- No incluyas secretos en texto plano en el repositorio.
- Usa Azure Key Vault o Variable Groups protegidos para las claves.
- El pipeline ya ejecuta un escaneo básico con Bandit y publica el informe.

## 📚 Documentación API

### Swagger UI
```
http://localhost:8000/docs
```

### OpenAPI Schema
```
http://localhost:8000/openapi.json
```

### Notas importantes
---------------------------

- Actualmente se usa sqlite para que múltiples instancias conozcan el estado de los jwt usados ya que se requiere que un jwt se único por cada transacción, por lo que se usa un volúmen persistente con este archivo sqlite. Para un entorno real se recomienda el uso de caché con redis o una base de datos más robusta.
- En entorno on-prem no se tiene configurado un certificado SSL por lo cual sólo se permite el acceso por http, mientras que en cloud al estar deplegado en App Service sólo se permite el acceso por https.
- En cloud se desplegó en app service, para el ambiente de staging un solo nodo mientras que para producción se desplegaron 2 instancias, no se coloca el autoescalamiento por temas de costos, pero es configurable tanto por terraform como por UI.

---

## ✅ Checklist de Requisitos Cumplidos


### Desarrollo del Microservicio
- [x] Microservicio REST con endpoint `/DevOps`
- [x] Acepta POST con JSON específico
- [x] Responde con JSON correcto
- [x] Otros métodos retornan ERROR


### Seguridad
- [x] API Key en headers (X-Parse-REST-API-Key)
- [x] JWT único por transacción (X-JWT-KWY)
- [x] Validación de ambos en cada request


### Despliegue
- [x] Containerizado con Docker
- [x] Dockerfile multi-stage optimizado
- [x] Balanceador de carga Nginx
- [x] 2+ nodos configurados
- [x] Health checks implementados


### Pipeline CI/CD
- [x] Azure DevOps Pipeline configurado
- [x] Etapas: Build, Test y Deploy
- [x] Master deploya a producción automáticamente
- [x] Soporte para ejecuciones bajo demanda
- [x] Gestión de dependencias con pip


### Pruebas y Análisis
- [x] 35+ casos de prueba
- [x] Cobertura > 95%
- [x] Análisis estático (Black, Ruff, Bandit, MyType)
- [x] TDD aplicado
- [x] pytest + coverage configurado


### DevOps Best Practices
- [x] Versionado en GitHub
- [x] .gitignore configurado
- [x] pyproject.toml con metadata
- [x] Docker Compose multi-servicio
- [x] Logging estructurado
- [x] Seguridad en Dockerfile
- [x] Rate limiting en load balancer
- [x] Headers de seguridad
- [x] Health checks todo el stack


# nvidia_ai_premvp

Pre-MVP del cliente IA para **Scr4per v3** (NAAT OSINT).

Expone dos endpoints HTTP sobre FastAPI que proxean requests hacia **NVIDIA NIM**
usando el endpoint OpenAI-compatible `/chat/completions`.

> **Alcance pre-MVP**: sin DB, Gateway, Auth, Playwright ni Scrapling.

---

## Estructura

```
nvidia_ai_premvp/
├── app/
│   ├── main.py              # FastAPI app + lifespan
│   ├── config.py            # pydantic-settings
│   ├── api/
│   │   ├── routes_health.py # GET /health
│   │   └── routes_chat.py   # POST /chat
│   └── nvidia/
│       └── client.py        # Cliente httpx async para NVIDIA NIM
├── requirements.txt
├── .env.example
└── README.md
```

---

## Setup

### 1. Crear entorno virtual

```bash
python -m venv .venv
source .venv/bin/activate
```

### 2. Instalar dependencias

```bash
pip install -r requirements.txt
```

### 3. Configurar variables de entorno

```bash
cp .env.example .env
# Edita .env y pon tu NVIDIA_API_KEY real
```

| Variable | Obligatoria | Descripción |
|---|---|---|
| `NVIDIA_API_KEY` | ✅ | API key de [build.nvidia.com](https://build.nvidia.com) |
| `NVIDIA_BASE_URL` | No | `https://integrate.api.nvidia.com/v1` |
| `NVIDIA_DEFAULT_MODEL` | No | `meta/llama-3.3-70b-instruct` |
| `NVIDIA_TIMEOUT_SECONDS` | No | `30` |
| `NVIDIA_MAX_TOKENS` | No | `1024` |
| `NVIDIA_TEMPERATURE` | No | `0.2` |

---

## Levantar el servicio

```bash
uvicorn app.main:app --reload --port 8010
```

El servidor queda disponible en `http://localhost:8010`.

---

## Endpoints

### GET /health

Verifica que el servicio está activo.

```bash
curl http://localhost:8010/health
```

Respuesta esperada:
```json
{"status": "ok", "service": "nvidia_ai_premvp"}
```

---

### POST /chat

Envía un mensaje al modelo de NVIDIA NIM.

```bash
curl -X POST http://localhost:8010/chat \
  -H "Content-Type: application/json" \
  -d '{"message": "Explica brevemente qué es OSINT.", "model": null}'
```

Respuesta esperada:
```json
{
  "reply": "OSINT (Open Source Intelligence) es la recopilación...",
  "model_used": "meta/llama-3.3-70b-instruct"
}
```

Para usar un modelo distinto al default:

```bash
curl -X POST http://localhost:8010/chat \
  -H "Content-Type: application/json" \
  -d '{"message": "¿Qué es un grafo de conocimiento?", "model": "meta/llama-3.1-8b-instruct"}'
```

---

## Documentación interactiva

Con el servidor activo, visita:

- Swagger UI: `http://localhost:8010/docs`
- ReDoc: `http://localhost:8010/redoc`

---

## Errores

Los errores HTTP de NVIDIA se re-lanzan sin exponer la API key:

| Código | Causa |
|---|---|
| 401 | API key inválida o expirada |
| 429 | Rate limit de NVIDIA |
| 504 | Timeout al llamar NVIDIA NIM |
| 502 | Error de red o respuesta inesperada |

---

## Notas de seguridad

- La `NVIDIA_API_KEY` nunca se loguea.
- No commitear `.env` con valores reales (agregar `.env` a `.gitignore`).

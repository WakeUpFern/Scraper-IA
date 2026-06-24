#!/usr/bin/env python3
"""
Punto de entrada para uvicorn.
Ejecutar desde /app (dentro del contenedor):
    uvicorn main:app --host 0.0.0.0 --port 8010 --reload
"""
from app.main import app  # noqa: F401 — re-export for uvicorn

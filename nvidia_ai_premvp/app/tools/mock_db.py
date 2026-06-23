"""
Simulación de base de datos en memoria para Scr4per v3.
Mantiene el estado de análisis, tool_runs y evidencias capturadas.
"""

from datetime import datetime
from typing import Any, Dict, List

# Almacenes globales en memoria
analyses: Dict[int, Dict[str, Any]] = {}
tool_runs: List[Dict[str, Any]] = []
raw_evidence: List[Dict[str, Any]] = []
identidades_observadas: List[Dict[str, Any]] = []
vinculos_sociales: List[Dict[str, Any]] = []
publicaciones: List[Dict[str, Any]] = []
comentarios: List[Dict[str, Any]] = []
graph_snapshots: List[Dict[str, Any]] = []


def init_analysis(id_analisis: int, id_usuario: int, id_caso: int | None, platform: str, target: str, limits: Dict[str, int]) -> Dict[str, Any]:
    """Inicializa el estado de un análisis."""
    analysis = {
        "id_analisis": id_analisis,
        "id_usuario": id_usuario,
        "id_caso": id_caso,
        "platform": platform,
        "username_or_url": target,
        "limits": limits,
        "status": "pending",
        "started_at": datetime.now().isoformat(),
        "finished_at": None,
        "error": None
    }
    analyses[id_analisis] = analysis
    return analysis


def get_analysis_status(id_analisis: int) -> Dict[str, Any]:
    """Obtiene el estado de un análisis o lanza KeyError si no existe."""
    if id_analisis not in analyses:
        raise KeyError(f"Análisis {id_analisis} no encontrado.")
    return analyses[id_analisis]


def update_analysis_status(id_analisis: int, status: str, error: str | None = None) -> None:
    """Actualiza el estado de un análisis."""
    if id_analisis in analyses:
        analyses[id_analisis]["status"] = status
        if error:
            analyses[id_analisis]["error"] = error
        if status in ("completed", "failed"):
            analyses[id_analisis]["finished_at"] = datetime.now().isoformat()


def add_tool_run(tool_run_data: Dict[str, Any]) -> Dict[str, Any]:
    """Registra una ejecución de herramienta (tool_run)."""
    # Auto-increment id
    new_id = len(tool_runs) + 1
    tool_run_data["id_tool_run"] = new_id
    tool_run_data["started_at"] = tool_run_data.get("started_at") or datetime.now().isoformat()
    tool_runs.append(tool_run_data)
    return tool_run_data


def get_tool_runs_for_analysis(id_analisis: int) -> List[Dict[str, Any]]:
    """Devuelve todos los tool_runs asociados a un análisis."""
    return [tr for tr in tool_runs if tr["id_analisis"] == id_analisis]


def add_raw_evidence(evidence_data: Dict[str, Any]) -> None:
    """Registra evidencia cruda obtenida por una herramienta."""
    new_id = len(raw_evidence) + 1
    evidence_data["id_raw_evidence"] = new_id
    evidence_data["observed_at"] = datetime.now().isoformat()
    raw_evidence.append(evidence_data)


def add_identidad_observada(identidad_data: Dict[str, Any]) -> None:
    """Registra una observación de identidad digital."""
    new_id = len(identidades_observadas) + 1
    identidad_data["id_identidad_observacion"] = new_id
    identidad_data["observed_at"] = datetime.now().isoformat()
    identidades_observadas.append(identidad_data)


def add_vinculo_social(vinculo_data: Dict[str, Any]) -> None:
    """Registra un vínculo social observado."""
    vinculos_sociales.append(vinculo_data)


def add_publicacion(pub_data: Dict[str, Any]) -> None:
    """Registra una publicación observada."""
    publicaciones.append(pub_data)


def add_comentario(com_data: Dict[str, Any]) -> None:
    """Registra un comentario observado."""
    comentarios.append(com_data)


def add_graph_snapshot(snapshot_data: Dict[str, Any]) -> None:
    """Registra un snapshot del grafo técnico."""
    new_id = len(graph_snapshots) + 1
    snapshot_data["id_graph_snapshot"] = new_id
    snapshot_data["created_at"] = datetime.now().isoformat()
    graph_snapshots.append(snapshot_data)

"""
Implementación real de la herramienta build_graph_from_analysis.
Consulta la base de datos real en PostgreSQL, genera el grafo técnico JSON y lo persiste en redes.graph_snapshot.
"""

import json
import logging
from datetime import datetime
from typing import List

from app.tools.base import BaseTool
from app.tools.schemas import BuildGraphInput, BuildGraphOutput, GraphNode, GraphEdge
from app.tools import mock_db
from app.runtime import db

logger = logging.getLogger(__name__)


class BuildGraphTool(BaseTool[BuildGraphInput, BuildGraphOutput]):
    """Herramienta real build_graph_from_analysis."""

    def __init__(self):
        super().__init__(
            name="build_graph_from_analysis",
            description="Genera el grafo técnico real en JSON a partir de las observaciones y vínculos persistidos en la base de datos.",
            input_model=BuildGraphInput,
            output_model=BuildGraphOutput
        )

    async def _run(self, id_analisis: int, id_usuario: int | None, input_data: BuildGraphInput) -> BuildGraphOutput:
        nodes: List[GraphNode] = []
        edges: List[GraphEdge] = []
        added_node_ids = set()

        # 1. Obtener identidades observadas
        identidades = await db.fetch(
            "SELECT nombre_publico_observado, username_observado, descripcion_observada FROM redes.identidad_observacion WHERE id_analisis = $1",
            id_analisis
        )
        for idx in identidades:
            u = idx["username_observado"]
            if u and u not in added_node_ids:
                nodes.append(GraphNode(
                    id=u,
                    label=idx["nombre_publico_observado"] or u,
                    type="identity",
                    metadata={"bio": idx["descripcion_observada"]}
                ))
                added_node_ids.add(u)

        # 2. Obtener publicaciones recopiladas
        publicaciones = await db.fetch(
            """
            SELECT p.identificador_externo, p.texto, i.username as author_username 
            FROM redes.publicacion p
            LEFT JOIN personas.identidad_digital i ON p.id_identidad_autor = i.id_identidad_digital
            WHERE p.id_analisis = $1
            """,
            id_analisis
        )
        for p in publicaciones:
            p_id = p["identificador_externo"]
            author = p["author_username"] or "unknown_author"
            
            if p_id and p_id not in added_node_ids:
                nodes.append(GraphNode(
                    id=p_id,
                    label=f"Post {p_id}",
                    type="post",
                    metadata={"content": p["texto"]}
                ))
                added_node_ids.add(p_id)
            
            if author:
                if author not in added_node_ids:
                    nodes.append(GraphNode(id=author, label=author, type="identity"))
                    added_node_ids.add(author)
                
                # Crear arista del autor al post
                edges.append(GraphEdge(
                    source=author,
                    target=p_id,
                    type="posted",
                    weight=5.0
                ))

        # 3. Obtener relaciones / vínculos sociales reales
        vinculos = await db.fetch(
            """
            SELECT i_orig.username as orig_user, i_dest.username as dest_user, tv.codigo as type_code, v.raw_json
            FROM redes.vinculo_social v
            JOIN personas.identidad_digital i_orig ON v.id_identidad_origen = i_orig.id_identidad_digital
            JOIN personas.identidad_digital i_dest ON v.id_identidad_destino = i_dest.id_identidad_digital
            JOIN redes.tipo_vinculo_social tv ON v.id_tipo_vinculo = tv.id_tipo_vinculo
            WHERE v.id_analisis = $1
            """,
            id_analisis
        )
        for v in vinculos:
            u_orig = v["orig_user"]
            u_dest = v["dest_user"]
            t_code = v["type_code"]
            
            # Asegurar que ambos nodos existan en el grafo
            for node_id in (u_orig, u_dest):
                if node_id and node_id not in added_node_ids:
                    nodes.append(GraphNode(id=node_id, label=node_id, type="identity"))
                    added_node_ids.add(node_id)
            
            # Peso de la relación
            weight = 1.0
            if t_code == "commented_on_post":
                weight = 3.0
            elif t_code == "liked_post":
                weight = 2.0
            
            if u_orig and u_dest:
                edges.append(GraphEdge(
                    source=u_orig,
                    target=u_dest,
                    type=t_code,
                    weight=weight
                ))

        result = BuildGraphOutput(
            analysis_id=id_analisis,
            nodes=nodes,
            edges=edges,
            observed_at=datetime.now().isoformat()
        )

        # Persistir snapshot en redes.graph_snapshot
        try:
            # Obtener id_caso si existe desde la tabla asociativa caso_analisis
            caso_row = await db.fetchrow("SELECT id_caso FROM casos.caso_analisis WHERE id_analisis = $1 LIMIT 1", id_analisis)
            id_caso = caso_row["id_caso"] if caso_row else None
            
            # Obtener id_usuario_ejecutor de la tabla de análisis
            analysis_row = await db.fetchrow("SELECT id_usuario_ejecutor FROM redes.analisis WHERE id_analisis = $1", id_analisis)
            id_user = analysis_row["id_usuario_ejecutor"] if (analysis_row and analysis_row.get("id_usuario_ejecutor")) else id_usuario
            
            await db.execute(
                """
                INSERT INTO redes.graph_snapshot 
                (id_analisis, id_caso, id_usuario, graph_scope, graph_json, metrics_json)
                VALUES ($1, $2, $3, $4, $5, $6)
                """,
                id_analisis, id_caso, id_user, "analysis", json.dumps(result.model_dump()), 
                json.dumps({"nodes_count": len(nodes), "edges_count": len(edges)})
            )
        except Exception as db_err:
            logger.error("Error guardando graph_snapshot en DB: %s", db_err)

        # Registrar en mock_db local por compatibilidad
        mock_db.add_graph_snapshot({
            "id_analisis": id_analisis,
            "graph_scope": "analysis",
            "nodes_count": len(nodes),
            "edges_count": len(edges),
            "raw_json": result.model_dump()
        })

        return result

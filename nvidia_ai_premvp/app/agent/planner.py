"""
Implementación del planificador autónomo (Planner Agent) de Scr4per v3.
Ejecuta un bucle ReAct con selección de herramientas dinámica usando NVIDIA NIM.
"""

import json
import logging
from typing import Any, Dict, List

from app.agent.prompts import SYSTEM_PROMPT
from app.nvidia.client import chat_completion
from app.tools.registry import get_tool, get_tools_for_openai

logger = logging.getLogger(__name__)


class ScraperAgentPlanner:
    """
    Planificador de adquisición inteligente.
    ponytail: mantiene el menor estado posible y delega las herramientas al Tool Registry.
    """

    def __init__(self, id_analisis: int, id_usuario: int, platform: str, username_or_url: str, limits: Dict[str, Any]):
        self.id_analisis = id_analisis
        self.id_usuario = id_usuario
        self.platform = platform
        self.username_or_url = username_or_url
        self.limits = limits
        self.max_tool_calls = 10

    async def run(self) -> Dict[str, Any]:
        """
        Ejecuta el bucle ReAct autónomo llamando a NIM e invocando herramientas.
        """
        logger.info("Iniciando bucle ReAct para analisis=%d, target=%s", self.id_analisis, self.username_or_url)

        # 1. Definir historial inicial de mensajes
        messages = [
            {"role": "system", "content": SYSTEM_PROMPT},
            {
                "role": "user",
                "content": (
                    f"Objetivo: Analizar la identidad '{self.username_or_url}' en la plataforma '{self.platform}'.\n"
                    f"Límites definidos por el analista:\n{json.dumps(self.limits, indent=2)}"
                )
            }
        ]

        tool_calls_count = 0
        final_reply = ""

        # 2. Bucle ReAct
        while tool_calls_count < self.max_tool_calls:
            # Obtener esquemas compatibles con OpenAI para el NIM
            openai_tools = get_tools_for_openai()

            logger.info("Llamando a NVIDIA NIM (bucle ReAct, paso %d/%d)...", tool_calls_count + 1, self.max_tool_calls)
            try:
                response = await chat_completion(message=messages, tools=openai_tools)
            except Exception as e:
                logger.error("Error en chat_completion con NIM: %s", e)
                final_reply = f"Error llamando al modelo de IA: {str(e)}"
                break

            choice_message = response["choices"][0]["message"]
            # ponytail: Asegurar formato compatible agregándolo al historial
            messages.append({
                "role": "assistant",
                "content": choice_message.get("content"),
                "tool_calls": choice_message.get("tool_calls")
            })

            tool_calls = choice_message.get("tool_calls")
            if not tool_calls:
                # El modelo decidió no llamar herramientas, finalizó el bucle
                logger.info("El agente decidió finalizar el bucle.")
                final_reply = choice_message.get("content") or "Adquisición completada por decisión del agente."
                break

            # Procesar las llamadas a herramientas solicitadas por el modelo
            for tool_call in tool_calls:
                tool_call_id = tool_call.get("id")
                function_data = tool_call.get("function", {})
                tool_name = function_data.get("name")
                raw_args = function_data.get("arguments", "{}")

                logger.info("Agente solicita ejecutar tool=%s con args=%s", tool_name, raw_args)

                # Parsear argumentos
                try:
                    args = json.loads(raw_args) if isinstance(raw_args, str) else raw_args
                except Exception as err:
                    logger.error("Error parseando argumentos JSON para tool=%s: %s", tool_name, err)
                    tool_result = {"status": "failed", "error": f"JSON parse error: {str(err)}"}
                else:
                    # Recuperar y ejecutar herramienta
                    tool = get_tool(tool_name)
                    if not tool:
                        logger.error("Herramienta solicitada no existe: %s", tool_name)
                        tool_result = {"status": "failed", "error": f"Tool '{tool_name}' not found."}
                    else:
                        try:
                            # Asegurar inyección de id_analisis y id_usuario si no vienen en args
                            args.setdefault("id_analisis", self.id_analisis)
                            args.setdefault("id_usuario", self.id_usuario)

                            # Validar que no violen los límites globales en tiempo de ejecución (ponytail: guardrail de seguridad)
                            if tool_name == "fetch_recent_posts":
                                args["limit"] = min(args.get("limit", self.limits.get("max_posts", 10)), self.limits.get("max_posts", 10))
                            elif tool_name == "fetch_post_comments_batch":
                                args["limit"] = min(args.get("limit", self.limits.get("max_comments_per_post", 50)), self.limits.get("max_comments_per_post", 50))
                            elif tool_name == "fetch_followers_batch":
                                args["limit"] = min(args.get("limit", self.limits.get("max_followers", 100)), self.limits.get("max_followers", 100))
                            elif tool_name == "fetch_following_batch":
                                args["limit"] = min(args.get("limit", self.limits.get("max_following", 100)), self.limits.get("max_following", 100))

                            tool_result = await tool.run(
                                id_analisis=self.id_analisis,
                                id_usuario=self.id_usuario,
                                raw_input=args
                            )
                        except Exception as exec_err:
                            logger.error("Error ejecutando tool=%s: %s", tool_name, exec_err)
                            tool_result = {"status": "failed", "error": str(exec_err)}

                # Guardar respuesta como mensaje de herramienta
                messages.append({
                    "role": "tool",
                    "tool_call_id": tool_call_id,
                    "name": tool_name,
                    "content": json.dumps(tool_result)
                })
                tool_calls_count += 1

                # Parar si superamos el máximo en medio de un lote de tool_calls
                if tool_calls_count >= self.max_tool_calls:
                    logger.warning("Límite máximo de tool_calls alcanzado durante la iteración.")
                    final_reply = "Bucle terminado debido al límite máximo de iteraciones alcanzado."
                    break

        return {
            "status": "completed",
            "final_reply": final_reply,
            "total_tool_calls": tool_calls_count,
            "steps": messages
        }

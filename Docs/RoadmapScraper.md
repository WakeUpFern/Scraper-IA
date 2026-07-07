# Roadmap propuesto para Scr4per v3.5


# Fase 1 — Modularización del scraper en tools

Esta es la primera fase grande. El objetivo no es meter más features, sino convertir el script actual en piezas reutilizables.

## 1.1 Crear estructura base

Estructura recomendada:

```txt
scr4per/
  app/
    main.py

    api/
      routes/
        health.py
        jobs.py
        tools.py
        graphs.py
        exports.py

    application/
      orchestrators/
        analysis_orchestrator.py
      runners/
        tool_runner.py
      registry/
        tool_registry.py

    domain/
      models/
        job.py
        tool_run.py
        target.py
        profile.py
        relationship.py
        engagement.py
        artifact.py
        graph.py
      enums/
        platform.py
        tool_status.py
        relationship_type.py

    tools/
      base.py
      facebook/
        validate_session.py
        fetch_profile_snapshot.py
        fetch_friends.py
        fetch_followers.py
        fetch_following.py
        fetch_photo_engagements.py
      instagram/
        validate_session.py
        fetch_profile_snapshot.py
        fetch_followers.py
        fetch_following.py
        fetch_post_engagements.py
      x/
        validate_session.py
        fetch_profile_snapshot.py
        fetch_followers.py
        fetch_following.py
        fetch_post_engagements.py
      common/
        normalize_target.py
        build_graph.py
        export_excel.py
        export_csv.py
        upload_artifacts.py

    infrastructure/
      browser/
        playwright_manager.py
        context_factory.py
      db/
        repositories/
          job_repository.py
          tool_run_repository.py
          identity_repository.py
          network_repository.py
          graph_repository.py
      storage/
        local_storage.py
        ftp_storage.py
      exporters/
        excel_exporter.py
        csv_exporter.py
      graph/
        graph_builder.py
```

## 1.2 Definir contrato de tool

Todas las tools deben tener la misma interfaz.

```python
class BaseTool:
    name: str
    platform: str | None

    async def run(self, ctx: ToolContext) -> ToolResult:
        raise NotImplementedError
```

`ToolContext` debe contener:

```txt
job_id
analysis_id opcional
platform
target_url
username
limits
scope
browser_context
previous_results
```

`ToolResult` debe devolver:

```txt
tool_name
status
profiles
relationships
publications
comments
reactions
artifacts
raw
error
started_at
finished_at
```

## 1.3 Convertir funciones actuales a tools

Orden de conversión:

```txt
facebook.validate_session
facebook.fetch_profile_snapshot
facebook.fetch_friends
facebook.fetch_followers
facebook.fetch_following
facebook.fetch_photo_engagements
common.build_graph
common.export_csv
```

No conviertas todo de golpe. Primero Facebook completo. Después Instagram. Después X.

## 1.4 Crear Tool Registry

El registry debe saber qué tools existen.

Ejemplo conceptual:

```python
TOOL_REGISTRY = {
    "facebook.validate_session": FacebookValidateSessionTool,
    "facebook.fetch_profile_snapshot": FacebookFetchProfileSnapshotTool,
    "facebook.fetch_friends": FacebookFetchFriendsTool,
    "facebook.fetch_followers": FacebookFetchFollowersTool,
    "facebook.fetch_following": FacebookFetchFollowingTool,
    "facebook.fetch_photo_engagements": FacebookFetchPhotoEngagementsTool,
    "common.build_graph": BuildGraphTool,
}
```

## 1.5 Crear planes de ejecución

El orquestador no debe tener lógica dura de Facebook. Debe construir un plan.

Ejemplo:

```txt
Plan Facebook:
1. facebook.validate_session
2. facebook.fetch_profile_snapshot
3. facebook.fetch_friends
4. facebook.fetch_followers
5. facebook.fetch_following
6. facebook.fetch_photo_engagements
7. common.build_graph
```

Para Instagram:

```txt
1. instagram.validate_session
2. instagram.fetch_profile_snapshot
3. instagram.fetch_followers
4. instagram.fetch_following
5. instagram.fetch_post_engagements
6. common.build_graph
```

**Resultado esperado de Fase 1:** el MVP sigue funcionando, pero ahora cada parte del scraping es una tool individual auditable.

---

# Fase 2 — Persistencia técnica de jobs y tool runs

Antes de guardar identidades, grafos o Excel, necesitas trazabilidad.

## 2.1 Crear tablas operativas del scraper

Aunque uses los schemas actuales, conviene tener tablas técnicas propias:

```txt
scraper.job
scraper.tool_run
scraper.artifact
scraper.raw_payload
```

Si no quieres crear schema `scraper`, puedes usar `redes`, pero conceptualmente estas tablas pertenecen al runtime del scraper.

## 2.2 `scraper.job`

Representa una ejecución completa.

Campos mínimos:

```txt
id_job
id_analisis nullable
platform
target_url
username
status
scope_json
limits_json
error
created_at
started_at
finished_at
```

Estados:

```txt
queued
running
completed
failed
cancelled
partial
```

## 2.3 `scraper.tool_run`

Representa cada tool ejecutada.

Campos mínimos:

```txt
id_tool_run
id_job
tool_name
status
input_json
output_summary_json
raw_payload_id nullable
error
started_at
finished_at
duration_ms
```

Esto te permite saber exactamente dónde falló un análisis.

## 2.4 Política de errores

Si falla una tool crítica:

```txt
validate_session falla → job failed
fetch_profile_snapshot falla → job failed
fetch_followers falla → job partial
fetch_photo_engagements falla → job partial
build_graph falla → job completed_without_graph
```

**Resultado esperado de Fase 2:** puedes consultar el historial de ejecución y depurar sin revisar logs manualmente.

---

# Fase 3 — Normalización de resultados

Antes de persistir en tablas finales, cada tool debe devolver datos en un formato común.

## 3.1 Modelo común de perfil

```json
{
  "platform": "facebook",
  "external_id": "123456789",
  "username": "juan.perez",
  "profile_url": "https://www.facebook.com/juan.perez/",
  "display_name": "Juan Pérez",
  "profile_photo_url": "https://...",
  "raw": {}
}
```

## 3.2 Modelo común de relación

```json
{
  "source": {
    "platform": "facebook",
    "username": "juan.perez",
    "external_id": "123456789"
  },
  "target": {
    "platform": "facebook",
    "username": "carlos.lopez",
    "external_id": "987654321"
  },
  "type": "FRIEND",
  "observed_at": "2026-06-29T12:00:00"
}
```

## 3.3 Tipos de relación mínimos

```txt
FRIEND
FOLLOWER
FOLLOWING
COMMENTED
REACTED
MENTIONED
LIKED
SHARED
UNKNOWN
```

## 3.4 Regla de deduplicación

Nunca deduplicar por nombre visible.

Orden correcto:

```txt
1. platform + external_id
2. platform + normalized_url
3. platform + username
4. temporary_hash
```

**Resultado esperado de Fase 3:** Facebook, Instagram y X pueden producir salidas compatibles aunque internamente scrapeen diferente.

---

# Fase 4 — Persistencia de identidades y vínculos técnicos

Aquí el scraper empieza a guardar datos reales, pero todavía no entra el grafo editable.

## 4.1 Guardar perfiles en `personas.identidad_digital`

Todos los perfiles van a la misma tabla:

```txt
objetivo
amigos
seguidores
seguidos
comentadores
reaccionadores
```

No debe haber una tabla distinta para “objetivos” y otra para “relacionados”.

## 4.2 Guardar relaciones en `redes.vinculo_social`

Las aristas técnicas deben vivir en una tabla de relaciones.

Ejemplo:

```txt
id_identidad_origen
id_identidad_destino
id_tipo_vinculo
id_analisis
vigente
fecha_observacion
```

## 4.3 Upsert obligatorio

Para evitar duplicados:

```txt
upsert identidad_digital
upsert vinculo_social
upsert publicación
upsert comentario
upsert reacción
```

## 4.4 No borrar físicamente

Nada scrapeado debería borrarse por default.

Usar:

```txt
activo
inactivo
descartado
fusionado
oculto
```

**Resultado esperado de Fase 4:** los datos técnicos del scraper quedan persistidos sin depender todavía del grafo editable.

---

# Fase 5 — Construcción de grafo técnico

Aquí `graph/build` debe usar los datos normalizados o persistidos.

## 5.1 Grafo técnico no editable

Primero genera un grafo técnico simple:

```json
{
  "nodes": [
    {
      "id": "identity:facebook:123456789",
      "id_identidad_digital": 10,
      "label": "Juan Pérez",
      "username": "juan.perez",
      "platform": "facebook",
      "type": "IDENTIDAD_DIGITAL"
    }
  ],
  "edges": [
    {
      "id": "edge:10:22:FRIEND",
      "source": "identity:facebook:123456789",
      "target": "identity:facebook:987654321",
      "type": "FRIEND"
    }
  ]
}
```

## 5.2 Regla central

```txt
El nombre visible puede cambiar.
El ID estable nunca cambia.
```

El frontend puede mostrar:

```txt
Juan Pérez
El Contador
Objetivo 1
Alias A
```

Pero internamente debe seguir siendo:

```txt
identity:facebook:123456789
```

## 5.3 Graph snapshot

Guardar cada grafo generado como snapshot:

```txt
id_graph_snapshot
id_job
id_analisis
graph_json
created_at
```

**Resultado esperado de Fase 5:** puedes generar grafos reproducibles sin edición manual todavía.

---

# Fase 6 — Grafo editable por caso

Esta fase debe vivir preferentemente en Core, no en Scr4per. Pero puedes modelarla desde ahora.

## 6.1 Crear `casos.grafo_nodo`

Representa el nodo editable dentro de un caso.

Campos importantes:

```txt
id_grafo_nodo
id_caso
tipo_nodo
stable_key
id_identidad_digital nullable
id_persona nullable
label_original
label_visible
alias_manual
metadata
posicion
estado
created_at
updated_at
```

`stable_key` debe ser único por caso:

```txt
identity:facebook:123456789
identity:instagram:987654321
person:42
phone:+525512345678
custom:uuid
```

## 6.2 Crear `casos.grafo_arista`

Representa la relación editable dentro de un caso.

Campos importantes:

```txt
id_grafo_arista
id_caso
id_nodo_origen
id_nodo_destino
tipo_relacion
fuente
id_vinculo_social nullable
id_analisis nullable
label_visible
metadata
estado
created_at
updated_at
```

## 6.3 Separar arista técnica de arista visual

```txt
redes.vinculo_social
= relación observada por scraper

casos.grafo_arista
= relación visible/editable en el caso
```

Una arista visual puede venir de:

```txt
SCRAPER
MANUAL
SABANA
IMPORTACION
INFERENCIA
```

## 6.4 No editar datos canónicos desde el grafo

El usuario puede editar:

```txt
alias
label_visible
color
posición
notas
agrupación
estado visual
```

No puede editar directamente:

```txt
id_identidad_digital
username canónico
external_id
stable_key
id_vinculo_social
```

**Resultado esperado de Fase 6:** el grafo se puede editar sin romper relaciones técnicas ni datos históricos.

---

# Fase 7 — Aliases por caso

Esta fase resuelve el problema de que una persona o identidad tenga alias distintos según el caso.

## 7.1 Alias de persona

Crear:

```txt
casos.caso_persona_alias
```

Campos:

```txt
id_caso_persona_alias
id_caso
id_persona
alias
es_principal
observaciones
estado
created_at
updated_at
```

## 7.2 Alias de identidad digital

Crear:

```txt
casos.caso_identidad_alias
```

Campos:

```txt
id_caso_identidad_alias
id_caso
id_identidad_digital
alias
es_principal
observaciones
estado
created_at
updated_at
```

## 7.3 Regla de visualización

```txt
display_name =
alias_manual del nodo
o alias principal en caso
o nombre_publico scrapeado
o username
o stable_key
```

**Resultado esperado de Fase 7:** un mismo perfil puede llamarse diferente en distintos casos sin duplicar identidades.

---

# Fase 8 — Edición de grafos

Aquí ya defines comportamiento del frontend/API.

## 8.1 Operaciones permitidas

```http
GET    /v1/cases/{case_id}/graph
POST   /v1/cases/{case_id}/graph/nodes
PATCH  /v1/cases/{case_id}/graph/nodes/{node_id}
DELETE /v1/cases/{case_id}/graph/nodes/{node_id}

POST   /v1/cases/{case_id}/graph/edges
PATCH  /v1/cases/{case_id}/graph/edges/{edge_id}
DELETE /v1/cases/{case_id}/graph/edges/{edge_id}
```

## 8.2 DELETE lógico, no físico

Eliminar un nodo del grafo debe hacer:

```sql
UPDATE casos.grafo_nodo
SET estado = 'oculto'
WHERE id_grafo_nodo = :id;
```

Y ocultar sus aristas:

```sql
UPDATE casos.grafo_arista
SET estado = 'oculta'
WHERE id_nodo_origen = :id
   OR id_nodo_destino = :id;
```

No borrar `personas.identidad_digital`.

## 8.3 Edición de alias

Cambiar alias:

```txt
PATCH grafo_nodo.alias_manual
```

No cambiar:

```txt
personas.identidad_digital.nombre_publico
```

## 8.4 Edición de aristas

Si una arista viene del scraper, el usuario puede ocultarla o renombrarla visualmente.

Pero no debería modificar el vínculo técnico original.

```txt
id_vinculo_social permanece intacto
label_visible puede cambiar
estado puede cambiar
metadata visual puede cambiar
```

**Resultado esperado de Fase 8:** el grafo es editable sin destruir evidencia.

---

# Fase 9 — Edge cases y reglas de protección

Esta fase debe implementarse antes de ponerlo live.

## 9.1 Duplicación de perfiles

Problema:

```txt
facebook.com/juanp
m.facebook.com/juanp
web.facebook.com/juanp
facebook.com/profile.php?id=123
```

Solución:

```txt
normalización obligatoria
upsert por platform + external_id
fallback platform + username
nunca deduplicar por nombre
```

## 9.2 Username cambia

Solución:

```txt
external_id manda sobre username
username anterior puede guardarse en historial
```

Tabla opcional:

```txt
personas.identidad_digital_username_historial
```

## 9.3 Dos perfiles tienen el mismo nombre

Solución:

```txt
nombre_publico no es llave
stable_key no depende del nombre
```

## 9.4 Misma relación aparece en varios análisis

No es duplicado necesariamente.

Solución:

```txt
redes.vinculo_social guarda observaciones por análisis
casos.grafo_arista consolida visualmente
metadata guarda analysis_ids, first_seen, last_seen, observed_count
```

## 9.5 Usuario borra nodo del grafo

No borrar identidad.

Solución:

```txt
estado = oculto
aristas relacionadas = ocultas
identidad_digital permanece
vinculos_sociales permanecen
```

## 9.6 Usuario borra caso

Depende de política:

```txt
casos.grafo_nodo puede borrarse por cascade
casos.grafo_arista puede borrarse por cascade
personas.identidad_digital no debe borrarse
redes.vinculo_social no debería borrarse automáticamente si quieres conservar histórico
```

## 9.7 Perfil huérfano

No siempre es error.

Puede ser:

```txt
perfil descubierto
perfil descartado
perfil no asignado todavía
perfil de análisis viejo
```

Solución:

```txt
mantener estado
crear proceso de limpieza/revisión
no borrar automáticamente
```

## 9.8 Merge de identidades duplicadas

Agregar a `personas.identidad_digital`:

```txt
merged_into_id nullable
```

Proceso:

```txt
A se conserva
B pasa a fusionada
relaciones de B se remapean a A
nodos de B se actualizan o se marcan como fusionados
historial se conserva
```

## 9.9 Edición concurrente del grafo

Dos usuarios editan el mismo nodo.

Solución mínima:

```txt
updated_at
updated_by
version integer
```

Al hacer PATCH:

```txt
si version enviada != version actual
rechazar con conflicto 409
```

## 9.10 Aristas manuales sin vínculo técnico

Debe permitirse.

No toda arista viene del scraper.

```txt
id_vinculo_social nullable
fuente = MANUAL
```

---

# Fase 10 — Exportación y artefactos

Ya con tools, persistencia y grafo, ahora sí agregas Excel/CSV/FTP.

## 10.1 Export Excel

Endpoint:

```http
POST /v1/analyses/{analysis_id}/exports/excel
```

Debe leer datos persistidos, no volver a scrapear.

## 10.2 Export CSV

Puede mantenerse para debug o compatibilidad.

```http
POST /v1/analyses/{analysis_id}/exports/csv
```

## 10.3 Artifact storage

Crear servicio:

```txt
ArtifactStorageService
```

Implementaciones:

```txt
LocalStorage
FTPStorage
MinIOStorage futuro
CoreStorage futuro
```

## 10.4 Artefactos mínimos

```txt
graph.json
analysis.xlsx
raw_payloads.json
screenshots opcionales
profile_images opcionales
```

**Resultado esperado de Fase 10:** los outputs se generan sin ensuciar el flujo de scraping.

---

# Fase 11 — Integración con Core

Esta debe ser la última fase, no la primera.

## 11.1 Flujo live

```txt
Frontend
  → Gateway
    → Core crea análisis
      → Core llama Scr4per
        → Scr4per ejecuta job
        → Scr4per devuelve resultados/eventos
      → Core vincula con caso/persona/grafo
```

## 11.2 Scr4per interno

Scr4per expone:

```http
POST /internal/v1/jobs
GET  /internal/v1/jobs/{job_id}
GET  /internal/v1/jobs/{job_id}/tool-runs
POST /internal/v1/jobs/{job_id}/cancel
```

## 11.3 Core público

Core expone:

```http
POST /v1/cases/{case_id}/digital-identities/{identity_id}/analyses
GET  /v1/analyses/{analysis_id}
GET  /v1/cases/{case_id}/graph
PATCH /v1/cases/{case_id}/graph/nodes/{node_id}
PATCH /v1/cases/{case_id}/graph/edges/{edge_id}
```

**Resultado esperado de Fase 11:** Scr4per deja de ser dueño de casos/personas y sólo produce evidencia.

---

# Orden recomendado de implementación

```txt
1. Congelar MVP funcional
2. Crear estructura modular
3. Convertir Facebook a tools
4. Crear ToolRegistry y ToolRunner
5. Agregar job y tool_run
6. Normalizar salida de tools
7. Persistir identidades digitales
8. Persistir vínculos sociales
9. Construir graph/build desde datos normalizados
10. Crear graph snapshots
11. Diseñar grafo_nodo y grafo_arista
12. Agregar aliases por caso
13. Implementar edición de nodos/aristas
14. Resolver edge cases: duplicados, merge, ocultar, huérfanos
15. Agregar Excel/CSV
16. Agregar FTP/artifacts
17. Integrar con Core
18. Agregar Auth/Gateway/service-to-service
```

# Prioridad realista

Para que no se haga enorme, lo dividiría en tres entregables.

## Entregable 1 — Scraper modular

```txt
Tools
ToolRunner
ToolRegistry
Job
ToolRun
Facebook, Instagram y X funcional
Graph build básico
```

## Entregable 2 — Persistencia y grafo técnico

```txt
Upsert identidad_digital
Upsert vinculo_social
Graph snapshot
Export CSV/Excel
Artifacts locales
```

## Entregable 3 — Grafo editable e integración Core

```txt
casos.grafo_nodo
casos.grafo_arista
aliases
edición visual
edge cases
FTP
Core integration
Auth/Gateway
```

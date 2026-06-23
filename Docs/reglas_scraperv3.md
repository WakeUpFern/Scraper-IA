# Scr4per v3 — Documento Técnico de Arquitectura

## 1. Propósito

**Scr4per v3** es la evolución del scraper actual hacia un **toolkit agentico de adquisición OSINT**, diseñado para que un modelo de IA pueda utilizar herramientas ligeras, precisas, auditables y componibles para investigar identidades digitales, recolectar observaciones, generar vínculos y construir grafos de relaciones.

A diferencia de la versión actual, que funciona como un flujo rígido de scraping por perfil, Scr4per v3 se concibe como una capa de herramientas operables por IA:

```text
Objetivo OSINT
  ↓
IA analiza contexto
  ↓
IA selecciona herramientas
  ↓
Scr4per ejecuta acciones específicas
  ↓
Se guardan observaciones trazables
  ↓
Se construye grafo contextual
  ↓
Analista valida, explora o expande
```

La idea central es:

```text
Scr4per v3 no ejecuta un flujo fijo.
Scr4per v3 expone capacidades OSINT controladas para que un agente IA construya dinámicamente una investigación.
```

---

## 2. Contexto del sistema OSINT

Scr4per forma parte de una plataforma OSINT más amplia. El sistema no gira únicamente alrededor del scraping, sino alrededor de:

* Casos.
* Analistas.
* Organizaciones.
* Departamentos.
* Personas físicas.
* Identidades digitales.
* Análisis.
* Observaciones.
* Evidencia.
* Grafos.
* Datos externos como sábanas telefónicas.

El **caso** es el contenedor formal de una investigación, pero no debe ser obligatorio para iniciar una adquisición OSINT. El sistema debe permitir:

* Análisis autónomos sin caso.
* Identidades digitales sin persona física atribuida.
* Personas físicas sin caso formal.
* Análisis exploratorios.
* Búsquedas por username, URL, alias, teléfono, email u otros indicadores.
* Vinculación posterior de análisis a casos.
* Vinculación posterior de identidades a personas.
* Separación estricta de información entre casos y analistas.

---

## 3. Principios de diseño

### 3.1 Herramientas semánticas, no acciones de navegador

La IA no debe operar directamente con acciones de bajo nivel como:

```text
click(selector)
scroll_modal()
eval_js()
wait_for_selector()
```

En su lugar, debe usar herramientas semánticas:

```text
fetch_profile_snapshot
fetch_followers_batch
fetch_following_batch
fetch_recent_posts
fetch_post_comments
fetch_post_reactions
build_graph_from_analysis
```

La complejidad de Playwright, Scrapling, interceptación de red, DOM fallback y sesiones debe quedar encapsulada dentro de cada herramienta.

---

### 3.2 Network-first, DOM fallback

La estrategia principal de extracción debe ser **network-first**:

```text
1. Capturar API calls, GraphQL, XHR, fetch y JSON estructurado.
2. Parsear raw JSON.
3. Normalizar entidades, publicaciones y vínculos.
4. Usar DOM solo como fallback o verificación.
```

Esto es preferible porque las redes sociales modernas suelen renderizar el DOM a partir de datos estructurados recibidos por API internas, GraphQL o endpoints dinámicos.

Comparación:

```text
DOM scraping:
  - Frágil ante cambios visuales.
  - Depende de selectores, clases, modales y layouts.
  - Mezcla datos con presentación.
  - Menos confiable para IDs internos y paginación.

Network/API scraping:
  - Datos estructurados.
  - IDs externos o internos más estables.
  - Cursors de paginación.
  - Raw JSON auditable.
  - Mejor normalización.
```

La estrategia recomendada no es “network-only”, sino:

```text
Network-first + DOM fallback + raw evidence.
```

---

### 3.3 Toda información scrapeada es una observación

El sistema no debe asumir que los datos obtenidos representan verdades globales permanentes.

No se debe modelar así:

```text
Esta identidad tiene estos seguidores.
```

Sino así:

```text
Este análisis observó estos seguidores, en esta fecha, usando esta herramienta, bajo este usuario/caso.
```

Esto permite:

* Aislamiento entre casos.
* Auditoría.
* Comparación histórica.
* Reprocesamiento.
* Evitar contaminación entre análisis.
* Mantener trazabilidad.

---

### 3.4 Catálogo global mínimo, observaciones privadas

El sistema puede mantener un catálogo global mínimo de entidades estables:

```text
personas.persona
personas.identidad_digital
redes.plataforma
redes.tipo_vinculo_social
```

Pero los datos derivados deben ser contextuales:

```text
redes.analisis
redes.vinculo_social
redes.publicacion
redes.comentario
redes.reaccion
redes.identidad_observacion
redes.tool_run
redes.graph_snapshot
```

La identidad puede ser global.

La observación pertenece a un análisis.

El análisis pertenece a un usuario y opcionalmente a un caso.

La visibilidad se decide por caso, propietario, ACL o permisos especiales.

---

### 3.5 Aislamiento entre casos y analistas

Una misma persona física o identidad digital puede aparecer en varios casos, pero los resultados de cada análisis no deben cruzarse automáticamente.

Por defecto:

```text
Analista A analiza @usuario
Analista B analiza @usuario
```

El analista B no debe ver automáticamente:

* Resultados de A.
* Grafos de A.
* Notas de A.
* Comentarios recolectados por A.
* Reacciones recolectadas por A.
* Relaciones descubiertas por A.
* Evidencias descargadas por A.
* Interpretaciones o hipótesis de A.

El sistema puede deduplicar internamente, pero no debe revelar información privada de otros casos o usuarios.

---

## 4. Modelo conceptual

### 4.1 Entidades principales

```text
Organización
  └── Área
      └── Departamento
          └── Usuario / Analista
              └── Caso
                  ├── Personas físicas
                  │   └── Identidades digitales
                  │       └── Análisis OSINT
                  │           ├── Observaciones de identidad
                  │           ├── Publicaciones
                  │           ├── Comentarios
                  │           ├── Reacciones
                  │           ├── Vínculos sociales
                  │           └── Evidencia
                  └── Sábanas / datos externos
```

---

### 4.2 Caso

El caso es el contenedor formal de investigación.

Un caso puede tener:

* Personas físicas.
* Identidades digitales.
* Análisis.
* Colaboradores.
* Evidencias.
* Grafos.
* Observaciones.
* Sábanas telefónicas.
* Reportes.

Pero un análisis no necesita nacer obligatoriamente dentro de un caso.

---

### 4.3 Persona física

Una persona física representa un individuo real.

Una persona puede tener:

```text
1..n identidades digitales
```

Ejemplo:

```text
Persona: Juan Pérez
  ├── Facebook: juan.perez.123
  ├── Instagram: @juanp
  ├── X: @jperez
  └── Telegram: @juanperez
```

La persona puede estar en varios casos, pero su información contextual no debe cruzarse entre ellos.

---

### 4.4 Identidad digital

Una identidad digital representa una cuenta, perfil o presencia digital en una plataforma.

Puede existir sin persona física atribuida:

```text
identidad_digital.id_persona = NULL
```

Esto permite flujos OSINT reales donde primero se encuentra una cuenta y después se intenta atribuir a una persona.

---

### 4.5 Atribución identidad → persona

La relación entre identidad digital y persona física no debe tratarse solo como una FK.

Debe modelarse como una hipótesis trazable:

```text
Esta identidad probablemente pertenece a esta persona.
Confianza: 0.82
Evidencia: foto, nombre, links, contactos, coincidencias.
Validado por: analista X
Fecha: ...
```

Tabla sugerida:

```sql
personas.atribucion_identidad (
  id_atribucion bigint primary key,
  id_identidad_digital bigint not null,
  id_persona bigint not null,
  id_usuario bigint not null,
  id_analisis bigint,
  id_caso bigint,
  confianza numeric(5,4),
  metodo varchar(100),
  observaciones text,
  evidencia_json jsonb default '{}',
  estado varchar(50) default 'propuesta',
  fecha_creacion timestamp default current_timestamp,
  fecha_modificacion timestamp
)
```

Estados sugeridos:

```text
propuesta
validada
rechazada
obsoleta
```

---

## 5. Arquitectura general de Scr4per v3

```text
┌───────────────────────────────────────────────┐
│                OSINT AI Agent                  │
│  planea, decide, razona, prioriza, resume       │
└───────────────────────┬───────────────────────┘
                        │
┌───────────────────────▼───────────────────────┐
│              Tool Registry                     │
│  schemas, permisos, límites, descripciones      │
└───────────────────────┬───────────────────────┘
                        │
┌───────────────────────▼───────────────────────┐
│              Tool Executor                     │
│  auditoría, retries, cuotas, timeouts           │
└───────────────────────┬───────────────────────┘
                        │
┌───────────────────────▼───────────────────────┐
│            Scraper Tool Layer                  │
│  herramientas OSINT semánticas                  │
└───────────────────────┬───────────────────────┘
                        │
┌───────────────────────▼───────────────────────┐
│            Platform Adapters                   │
│  Facebook / Instagram / X / futuras fuentes     │
└───────────────────────┬───────────────────────┘
                        │
┌───────────────────────▼───────────────────────┐
│       Playwright + Scrapling Runtime           │
│  browser, sesiones, network capture, fallback   │
└───────────────────────┬───────────────────────┘
                        │
┌───────────────────────▼───────────────────────┐
│        Normalization + Observation Layer       │
│  raw_json → modelo común OSINT                  │
└───────────────────────┬───────────────────────┘
                        │
┌───────────────────────▼───────────────────────┐
│          Persistence + RAG Layer               │
│  PostgreSQL, raw evidence, ACL, contexto IA     │
└───────────────────────┬───────────────────────┘
                        │
┌───────────────────────▼───────────────────────┐
│              Graph Builder                     │
│  grafo por análisis, caso, persona o identidad  │
└───────────────────────────────────────────────┘
```

---

## 6. Integración de IA

### 6.1 Rol de la IA

La IA actúa como:

* Planificador.
* Selector de herramientas.
* Evaluador de resultados.
* Priorizador de nodos.
* Generador de hipótesis.
* Constructor de contexto.
* Generador de grafo.
* Asistente del analista.

La IA no debe sustituir al analista en decisiones críticas, como atribuir definitivamente una identidad a una persona o marcar a alguien como relevante en un caso sensible.

---

### 6.2 Ciclo agentico

```text
1. Recibir objetivo
2. Consultar contexto permitido
3. Crear o reutilizar análisis
4. Planificar pasos
5. Ejecutar herramienta
6. Observar resultado
7. Persistir observaciones
8. Evaluar relevancia
9. Decidir siguiente herramienta
10. Construir o actualizar grafo
11. Generar resumen
12. Solicitar validación humana si aplica
```

---

### 6.3 Ejemplo de flujo

Objetivo:

```text
Analizar la identidad de Instagram @juanp.
```

Flujo:

```text
1. IA normaliza username.
2. IA consulta si la identidad ya existe.
3. Sistema detecta identidad global o crea una nueva.
4. IA crea análisis privado.
5. IA ejecuta fetch_profile_snapshot.
6. Se capturan datos de perfil.
7. Se guarda identidad_observacion.
8. IA detecta links externos en bio.
9. IA crea identidades candidatas en otras plataformas.
10. IA ejecuta fetch_recent_posts.
11. IA obtiene comentarios y reacciones de posts relevantes.
12. IA prioriza usuarios frecuentes.
13. IA obtiene followers/following de forma limitada.
14. Se guardan vínculos sociales observados.
15. Se genera grafo ponderado.
16. IA produce resumen y hallazgos.
```

---

## 7. Tool Registry

El Tool Registry define qué herramientas existen, cuándo se pueden usar, qué permisos requieren, qué inputs aceptan, qué outputs devuelven y qué límites tienen.

Cada herramienta debe tener:

```text
name
description
input_schema
output_schema
required_permissions
allowed_platforms
rate_limits
timeout
max_items
side_effects
audit_level
```

Ejemplo:

```json
{
  "name": "fetch_followers_batch",
  "description": "Obtiene un lote paginado de seguidores observados para una identidad digital.",
  "allowed_platforms": ["facebook", "instagram", "x"],
  "input_schema": {
    "id_analisis": "number",
    "identity_ref": "string",
    "platform": "string",
    "limit": "number",
    "cursor": "string | null"
  },
  "output_schema": {
    "items": "array",
    "next_cursor": "string | null",
    "has_more": "boolean",
    "observation_time": "timestamp",
    "warnings": "array"
  },
  "side_effects": [
    "network_access",
    "may_create_identity_observations",
    "may_create_relationship_observations"
  ]
}
```

---

## 8. Familias de herramientas

### 8.1 Herramientas de identidad

```text
resolve_platform_from_url
normalize_username
resolve_identity
search_identity_candidates
find_similar_identities
suggest_identity_attribution
```

---

### 8.2 Herramientas de perfil

```text
fetch_profile_snapshot
fetch_profile_photo
fetch_profile_public_metadata
check_profile_availability
```

---

### 8.3 Herramientas de red

```text
fetch_followers_batch
fetch_following_batch
fetch_friends_batch
fetch_mutual_connections
```

---

### 8.4 Herramientas de contenido

```text
fetch_recent_posts
fetch_post_detail
fetch_post_comments_batch
fetch_post_reactions_batch
fetch_post_shares_batch
```

---

### 8.5 Herramientas de normalización

```text
normalize_observed_identity
normalize_relationship
normalize_post
normalize_comment
normalize_reaction
normalize_media
```

---

### 8.6 Herramientas de persistencia

```text
create_analysis_context
persist_identity_observation
persist_relationship_observations
persist_content_observations
persist_raw_evidence
link_analysis_to_case
mark_identity_relevant_to_case
mark_person_relevant_to_case
```

---

### 8.7 Herramientas de grafo

```text
build_graph_from_analysis
build_graph_from_case
build_graph_from_identity
rank_graph_nodes
detect_communities
export_graph
```

---

## 9. Playwright + Scrapling

### 9.1 Rol de Playwright

Playwright debe seguir siendo el runtime principal para:

* Lanzar Chromium headless.
* Manejar storage_state/cookies.
* Crear contextos aislados.
* Navegar perfiles.
* Interceptar requests/responses.
* Capturar GraphQL/API calls.
* Manejar sesiones.
* Ejecutar fallback visual si es necesario.
* Generar screenshots/traces cuando aplique.

---

### 9.2 Rol de Scrapling

Scrapling puede integrarse como capa auxiliar para:

* Parsing adaptativo.
* Manejo de raw JSON.
* Extracción de datos estructurados.
* Fetchers ligeros cuando no se necesita una página completa.
* Crawling controlado.
* Utilidades stealth o anti-detección moderadas.
* Fallback DOM más resistente.
* Normalización inicial de respuestas.

Scrapling no debe reemplazar a Playwright como runtime principal si el sistema necesita navegación real, sesiones autenticadas y captura de tráfico en navegador.

La combinación recomendada es:

```text
Playwright:
  navegador, sesión, contexto, navegación, network capture.

Scrapling:
  parsing, fetch auxiliar, adaptación, fallback, raw extraction.

Normalizers:
  convierten cualquier fuente a modelo OSINT común.

Tools:
  exponen capacidades semánticas a la IA.
```

---

### 9.3 Estrategia de extracción

Cada herramienta debe implementar un pipeline interno:

```text
1. Preparar contexto de navegador.
2. Cargar sesión autorizada.
3. Navegar o disparar evento mínimo.
4. Capturar API/GraphQL/XHR.
5. Extraer raw JSON.
6. Parsear con extractor específico.
7. Normalizar a modelo común.
8. Guardar raw evidence.
9. Persistir observaciones.
10. Devolver resultado compacto a la IA.
```

Fallback:

```text
Si no se detecta respuesta network:
  → intentar endpoint alternativo
  → intentar DOM parser
  → intentar screenshot/HTML snapshot
  → devolver partial_success con warnings
```

---

## 10. Extractores por plataforma

### 10.1 Estructura sugerida

```text
platforms/
  facebook/
    capabilities.py
    client.py
    network_extractors/
      profile_graphql.py
      friends_graphql.py
      followers_graphql.py
      reactions_graphql.py
      comments_graphql.py
    dom_extractors/
      profile_dom.py
      list_dom.py
    normalizers/
      identity.py
      relationship.py
      post.py
      comment.py
      reaction.py

  instagram/
    capabilities.py
    client.py
    network_extractors/
      profile_graphql.py
      followers_graphql.py
      following_graphql.py
      posts_graphql.py
      comments_graphql.py
      reactions_graphql.py
    dom_extractors/
      profile_dom.py
      modal_list_dom.py
    normalizers/
      identity.py
      relationship.py
      post.py
      comment.py
      reaction.py

  x/
    capabilities.py
    client.py
    network_extractors/
      profile_api.py
      followers_api.py
      following_api.py
      timeline_api.py
      replies_api.py
    dom_extractors/
      profile_dom.py
      timeline_dom.py
    normalizers/
      identity.py
      relationship.py
      post.py
      comment.py
      reaction.py
```

---

### 10.2 Capabilities

No todas las plataformas soportan las mismas herramientas.

Cada plataforma debe declarar capacidades:

```json
{
  "platform": "instagram",
  "capabilities": {
    "profile_snapshot": true,
    "followers": true,
    "following": true,
    "friends": false,
    "posts": true,
    "comments": true,
    "reactions": true,
    "shares": false
  }
}
```

La IA debe consultar capacidades antes de planificar.

---

## 11. Modelo de datos recomendado

### 11.1 Tablas existentes relevantes

El modelo actual ya incluye tablas fundamentales:

```text
casos.caso
casos.colaborador_caso
casos.caso_persona
casos.caso_identidad_digital
casos.caso_analisis

personas.persona
personas.identidad_digital

redes.plataforma
redes.analisis
redes.vinculo_social
redes.tipo_vinculo_social
redes.publicacion
redes.comentario
redes.reaccion
redes.compartido
redes.publicacion_multimedia
```

---

### 11.2 Tablas sugeridas para v3

#### 11.2.1 `redes.tool_run`

Registra cada ejecución de herramienta.

```sql
CREATE TABLE redes.tool_run (
  id_tool_run bigserial PRIMARY KEY,
  id_analisis bigint NOT NULL REFERENCES redes.analisis(id_analisis),
  id_usuario bigint REFERENCES entidades.usuario(id_usuario),
  tool_name varchar(150) NOT NULL,
  platform varchar(50),
  input_json jsonb NOT NULL DEFAULT '{}',
  output_json jsonb NOT NULL DEFAULT '{}',
  status varchar(50) NOT NULL,
  error text,
  started_at timestamp NOT NULL DEFAULT current_timestamp,
  finished_at timestamp,
  cost_json jsonb NOT NULL DEFAULT '{}',
  extractor_strategy varchar(100),
  parser_version varchar(50),
  created_by_agent boolean DEFAULT true
);
```

Estados sugeridos:

```text
pending
running
success
partial_success
failed
cancelled
timeout
blocked
```

---

#### 11.2.2 `redes.raw_evidence`

Guarda respuestas crudas, HTML, screenshots, JSON o blobs referenciados.

```sql
CREATE TABLE redes.raw_evidence (
  id_raw_evidence bigserial PRIMARY KEY,
  id_analisis bigint NOT NULL REFERENCES redes.analisis(id_analisis),
  id_tool_run bigint REFERENCES redes.tool_run(id_tool_run),
  evidence_type varchar(50) NOT NULL,
  platform varchar(50),
  source_url text,
  request_hash varchar(255),
  operation_name varchar(255),
  storage_path text,
  raw_json jsonb,
  metadata jsonb DEFAULT '{}',
  observed_at timestamp NOT NULL DEFAULT current_timestamp
);
```

Tipos:

```text
json
html
screenshot
har
image
video
file
api_response
graphql_response
```

---

#### 11.2.3 `redes.identidad_observacion`

Guarda snapshots contextuales de una identidad.

```sql
CREATE TABLE redes.identidad_observacion (
  id_identidad_observacion bigserial PRIMARY KEY,
  id_analisis bigint NOT NULL REFERENCES redes.analisis(id_analisis),
  id_tool_run bigint REFERENCES redes.tool_run(id_tool_run),
  id_identidad_digital bigint NOT NULL REFERENCES personas.identidad_digital(id_identidad_digital),
  id_usuario_observador bigint REFERENCES entidades.usuario(id_usuario),
  id_caso bigint REFERENCES casos.caso(id_caso),
  nombre_publico_observado varchar(150),
  username_observado varchar(150),
  usuario_url_observada text,
  descripcion_observada text,
  foto_url_observada text,
  metricas_json jsonb DEFAULT '{}',
  raw_json jsonb DEFAULT '{}',
  observed_at timestamp NOT NULL DEFAULT current_timestamp
);
```

Esta tabla evita que los campos dinámicos de `personas.identidad_digital` se conviertan en verdad global.

---

#### 11.2.4 `personas.identidad_digital_alias`

Historial de usernames y URLs.

```sql
CREATE TABLE personas.identidad_digital_alias (
  id_alias bigserial PRIMARY KEY,
  id_identidad_digital bigint NOT NULL REFERENCES personas.identidad_digital(id_identidad_digital),
  username varchar(150),
  usuario_url text,
  id_analisis bigint REFERENCES redes.analisis(id_analisis),
  fecha_observacion timestamp NOT NULL DEFAULT current_timestamp,
  vigente boolean DEFAULT true,
  raw_json jsonb DEFAULT '{}'
);
```

---

#### 11.2.5 `redes.resultado_busqueda_identidad`

Resultados de búsqueda exploratoria.

```sql
CREATE TABLE redes.resultado_busqueda_identidad (
  id_resultado bigserial PRIMARY KEY,
  id_analisis bigint NOT NULL REFERENCES redes.analisis(id_analisis),
  id_identidad_digital bigint REFERENCES personas.identidad_digital(id_identidad_digital),
  plataforma varchar(50),
  query text NOT NULL,
  score numeric(5,4),
  motivo_match jsonb DEFAULT '{}',
  raw_json jsonb DEFAULT '{}',
  estado varchar(50) DEFAULT 'candidato',
  fecha_creacion timestamp DEFAULT current_timestamp
);
```

---

#### 11.2.6 `redes.analisis_acl`

Control explícito de visibilidad.

```sql
CREATE TABLE redes.analisis_acl (
  id_analisis_acl bigserial PRIMARY KEY,
  id_analisis bigint NOT NULL REFERENCES redes.analisis(id_analisis),
  id_usuario bigint REFERENCES entidades.usuario(id_usuario),
  id_caso bigint REFERENCES casos.caso(id_caso),
  permiso varchar(50) NOT NULL,
  fecha_creacion timestamp DEFAULT current_timestamp
);
```

Permisos sugeridos:

```text
owner
read
write
export
share
audit
```

---

#### 11.2.7 `redes.graph_snapshot`

Snapshot de grafo generado.

```sql
CREATE TABLE redes.graph_snapshot (
  id_graph_snapshot bigserial PRIMARY KEY,
  id_analisis bigint REFERENCES redes.analisis(id_analisis),
  id_caso bigint REFERENCES casos.caso(id_caso),
  id_usuario bigint REFERENCES entidades.usuario(id_usuario),
  graph_scope varchar(50) NOT NULL,
  graph_json jsonb NOT NULL,
  metrics_json jsonb DEFAULT '{}',
  storage_path text,
  fecha_creacion timestamp DEFAULT current_timestamp
);
```

Scopes:

```text
analysis
case
person
identity
workspace
```

---

## 12. RAG estructurado sobre la DB

La IA debe usar la DB como memoria estructurada, pero siempre filtrada por permisos.

No se debe permitir que la IA consulte toda la base directamente.

Debe existir una capa:

```text
Retrieval Policy Layer
  ↓
Permission Filter
  ↓
Structured Retriever
  ↓
Vector Retriever
  ↓
Context Builder
  ↓
IA
```

---

### 12.1 RAG estructurado

Sirve para preguntas exactas:

```text
¿Esta identidad ya existe?
¿Qué aliases tiene?
¿Qué análisis puede ver este usuario?
¿Qué identidades están vinculadas a este caso?
¿Qué vínculos observó este análisis?
¿Qué nodos pertenecen al grafo del caso?
```

---

### 12.2 RAG vectorial

Sirve para texto no estructurado:

```text
bios
descripciones
posts
comentarios
notas
reportes
observaciones narrativas
transcripciones
documentos
```

Debe respetar las mismas reglas de visibilidad.

---

### 12.3 Contextos seguros para la IA

Ejemplo de contexto global sanitizado:

```json
{
  "identity_exists": true,
  "platform": "instagram",
  "username": "juanperez",
  "external_id_known": true,
  "known_aliases_count": 2,
  "visible_previous_observations_count": 0,
  "restricted_observations_count": 3
}
```

La IA puede saber que hay conocimiento previo sin acceder a los detalles privados.

---

## 13. Políticas de visibilidad

Un usuario puede ver un análisis si:

```text
1. Es el ejecutor y el análisis es privado/autónomo.
2. El análisis está ligado a un caso donde el usuario es colaborador activo.
3. El análisis fue compartido explícitamente con él.
4. Tiene rol especial de auditoría.
```

Modos sugeridos:

```text
strict:
  No revela ni la existencia de datos en otros casos.

metadata_only:
  Revela existencia de identidad global, no observaciones.

shared_index:
  Permite usar features agregadas o sanitizadas.

collaborative:
  Comparte observaciones entre casos relacionados.

auditor:
  Acceso especial controlado y registrado.
```

---

## 14. Estados de análisis

`redes.analisis.estado` debería soportar:

```text
pendiente
en_proceso
completado
completado_parcial
fallido
cancelado
expirado
bloqueado_por_sesion
sin_datos
requiere_validacion
```

---

## 15. Tipos de análisis

`redes.analisis.tipo_analisis` puede incluir:

```text
identity_search
social_profile_scrape
social_network_scrape
social_posts_scrape
social_engagement_scrape
cross_identity_resolution
graph_generation
phone_records_analysis
case_graph_refresh
```

---

## 16. Control de autonomía de la IA

La IA debe tener límites operativos:

```text
max_tool_calls
max_depth
max_related_profiles
max_followers_per_identity
max_posts_per_identity
max_comments_per_post
max_reactions_per_post
max_runtime_seconds
max_cost
allowed_platforms
requires_human_approval_for_expansion
```

Ejemplo:

```json
{
  "max_depth": 1,
  "max_related_profiles": 50,
  "max_followers_per_identity": 100,
  "max_posts_per_identity": 10,
  "requires_human_approval_for_expansion": true
}
```

---

## 17. Priorización de nodos

La IA no debe expandir todos los nodos.

Debe priorizar identidades que:

```text
aparecen en varias señales
comentan frecuentemente
reaccionan frecuentemente
son followers/following del objetivo
aparecen en varias plataformas
comparten nombre, foto, link o alias
tienen alta centralidad en el grafo
fueron marcadas por el analista
aparecen en múltiples análisis accesibles
```

---

## 18. Grafo

El grafo debe generarse desde observaciones persistidas, no directamente desde el scrape bruto.

Cada nodo y arista debe tener procedencia.

Ejemplo:

```json
{
  "nodes": [
    {
      "id": "identity:instagram:juanp",
      "type": "identity",
      "label": "@juanp",
      "platform": "instagram",
      "observed_in": [123],
      "case_relevant": true
    }
  ],
  "edges": [
    {
      "source": "identity:instagram:ana",
      "target": "identity:instagram:juanp",
      "type": "commented_on_post",
      "weight": 3,
      "evidence": {
        "analysis_id": 123,
        "tool_run_id": 987,
        "post_id": 456,
        "observed_at": "2026-06-19T12:00:00"
      }
    }
  ]
}
```

---

## 19. Pesos sugeridos de relaciones

```text
follows: 1
followed_by: 1
friend: 3
commented_on_post: 3
reacted_to_post: 2
shared_post: 4
mentioned: 4
tagged_with: 5
same_external_link: 6
same_phone: 8
same_email: 8
analyst_marked_relevant: 10
```

Los pesos deben ser configurables por organización o tipo de caso.

---

## 20. Estructura de código sugerida

```text
scraper_v3/
  agent/
    planner.py
    policies.py
    prompts.py
    context_builder.py

  tools/
    registry.py
    schemas.py
    executor.py

    identity/
      resolve_identity.py
      search_candidates.py
      normalize_identity.py

    profile/
      fetch_snapshot.py
      fetch_photo.py

    network/
      fetch_followers.py
      fetch_following.py
      fetch_friends.py

    content/
      fetch_posts.py
      fetch_comments.py
      fetch_reactions.py

    persistence/
      persist_observations.py
      persist_relationships.py
      persist_evidence.py

    graph/
      build_graph.py
      rank_nodes.py
      export_graph.py

  platforms/
    facebook/
      capabilities.py
      client.py
      network_extractors/
      dom_extractors/
      normalizers/

    instagram/
      capabilities.py
      client.py
      network_extractors/
      dom_extractors/
      normalizers/

    x/
      capabilities.py
      client.py
      network_extractors/
      dom_extractors/
      normalizers/

  runtime/
    browser_pool.py
    session_pool.py
    rate_limits.py
    retries.py
    audit.py
    storage.py

  rag/
    retrieval_policy.py
    structured_retriever.py
    vector_retriever.py
    permission_filter.py
    context_builder.py
```

---

## 21. API sugerida

### 21.1 Crear análisis

```http
POST /analyses
```

```json
{
  "id_caso": null,
  "id_persona": null,
  "identity_input": {
    "platform": "instagram",
    "username_or_url": "juanp"
  },
  "tipo_analisis": "social_profile_scrape",
  "mode": "agentic",
  "limits": {
    "max_depth": 1,
    "max_related_profiles": 50
  }
}
```

---

### 21.2 Ejecutar herramienta

```http
POST /analyses/{id_analisis}/tools/{tool_name}/run
```

```json
{
  "input": {
    "identity_ref": "instagram:juanp",
    "limit": 100,
    "cursor": null
  }
}
```

---

### 21.3 Consultar contexto para IA

```http
POST /rag/context
```

```json
{
  "scope": "analysis",
  "id_analisis": 123,
  "user_id": 1,
  "query": "identidades similares a @juanp"
}
```

---

### 21.4 Generar grafo

```http
POST /graphs/build
```

```json
{
  "scope": "analysis",
  "id_analisis": 123,
  "include_evidence": true
}
```

---

## 22. Seguridad y auditoría

Scr4per v3 debe registrar:

```text
quién ejecutó
qué herramienta ejecutó
con qué parámetros
qué sesión usó
qué plataforma consultó
qué raw data obtuvo
qué normalizador se aplicó
qué datos persistió
qué grafo generó
qué errores ocurrieron
qué decisiones tomó la IA
```

La tabla `redes.tool_run` debe ser la pieza central de auditoría operativa.

---

## 23. Manejo de sesiones

El sistema debe mantener un pool de sesiones por plataforma.

Cada sesión debe tener:

```text
id_sesion
plataforma
usuario/cuenta
estado
última_actividad
errores_consecutivos
bloqueada
expirada
cooldown_until
metadata
```

El Tool Executor debe seleccionar sesión de forma controlada y registrar su uso.

---

## 24. Manejo de errores

Errores sugeridos:

```text
session_expired
account_banned
rate_limited
profile_not_found
profile_private
network_capture_failed
dom_fallback_failed
parser_error
partial_data
timeout
tool_budget_exceeded
permission_denied
```

Una herramienta debe poder devolver:

```text
success
partial_success
failed
```

El análisis completo puede terminar como `completado_parcial` si se recolectó información útil aunque algunas herramientas fallaran.

---

## 25. Salida estándar de herramienta

Toda herramienta debe devolver un contrato común:

```json
{
  "status": "success",
  "tool_name": "fetch_profile_snapshot",
  "id_tool_run": 987,
  "observed_at": "2026-06-19T12:00:00",
  "platform": "instagram",
  "data": {},
  "normalized": {},
  "created_records": {
    "identities": [],
    "observations": [],
    "relationships": [],
    "posts": [],
    "comments": [],
    "reactions": []
  },
  "warnings": [],
  "next_actions_suggested": []
}
```

---

## 26. Decisiones humanas

La IA puede sugerir, pero ciertas decisiones deben requerir confirmación humana:

```text
atribuir identidad a persona física
marcar identidad como relevante para caso
expandir análisis a profundidad mayor
compartir análisis con otro caso
exportar evidencia sensible
fusionar identidades
fusionar personas
```

---

## 27. Beneficios esperados

Scr4per v3 permitirá:

```text
mayor flexibilidad
mejor razonamiento OSINT
menos rigidez por plataforma
mejor tolerancia a fallos
mejor trazabilidad
mejor aislamiento entre casos
mejor reutilización de datos globales mínimos
mejor generación de grafos
mayor capacidad de análisis autónomo
mejor integración con IA
```

---

## 28. Resumen ejecutivo

Scr4per v3 debe dejar de ser un scraper monolítico y convertirse en un **toolkit de adquisición OSINT controlado por IA**.

El sistema debe operar bajo estos principios:

```text
1. La IA planifica y decide.
2. Las herramientas ejecutan acciones OSINT concretas.
3. Playwright maneja navegador, sesiones y captura de red.
4. Scrapling apoya parsing, fetch dinámico y fallback adaptativo.
5. La extracción debe ser network-first y DOM fallback.
6. Todo resultado se guarda como observación contextual.
7. La identidad puede ser global, pero la observación es privada.
8. El análisis pertenece a usuario y opcionalmente a caso.
9. La visibilidad se controla por caso, propietario o ACL.
10. El grafo se construye desde observaciones auditables.
```

La frase guía del rediseño:

```text
Scr4per v3 no scrapea perfiles de forma rígida;
construye investigaciones digitales mediante herramientas agenticas,
observaciones trazables y grafos contextuales.
```

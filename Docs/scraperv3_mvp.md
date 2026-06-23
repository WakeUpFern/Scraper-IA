# Scr4per v3 — MVP Actualizado, Fases y Sprints de Implementación

## 1. Objetivo del MVP

El objetivo del MVP de **Scr4per v3** es validar la evolución del scraper actual hacia un **microservicio/toolkit agentico de adquisición OSINT social**, sin convertirlo en el sistema OSINT completo.

Scr4per v3 debe demostrar que:

1. Puede operar como un conjunto de herramientas semánticas de scraping.
2. Una IA interna del scraper puede decidir qué herramientas usar.
3. Playwright puede seguir siendo el runtime principal.
4. Scrapling puede integrarse como apoyo para parsing, raw JSON, fetch auxiliar y fallback.
5. Las respuestas network/API/GraphQL pueden aprovecharse antes que el DOM.
6. Cada herramienta ejecutada puede dejar trazabilidad mediante `tool_run`.
7. Cada dato recolectado puede guardarse como observación contextual ligada a un análisis.
8. El scraper puede generar un grafo técnico derivado de la información recolectada.
9. Scr4per puede operar con contexto recibido desde la API General, sin administrar directamente casos, personas, identidades ni permisos globales.

La frase guía del MVP es:

```text id="f10x61"
Scr4per v3 no es el sistema OSINT completo.
Es el microservicio de adquisición social que recibe contexto,
ejecuta herramientas de scraping auditables,
y devuelve observaciones, evidencia y grafos técnicos.
```

---

## 2. Decisión arquitectónica clave

### 2.1 Scr4per v3 no administra el dominio OSINT completo

Scr4per v3 **no debe crear ni administrar directamente**:

```text id="6avody"
casos
personas físicas
identidades digitales oficiales
organizaciones
departamentos
usuarios
roles
permisos
colaboradores de caso
sábanas telefónicas
reportes generales
```

Estas responsabilidades pertenecen a otros componentes del sistema:

| Componente  | Responsabilidad                                                                     |
| ----------- | ----------------------------------------------------------------------------------- |
| Auth MS     | Usuarios, login, tokens, roles, permisos, scopes                                    |
| Gateway     | Entrada única, routing, validación, rate limits, auditoría                          |
| API General | Casos, personas, identidades, análisis de negocio, vínculos de caso                 |
| Scr4per v3  | Scraping social, herramientas agenticas, observaciones, raw evidence, grafo técnico |
| Sábanas MS  | Carga, parsing y análisis de sábanas telefónicas                                    |
| DB          | Persistencia estructurada y aislamiento por usuario/caso/análisis                   |

---

### 2.2 IA exclusiva del scraper en el MVP

Para el MVP, la IA estará limitada al dominio del scraper.

La IA de Scr4per puede decidir:

```text id="ru930s"
qué herramienta de scraping ejecutar
qué lote solicitar
qué post analizar
cuándo detenerse
qué nodos priorizar dentro del análisis
cómo construir el grafo técnico
qué advertencias reportar
```

La IA de Scr4per no puede decidir ni ejecutar directamente:

```text id="llade9"
crear caso
crear persona física
crear identidad oficial de negocio
vincular persona a caso
vincular identidad a persona
asignar colaboradores
modificar permisos
compartir análisis entre casos
fusionar personas
fusionar identidades
procesar sábanas telefónicas
```

Esas acciones pertenecen a la API General o a otros microservicios.

---

### 2.3 IA OSINT futura

A futuro puede existir una **IA global del sistema OSINT**, pero esa IA deberá operar como un cliente autorizado del sistema.

La IA OSINT futura deberá:

```text id="mnw517"
autenticarse
actuar bajo un usuario, organización, caso o service account controlado
enviar solicitudes por Gateway
respetar scopes y permisos
no acceder directo a DB
no invocar APIs internas saltándose Gateway
dejar auditoría completa
pedir confirmación humana para acciones críticas
```

Flujo futuro correcto:

```text id="o4wn22"
IA OSINT global
  ↓
Gateway
  ↓
Auth / autorización
  ↓
API General / Scr4per / Sábanas / otros microservicios
```

Flujos prohibidos:

```text id="in3mis"
IA OSINT → DB directa

IA OSINT → API General interna saltándose Gateway

IA OSINT → Scr4per interno sin autenticación ni auditoría
```

---

## 3. Arquitectura del ecosistema

```text id="hpa2cp"
┌──────────────────────────────────────────────┐
│              Frontend / Cliente               │
└──────────────────────┬───────────────────────┘
                       │
┌──────────────────────▼───────────────────────┐
│                   Gateway                     │
│ Auth delegation, routing, rate limits, audit   │
└──────────────┬───────────────┬────────────────┘
               │               │
               ▼               ▼
┌──────────────────────┐ ┌──────────────────────┐
│     API General       │ │      Scr4per v3       │
│ casos                 │ │ scraping tools        │
│ personas              │ │ IA del scraper        │
│ identidades           │ │ Playwright/Scrapling  │
│ análisis negocio      │ │ raw evidence          │
│ vínculos de caso      │ │ graph técnico         │
└──────────────────────┘ └──────────────────────┘
               │               │
               ▼               ▼
┌──────────────────────┐ ┌──────────────────────┐
│       Auth MS         │ │      Sábanas MS       │
│ usuarios/roles        │ │ telefonía/registros   │
│ permisos/scopes       │ │ análisis de sábanas   │
└──────────────────────┘ └──────────────────────┘
```

---

## 4. Frontera funcional de Scr4per v3

### 4.1 Scr4per recibe contexto

Scr4per v3 debe recibir solicitudes ya contextualizadas por la API General o por el Gateway.

Ejemplo de input:

```json id="vxiwox"
{
  "id_analisis": 123,
  "id_usuario": 7,
  "id_caso": 55,
  "id_identidad_digital_objetivo": 999,
  "platform": "instagram",
  "username_or_url": "juanp",
  "limits": {
    "max_followers": 100,
    "max_following": 100,
    "max_posts": 10,
    "max_comments_per_post": 50
  },
  "visibility_policy": "case"
}
```

`id_caso` puede ser `null` si el análisis es autónomo.

---

### 4.2 Scr4per produce observaciones

Scr4per debe devolver y persistir:

```text id="b2hhxh"
tool_runs
raw_evidence
observaciones de identidad
identidades observadas
relaciones observadas
publicaciones
comentarios
reacciones
graph_snapshot
resumen técnico
warnings
estado del análisis
```

Ejemplo de output:

```json id="y4b0w1"
{
  "id_analisis": 123,
  "status": "completed_partial",
  "observed_identities_count": 180,
  "observed_relationships_count": 240,
  "posts_count": 10,
  "comments_count": 350,
  "raw_evidence_refs": [991, 992, 993],
  "graph_snapshot_id": 456,
  "warnings": [
    "followers_limited_by_budget",
    "comments_partial"
  ]
}
```

---

## 5. Alcance mínimo del MVP

### 5.1 Plataforma inicial

Se recomienda iniciar con una sola plataforma.

Opción recomendada:

```text id="tbj1jd"
Instagram
```

Motivos:

```text id="hix7ji"
permite validar perfil, followers, following, posts y comentarios
permite probar network-first
permite probar DOM fallback
permite validar normalización multi-entidad
tiene suficiente complejidad para probar la arquitectura
```

No se recomienda iniciar el MVP con Facebook, Instagram y X al mismo tiempo.

---

### 5.2 Capacidades mínimas

El MVP debe soportar:

```text id="oq55yf"
1. Recibir una solicitud de análisis desde API General/Gateway.
2. Ejecutar análisis autónomo o ligado a caso según contexto recibido.
3. Resolver técnicamente la identidad objetivo desde username o URL.
4. Obtener snapshot básico de perfil.
5. Obtener lote limitado de followers.
6. Obtener lote limitado de following.
7. Obtener posts recientes.
8. Obtener comentarios de posts seleccionados.
9. Persistir tool_runs.
10. Persistir raw evidence.
11. Persistir observaciones normalizadas.
12. Persistir vínculos sociales observados.
13. Generar grafo JSON desde un análisis.
14. Reportar progreso y estado.
15. Ejecutar un flujo agentico básico limitado al scraper.
```

---

### 5.3 Fuera del MVP

No incluir en Scr4per v3 MVP:

```text id="a4idxv"
crear casos
crear personas físicas
crear identidades oficiales de negocio
gestionar permisos
gestionar colaboradores
gestionar organizaciones
gestionar departamentos
procesar sábanas telefónicas
generar reportes finales del sistema OSINT
compartir análisis entre casos
fusión de personas
fusión de identidades
atribución definitiva identidad-persona
IA OSINT global
```

Tampoco incluir inicialmente:

```text id="jciqg2"
multi-plataforma completa
expansión profunda de grafos
detección avanzada de comunidades
vector DB completa
reportes PDF
UI completa de investigación
```

---

## 6. Definición del MVP

El MVP de Scr4per v3 es:

```text id="kbl7oh"
Un microservicio de scraping social capaz de recibir un análisis creado por la API General,
usar una IA interna limitada para seleccionar herramientas de adquisición,
recolectar observaciones mediante Playwright + Scrapling,
guardar raw evidence y datos normalizados,
respetar el contexto de visibilidad recibido,
y generar un grafo JSON auditable desde la información recolectada.
```

---

## 7. Flujo MVP

```text id="ga7q8s"
1. Usuario solicita análisis desde Frontend.
2. Gateway valida token y envía solicitud a API General.
3. API General crea o valida redes.analisis.
4. API General llama a Scr4per v3 vía Gateway o canal autorizado.
5. Scr4per recibe id_analisis, usuario, caso opcional, identidad objetivo y límites.
6. IA interna de Scr4per planifica herramientas de scraping.
7. Tool Executor ejecuta herramientas.
8. Playwright + Scrapling capturan API/GraphQL/DOM fallback.
9. Scr4per guarda tool_run, raw_evidence y observaciones.
10. Scr4per genera graph_snapshot.
11. Scr4per reporta estado a API General.
12. API General presenta resultados al usuario según permisos.
```

---

## 8. Criterios de éxito del MVP

El MVP se considera exitoso si:

```text id="tkpjso"
1. Scr4per puede ejecutar un análisis recibido desde API General.
2. Scr4per no necesita crear casos, personas ni identidades de negocio.
3. La IA interna solo ejecuta herramientas de scraping permitidas.
4. Cada herramienta genera un tool_run auditable.
5. Cada raw JSON útil queda asociado a análisis y herramienta.
6. Cada observación puede rastrearse hasta un tool_run.
7. El grafo se genera desde datos persistidos.
8. Un análisis puede existir sin caso.
9. Un análisis puede estar ligado a caso mediante contexto externo.
10. Dos usuarios no ven análisis ajenos si API General/Gateway no lo permite.
11. Fallos parciales no rompen todo el análisis.
12. El sistema devuelve resumen técnico y grafo.
```

---

## 9. Herramientas mínimas de Scr4per v3 MVP

### 9.1 `resolve_scraping_target`

Resuelve técnicamente un input de scraping.

No crea caso ni persona física.

Puede usar o devolver referencia a una identidad digital recibida.

Input:

```json id="3n5609"
{
  "id_analisis": 123,
  "platform": "instagram",
  "username_or_url": "juanp",
  "id_identidad_digital_objetivo": 999
}
```

Output:

```json id="mkqwae"
{
  "platform": "instagram",
  "username": "juanp",
  "profile_url": "https://instagram.com/juanp",
  "identity_ref": "instagram:juanp",
  "id_identidad_digital_objetivo": 999,
  "confidence": 0.98
}
```

Responsabilidades:

```text id="ewqfxc"
normalizar URL o username
validar plataforma
preparar referencia técnica
no atribuir a persona física
no crear caso
```

---

### 9.2 `fetch_profile_snapshot`

Obtiene snapshot básico de perfil.

Recolecta:

```text id="js1buu"
username observado
nombre público observado
bio/descripción observada
foto de perfil observada
URL observada
métricas públicas disponibles
links externos
estado del perfil
raw_json
```

Persiste:

```text id="qfb0m9"
redes.tool_run
redes.raw_evidence
redes.identidad_observacion
```

---

### 9.3 `fetch_followers_batch`

Obtiene un lote limitado de seguidores.

Persiste:

```text id="90ksrg"
redes.tool_run
redes.raw_evidence
personas.identidad_digital si aplica como identidad observada
redes.vinculo_social
```

Regla:

```text id="qz1xxe"
No marcar automáticamente followers como relevantes para el caso.
Solo registrar observaciones del análisis.
```

---

### 9.4 `fetch_following_batch`

Obtiene un lote limitado de cuentas seguidas.

Mismo patrón que followers.

---

### 9.5 `fetch_recent_posts`

Obtiene publicaciones recientes de la identidad objetivo.

Persiste:

```text id="i0i8u4"
redes.tool_run
redes.raw_evidence
redes.publicacion
```

---

### 9.6 `fetch_post_comments_batch`

Obtiene comentarios de un post seleccionado.

Persiste:

```text id="jyjvz4"
redes.tool_run
redes.raw_evidence
redes.comentario
personas.identidad_digital para autores observados
redes.vinculo_social tipo commented_on_post
```

---

### 9.7 `build_graph_from_analysis`

Construye un grafo JSON a partir de datos persistidos para `id_analisis`.

Incluye:

```text id="24avak"
nodos de identidad
nodos de publicación opcionales
aristas follows/following/commented
pesos
evidencia
tool_run_id
analysis_id
observed_at
```

Persiste:

```text id="57tmcy"
redes.graph_snapshot
```

---

## 10. IA interna de Scr4per

### 10.1 Rol

La IA interna del scraper actúa como planner operativo de adquisición.

Puede:

```text id="v0grcx"
leer el contexto del análisis recibido
consultar capacidades de plataforma
seleccionar herramientas de scraping
priorizar posts o lotes
decidir cuándo detenerse por presupuesto
proponer advertencias
generar resumen técnico
solicitar continuación si requiere aprobación
```

No puede:

```text id="lxzr30"
crear caso
crear persona
crear identidad oficial
vincular persona a caso
vincular identidad a persona
modificar ACL global
compartir análisis
exportar evidencia sensible fuera del flujo autorizado
```

---

### 10.2 Planner MVP

El planner inicial puede ser híbrido:

```text id="j0i5b0"
reglas determinísticas + LLM limitado
```

Flujo base:

```text id="u0behj"
1. resolve_scraping_target
2. fetch_profile_snapshot
3. fetch_recent_posts
4. fetch_post_comments_batch para N posts
5. fetch_followers_batch
6. fetch_following_batch
7. build_graph_from_analysis
8. summarize_scraping_analysis
```

---

### 10.3 Límites del agente MVP

```json id="5lx74f"
{
  "max_tool_calls": 10,
  "max_followers": 100,
  "max_following": 100,
  "max_posts": 10,
  "max_comments_per_post": 50,
  "max_depth": 1,
  "expand_related_profiles": false
}
```

El MVP no debe expandir automáticamente perfiles relacionados.

---

## 11. Playwright + Scrapling

### 11.1 Playwright

Playwright debe ser el runtime principal para:

```text id="d35e7s"
navegador headless
storage_state/cookies
contextos aislados
interceptación request/response
captura de GraphQL/API calls
navegación mínima
screenshots/tracing opcional
manejo de sesiones
```

---

### 11.2 Scrapling

Scrapling se integra como apoyo para:

```text id="dx0kmr"
parsing adaptativo
extracción de raw JSON
fetch auxiliar
crawling controlado
DOM fallback más resistente
normalización auxiliar
utilidades stealth moderadas
```

Scrapling no reemplaza el runtime principal de navegador.

---

### 11.3 Estrategia de extracción

Cada herramienta debe usar:

```text id="jhs5t6"
1. Network/API/GraphQL first.
2. Raw JSON capture.
3. Normalización.
4. Persistencia.
5. DOM fallback si falla network.
6. Resultado partial_success si hay datos incompletos.
```

---

## 12. Modelo de datos mínimo para Scr4per v3

### 12.1 Tablas existentes usadas

```text id="z237xl"
redes.analisis
personas.identidad_digital
redes.plataforma
redes.vinculo_social
redes.tipo_vinculo_social
redes.publicacion
redes.comentario
redes.reaccion
casos.caso_analisis
```

Nota:

```text id="kv3tn0"
Scr4per puede referenciar id_caso o id_identidad_digital recibidos,
pero la creación/gestión de esos registros pertenece a API General.
```

---

### 12.2 Tablas nuevas mínimas

#### `redes.tool_run`

```sql id="jv3ipk"
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

---

#### `redes.raw_evidence`

```sql id="rsycyu"
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

---

#### `redes.identidad_observacion`

```sql id="w77zzd"
CREATE TABLE redes.identidad_observacion (
  id_identidad_observacion bigserial PRIMARY KEY,
  id_analisis bigint NOT NULL REFERENCES redes.analisis(id_analisis),
  id_tool_run bigint REFERENCES redes.tool_run(id_tool_run),
  id_identidad_digital bigint REFERENCES personas.identidad_digital(id_identidad_digital),
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

---

#### `redes.graph_snapshot`

```sql id="h9kjbd"
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

---

## 13. API de Scr4per v3 MVP

Scr4per debe exponer endpoints propios, pero normalmente serán llamados a través del Gateway.

### 13.1 Iniciar análisis de scraping

```http id="hcrpde"
POST /scraper/analyses/{id_analisis}/run
```

Input:

```json id="fr4ob5"
{
  "id_usuario": 7,
  "id_caso": 55,
  "id_identidad_digital_objetivo": 999,
  "platform": "instagram",
  "username_or_url": "juanp",
  "limits": {
    "max_followers": 100,
    "max_following": 100,
    "max_posts": 10,
    "max_comments_per_post": 50
  }
}
```

---

### 13.2 Ejecutar herramienta explícita

```http id="kln2ql"
POST /scraper/analyses/{id_analisis}/tools/{tool_name}/run
```

Este endpoint puede usarse para debugging, pruebas o ejecución controlada desde API General.

---

### 13.3 Consultar estado

```http id="vqs3cf"
GET /scraper/analyses/{id_analisis}/status
```

---

### 13.4 Consultar tool runs

```http id="ouqi37"
GET /scraper/analyses/{id_analisis}/tool-runs
```

---

### 13.5 Generar grafo

```http id="fua8ax"
POST /scraper/analyses/{id_analisis}/graph/build
```

---

## 14. Seguridad y Gateway

### 14.1 Regla principal

Scr4per v3 debe estar detrás del Gateway.

```text id="m3x6za"
Cliente → Gateway → Scr4per
API General → Gateway/canal interno autorizado → Scr4per
```

El scraper no debe exponerse como API pública sin control.

---

### 14.2 Validación

El Gateway/Auth debe validar:

```text id="qc29fz"
token
usuario
organización
scopes
permisos
rate limits
id_caso si aplica
id_analisis
```

Scr4per también debe validar el contexto recibido y rechazar solicitudes incompletas o inconsistentes.

---

### 14.3 Scopes sugeridos

```text id="b22413"
scraper:run
scraper:read
scraper:tool:run
scraper:graph:build
scraper:evidence:read
scraper:admin
```

---

## 15. Fases y sprints

## Fase 0 — Alineación de microservicios

Duración sugerida:

```text id="pjw91f"
1 sprint
```

Objetivo:

```text id="d2blms"
Definir claramente contratos entre Gateway, API General y Scr4per.
```

Tareas:

```text id="csu09b"
- Definir qué crea API General.
- Definir qué recibe Scr4per.
- Definir scopes del scraper.
- Definir endpoints de Scr4per.
- Definir payload estándar de análisis.
- Definir contrato de respuesta de Scr4per.
- Definir eventos de progreso.
```

Criterio de salida:

```text id="r1ilkb"
API General puede crear un análisis y llamar a Scr4per con contexto completo.
```

---

## Fase 1 — Preparación técnica Scr4per v3

Duración sugerida:

```text id="vpxo88"
1 sprint
```

Tareas:

```text id="dbl63g"
- Crear módulo scraper_v3.
- Crear Tool Registry.
- Crear Tool Executor.
- Crear schemas base.
- Crear contrato estándar de herramientas.
- Crear mecanismo inicial de auditoría.
- Crear herramienta dummy.
```

Criterio de salida:

```text id="w1wkvx"
Se puede ejecutar una herramienta dummy y generar un registro tool_run.
```

---

## Fase 2 — Modelo de datos MVP

Duración sugerida:

```text id="wb1c3w"
1 sprint
```

Tareas:

```text id="si7mw6"
- Crear migración redes.tool_run.
- Crear migración redes.raw_evidence.
- Crear migración redes.identidad_observacion.
- Crear migración redes.graph_snapshot.
- Crear repositorios de persistencia.
- Asegurar índices por id_analisis e id_tool_run.
```

Criterio de salida:

```text id="bqm817"
Scr4per puede guardar auditoría, raw evidence, observaciones y graph_snapshot.
```

---

## Fase 3 — Runtime Playwright + Scrapling

Duración sugerida:

```text id="upb4al"
1 a 2 sprints
```

Tareas:

```text id="4ksw1k"
- Crear BrowserPool.
- Crear SessionPool.
- Crear NetworkCaptureManager.
- Crear ScraplingAdapter.
- Implementar raw JSON capture.
- Implementar DOM fallback básico.
- Implementar errores tipados.
- Implementar partial_success.
```

Criterio de salida:

```text id="cic2iw"
Una herramienta puede navegar, capturar network responses y guardar raw evidence.
```

---

## Fase 4 — Plataforma inicial

Duración sugerida:

```text id="nkeep1"
2 sprints
```

Plataforma recomendada:

```text id="olh0uc"
Instagram
```

Tareas:

```text id="b2ztqy"
- Crear platform adapter.
- Declarar capabilities.
- Implementar resolve_scraping_target.
- Implementar fetch_profile_snapshot.
- Implementar fetch_followers_batch.
- Implementar fetch_following_batch.
- Implementar fetch_recent_posts.
- Implementar fetch_post_comments_batch.
- Crear normalizadores.
```

Criterio de salida:

```text id="xmmx8t"
Scr4per puede analizar una identidad de Instagram y persistir observaciones.
```

---

## Fase 5 — API de Scr4per

Duración sugerida:

```text id="lq948w"
1 sprint
```

Tareas:

```text id="q2myfz"
- Crear endpoint de ejecución de análisis.
- Crear endpoint de ejecución de herramienta.
- Crear endpoint de estado.
- Crear endpoint de tool_runs.
- Crear endpoint de grafo.
- Validar payloads.
- Validar scopes/contexto.
```

Criterio de salida:

```text id="cp3s3k"
API General puede iniciar un análisis de Scr4per mediante endpoint controlado.
```

---

## Fase 6 — IA interna del scraper MVP

Duración sugerida:

```text id="dcji7v"
1 a 2 sprints
```

Tareas:

```text id="jewk9l"
- Crear ScraperAgentPlanner.
- Crear políticas de selección de herramientas.
- Crear límites de autonomía.
- Crear prompt interno del scraper.
- Registrar decisiones del agente.
- Ejecutar flujo base.
```

Flujo base:

```text id="dlbcdo"
resolve_scraping_target
fetch_profile_snapshot
fetch_recent_posts
fetch_post_comments_batch
fetch_followers_batch
fetch_following_batch
build_graph_from_analysis
summarize_scraping_analysis
```

Criterio de salida:

```text id="g37vjt"
La IA del scraper puede ejecutar un análisis completo dentro de límites.
```

---

## Fase 7 — Graph Builder MVP

Duración sugerida:

```text id="op3c0x"
1 sprint
```

Tareas:

```text id="xyefgb"
- Construir nodos de identidad.
- Construir nodos de posts opcionales.
- Construir aristas.
- Calcular pesos simples.
- Adjuntar evidence metadata.
- Guardar graph_snapshot.
```

Criterio de salida:

```text id="irpnac"
El grafo puede reconstruirse desde datos persistidos.
```

---

## Fase 8 — Seguridad, aislamiento y pruebas E2E

Duración sugerida:

```text id="ufgshf"
1 sprint
```

Tareas:

```text id="6mp5ay"
- Validar que Scr4per no expone análisis sin contexto autorizado.
- Probar análisis autónomo.
- Probar análisis con caso.
- Probar dos usuarios analizando la misma identidad.
- Probar fallo parcial.
- Probar generación de grafo.
- Probar raw evidence.
- Probar auditoría de tool_run.
```

Criterio de salida:

```text id="wvvsyy"
El MVP es demostrable de punta a punta y no mezcla información entre usuarios/casos.
```

---

## 16. Cronograma sugerido

Plan completo:

```text id="sec9t1"
Sprint 0: Alineación de microservicios
Sprint 1: Preparación técnica Scr4per v3
Sprint 2: Modelo de datos MVP
Sprint 3: Runtime Playwright + Scrapling
Sprint 4: Plataforma inicial — perfil e identidad
Sprint 5: Plataforma inicial — followers/following/posts/comments
Sprint 6: API Scr4per
Sprint 7: IA interna del scraper
Sprint 8: Graph Builder
Sprint 9: Seguridad, aislamiento y pruebas E2E
```

Duración aproximada:

```text id="u5eh68"
8 a 10 sprints
```

---

## 17. MVP reducido

Si se quiere validar rápido:

### Sprint A

```text id="o1kzih"
Tool Registry
Tool Executor
tool_run
raw_evidence
Playwright runtime
Scrapling adapter
```

### Sprint B

```text id="4hq5r7"
resolve_scraping_target
fetch_profile_snapshot
identidad_observacion
```

### Sprint C

```text id="bcjjlx"
fetch_followers_batch
fetch_following_batch
vinculo_social
```

### Sprint D

```text id="dgs43n"
build_graph_from_analysis
IA interna básica
resumen técnico
```

Este MVP reducido no incluye posts ni comentarios inicialmente.

---

## 18. Roadmap posterior al MVP

### Fase 9 — Segunda plataforma

Agregar Facebook o X usando el mismo contrato de herramientas.

---

### Fase 10 — RAG interno del scraper

Agregar contexto técnico del scraper:

```text id="x5kbk9"
análisis previos accesibles
identidades observadas en análisis accesibles
errores históricos por plataforma
capabilities
tool_runs anteriores
patrones de extracción
```

Este RAG debe estar limitado al dominio de Scr4per y respetar visibilidad.

---

### Fase 11 — RAG OSINT global

Esto no pertenece al MVP de Scr4per.

Debe vivir en API General o en un servicio IA OSINT futuro.

---

### Fase 12 — IA OSINT global

A futuro, la IA OSINT global podrá:

```text id="xe1l2r"
crear casos
crear personas
crear identidades
pedir análisis a Scr4per
pedir análisis a Sábanas
consultar contexto permitido
generar reportes
```

Pero siempre:

```text id="4t3unw"
autenticada
pasando por Gateway
con scopes
con auditoría
sin acceso directo a DB
sin acceso directo a APIs internas
```

---

### Fase 13 — Atribución identidad-persona

Debe vivir principalmente en API General, no en Scr4per.

Scr4per puede aportar evidencias observadas, pero no validar atribuciones definitivas.

---

### Fase 14 — Expansión agentica controlada

Permitir que la IA del scraper expanda perfiles relacionados bajo límites y/o aprobación.

---

## 19. Backlog técnico priorizado

### P0 — indispensable para MVP

```text id="jqnmmp"
contrato API General → Scr4per
Tool Registry
Tool Executor
redes.tool_run
redes.raw_evidence
redes.identidad_observacion
redes.graph_snapshot
Playwright runtime
Scrapling adapter
resolve_scraping_target
fetch_profile_snapshot
fetch_followers_batch
fetch_following_batch
build_graph_from_analysis
scopes scraper básicos
```

---

### P1 — MVP completo

```text id="b2kkjb"
fetch_recent_posts
fetch_post_comments_batch
IA interna del scraper
resumen técnico
partial_success
normalizadores versionados
eventos de progreso
DOM fallback
```

---

### P2 — posterior al MVP

```text id="o80qhl"
segunda plataforma
RAG interno del scraper
detección de nodos prioritarios
expansión depth 2
post reactions
post shares
ranking avanzado de grafo
```

---

### P3 — fuera de Scr4per

```text id="tg5c2z"
crear casos
crear personas
crear identidades de negocio
atribución identidad-persona
colaboradores
roles/permisos globales
sábanas
IA OSINT global
reportes finales
```

---

## 20. Riesgos y mitigaciones

### Riesgo: Scr4per vuelve a convertirse en monolito

Mitigación:

```text id="js5yaf"
mantener frontera clara
no crear casos/personas desde scraper
API General como dueña del dominio OSINT
Scr4per solo adquisición social
```

---

### Riesgo: IA del scraper excede su dominio

Mitigación:

```text id="ryxwgf"
Tool Registry limitado
scopes scraper
sin herramientas de negocio
sin acceso directo a API General
sin acceso directo a DB fuera de su dominio
```

---

### Riesgo: fuga entre casos

Mitigación:

```text id="qr0ns1"
id_analisis obligatorio
id_usuario obligatorio
id_caso opcional pero explícito
lecturas filtradas por API General/Gateway
no exposición directa de Scr4per público
```

---

### Riesgo: APIs internas de redes cambian

Mitigación:

```text id="qk5bdx"
network-first
DOM fallback
raw evidence
normalizadores versionados
extractores por plataforma
partial_success
```

---

## 21. Entregable final del MVP

El MVP debe entregar:

```text id="sj09lo"
1. Microservicio Scr4per v3 detrás de Gateway.
2. Contrato con API General.
3. Una plataforma integrada.
4. Herramientas semánticas básicas.
5. IA interna limitada al scraper.
6. Playwright + Scrapling runtime.
7. Persistencia trazable.
8. Raw evidence.
9. Observaciones normalizadas.
10. Grafo JSON técnico.
11. Resumen técnico del análisis.
12. Seguridad mínima por contexto recibido.
```

---

## 22. Definición final actualizada

El MVP de Scr4per v3 es:

```text id="lxh5tt"
Un microservicio de adquisición social que recibe análisis creados por la API General,
usa una IA interna exclusivamente para decidir herramientas de scraping,
ejecuta Playwright + Scrapling con estrategia network-first,
guarda raw evidence y observaciones trazables,
genera un grafo técnico por análisis,
y opera siempre detrás del Gateway sin administrar directamente casos, personas, identidades o permisos globales.
```

La frase guía actualizada:

```text id="tkgb19"
Scr4per observa y produce evidencia.
API General administra el dominio OSINT.
Gateway controla el acceso.
Auth define permisos.
La IA del MVP solo razona dentro del scraper.
```

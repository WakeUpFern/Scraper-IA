# AGENTS.md

## Project role

This repository contains Scr4per v3, the social acquisition microservice of the NAAT OSINT system.

Scr4per is not the whole OSINT system. It only performs social scraping, observation persistence, raw evidence capture, tool execution, and technical graph generation.

## Architecture boundaries

Scr4per MUST NOT:
- create cases
- create physical persons
- create official business identities
- manage users, roles, departments, organizations, or permissions
- process phone records / sabanas
- bypass the Gateway
- access the API General directly unless a documented internal contract allows it
- access production databases directly from tests or prototypes

Scr4per MAY:
- receive id_analisis, id_usuario, id_caso optional, platform, target identity input, limits, and visibility policy
- execute scraping tools
- use Playwright and Scrapling
- capture network/API/GraphQL responses
- use DOM fallback
- persist tool_run, raw_evidence, identidad_observacion, vinculo_social, publicaciones, comentarios, reacciones, graph_snapshot
- generate technical graph JSON

## AI behavior

Use Ponytail-style engineering:
- write the least code that satisfies the contract
- reuse existing modules before creating new ones
- avoid unnecessary abstractions
- do not introduce frameworks unless required
- prefer simple functions over classes when one function is enough
- add tests for behavior that matters

But do not be lazy with:
- security
- input validation
- permission boundaries
- auditability
- tool_run logging
- raw evidence traceability
- error handling
- timeouts

## Grounded docs

Before using external APIs or libraries, consult grounded-docs.

Required docs:
- Playwright Python
- Scrapling
- NVIDIA NIM / API Catalog
- FastAPI
- Pydantic v2
- HTTPX
- PostgreSQL JSONB / constraints
- SQLAlchemy or asyncpg, depending on the module
- Alembic if writing migrations

Do not invent methods, parameters, classes, or endpoints. If documentation is missing, stop and report the missing doc.

## Implementation style

- Prefer typed Python.
- Use Pydantic models for API contracts.
- Use async only where the call chain actually benefits from async.
- Keep modules small.
- Keep tool schemas explicit.
- Every scraper tool must return a structured result.
- Every real tool execution must be auditable through tool_run.
- Network-first extraction, DOM fallback.
- No real scraping in unit tests.
- No API keys in code, logs, or tests.

## MVP focus

For the current phase, build only:
- NVIDIA pre-MVP client
- planner JSON
- simulated tools
- Scr4per tool contracts
- one initial platform when ready

Do not build:
- IA OSINT global
- full RAG system
- full gateway
- full auth
- multi-platform scraping
- report generation
- case/person/identity management
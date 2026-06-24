"""
app/schemas.py — Pydantic models para el contrato HTTP del MVP.
"""
from __future__ import annotations
from datetime import datetime
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field


# ---------------------------------------------------------------------------
# Job request
# ---------------------------------------------------------------------------

class JobTarget(BaseModel):
    platform: str = Field(..., pattern="^(facebook|instagram|x)$")
    url_or_username: str


class JobScope(BaseModel):
    profile: bool = True
    friends: bool = False
    followers: bool = False
    following: bool = False
    photos: bool = False
    comments: bool = False
    reactions: bool = False


class JobLimits(BaseModel):
    max_friends: int = 100
    max_followers: int = 1000
    max_following: int = 1000
    max_photos: int = 115
    max_comments_per_post: int = 100


class JobRequest(BaseModel):
    target: JobTarget
    scope: JobScope = Field(default_factory=JobScope)
    limits: JobLimits = Field(default_factory=JobLimits)
    # Correlación opcional para integración futura con Core
    correlation: Optional[Dict[str, Any]] = None


# ---------------------------------------------------------------------------
# Job response / status
# ---------------------------------------------------------------------------

class JobCreated(BaseModel):
    job_id: str
    status: str
    created_at: datetime


class JobProgress(BaseModel):
    step: Optional[str] = None
    counts: Optional[Dict[str, int]] = None


class JobStatus(BaseModel):
    job_id: str
    status: str  # queued | running | persisting | graph_building | completed | failed | cancelled
    platform: str
    target: str
    created_at: datetime
    started_at: Optional[datetime] = None
    finished_at: Optional[datetime] = None
    progress: Optional[JobProgress] = None
    summary: Optional[Dict[str, Any]] = None
    error: Optional[str] = None


# ---------------------------------------------------------------------------
# Graph
# ---------------------------------------------------------------------------

class GraphResponse(BaseModel):
    job_id: str
    graph: Optional[Dict[str, Any]] = None
    built_at: Optional[datetime] = None


class GraphBuildResponse(BaseModel):
    job_id: str
    status: str
    message: str


# ---------------------------------------------------------------------------
# Tool runs
# ---------------------------------------------------------------------------

class ToolRunItem(BaseModel):
    id: int
    tool_name: str
    platform: Optional[str]
    status: str
    started_at: datetime
    finished_at: Optional[datetime]
    error: Optional[str]
    extractor_strategy: Optional[str]


class ToolRunsResponse(BaseModel):
    job_id: str
    tool_runs: List[ToolRunItem]


# ---------------------------------------------------------------------------
# Artifacts
# ---------------------------------------------------------------------------

class ArtifactItem(BaseModel):
    name: str
    type: str  # json | csv | screenshot | log
    path: Optional[str] = None
    size_bytes: Optional[int] = None


class ArtifactsResponse(BaseModel):
    job_id: str
    artifacts: List[ArtifactItem]

"""
Modelos Pydantic para los inputs y outputs de las herramientas de Scr4per v3.
"""

from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field


# 1. resolve_scraping_target
class ResolveTargetInput(BaseModel):
    id_analisis: int
    platform: str
    username_or_url: str
    id_identidad_digital_objetivo: Optional[int] = None

class ResolveTargetOutput(BaseModel):
    platform: str
    username: str
    profile_url: str
    identity_ref: str
    id_identidad_digital_objetivo: Optional[int] = None
    confidence: float


# 2. fetch_profile_snapshot
class FetchProfileInput(BaseModel):
    platform: str
    username: str
    profile_url: str

class FetchProfileOutput(BaseModel):
    username_observado: str
    nombre_publico_observado: str
    descripcion_observada: str
    foto_url_observada: str
    usuario_url_observada: str
    metricas_json: Dict[str, Any] = Field(default_factory=dict)
    links_externos: List[str] = Field(default_factory=list)
    estado_perfil: str = "active"
    extractor_strategy: str  # e.g., 'network_capture' or 'dom_fallback'
    parser_version: str


# 3. fetch_followers_batch
class FetchFollowersInput(BaseModel):
    platform: str
    username: str
    limit: int = 100
    cursor: Optional[str] = None

class FollowerInfo(BaseModel):
    username: str
    nombre_publico: Optional[str] = None
    profile_url: str
    foto_url: Optional[str] = None

class FetchFollowersOutput(BaseModel):
    followers: List[FollowerInfo]
    next_cursor: Optional[str] = None
    total_fetched: int
    extractor_strategy: str
    parser_version: str


# 4. fetch_following_batch
class FetchFollowingInput(BaseModel):
    platform: str
    username: str
    limit: int = 100
    cursor: Optional[str] = None

class FetchFollowingOutput(BaseModel):
    following: List[FollowerInfo]
    next_cursor: Optional[str] = None
    total_fetched: int
    extractor_strategy: str
    parser_version: str


# 5. fetch_recent_posts
class FetchRecentPostsInput(BaseModel):
    platform: str
    username: str
    limit: int = 10

class PostInfo(BaseModel):
    post_id: str
    post_url: str
    content: Optional[str] = None
    published_at: Optional[str] = None
    like_count: int = 0
    comment_count: int = 0
    share_count: int = 0
    raw_data: Dict[str, Any] = Field(default_factory=dict)

class FetchRecentPostsOutput(BaseModel):
    posts: List[PostInfo]
    total_fetched: int
    extractor_strategy: str
    parser_version: str


# 6. fetch_post_comments_batch
class FetchCommentsInput(BaseModel):
    platform: str
    post_id: str
    post_url: str
    limit: int = 50
    cursor: Optional[str] = None

class CommentInfo(BaseModel):
    comment_id: str
    author_username: str
    author_name: Optional[str] = None
    author_profile_url: str
    text: str
    published_at: Optional[str] = None
    like_count: int = 0

class FetchCommentsOutput(BaseModel):
    comments: List[CommentInfo]
    next_cursor: Optional[str] = None
    total_fetched: int
    extractor_strategy: str
    parser_version: str


# 7. build_graph_from_analysis
class BuildGraphInput(BaseModel):
    id_analisis: int

class GraphNode(BaseModel):
    id: str
    label: str
    type: str  # 'identity' or 'post'
    metadata: Dict[str, Any] = Field(default_factory=dict)

class GraphEdge(BaseModel):
    source: str
    target: str
    type: str  # 'follows', 'commented_on_post', etc.
    weight: float
    metadata: Dict[str, Any] = Field(default_factory=dict)

class BuildGraphOutput(BaseModel):
    analysis_id: int
    nodes: List[GraphNode]
    edges: List[GraphEdge]
    observed_at: str


# 8. summarize_scraping_analysis
class SummarizeInput(BaseModel):
    id_analisis: int

class SummarizeOutput(BaseModel):
    analysis_id: int
    summary: str
    total_tool_runs: int
    total_identities_found: int
    total_relationships_found: int
    warnings: List[str] = Field(default_factory=list)

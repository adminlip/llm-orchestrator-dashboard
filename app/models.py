from __future__ import annotations

from datetime import datetime
from typing import Any, Literal

from pydantic import BaseModel, Field


ModelRole = Literal["primary", "backup", "worker"]
ModelStatus = Literal["active", "standby", "failed", "disabled", "promoted"]
PlatformKind = Literal["openai_compatible", "hermes", "openclew", "codeclue", "custom"]


class PlatformConfig(BaseModel):
    id: str
    name: str
    kind: PlatformKind
    base_url: str | None = None
    api_key_env: str | None = None
    transport: str = "openai_chat"
    enabled: bool = True
    metadata: dict[str, Any] = Field(default_factory=dict)


class ModelConfig(BaseModel):
    id: str
    name: str
    role: ModelRole
    status: ModelStatus = "standby"
    model_name: str
    platform_id: str
    priority: int = 0
    temperature: float = 0.3
    max_tokens: int = 2048
    tags: list[str] = Field(default_factory=list)
    system_prompt: str = ""
    last_error: str | None = None
    fail_count: int = 0
    updated_at: datetime = Field(default_factory=datetime.utcnow)


class TaskRequest(BaseModel):
    prompt: str
    primary_model_id: str | None = None
    worker_model_ids: list[str] = Field(default_factory=list)
    strategy: Literal["delegate_then_summarize", "parallel_review"] = "delegate_then_summarize"


class PrimarySwitchRequest(BaseModel):
    model_id: str
    reason: str = "manual switch"


class WorkerResult(BaseModel):
    model_id: str
    model_name: str
    success: bool = True
    output: str
    latency_ms: int = 0
    error: str | None = None


class OrchestrationResult(BaseModel):
    request_id: str
    primary_model_id: str
    primary_model_name: str
    strategy: str
    summary: str
    worker_results: list[WorkerResult]
    failover_triggered: bool = False
    failover_reason: str | None = None
    created_at: datetime = Field(default_factory=datetime.utcnow)


class FailoverEvent(BaseModel):
    id: str
    from_model_id: str
    to_model_id: str
    reason: str
    created_at: datetime = Field(default_factory=datetime.utcnow)


class RegistryState(BaseModel):
    platforms: list[PlatformConfig] = Field(default_factory=list)
    models: list[ModelConfig] = Field(default_factory=list)
    failover_events: list[FailoverEvent] = Field(default_factory=list)
    recent_runs: list[OrchestrationResult] = Field(default_factory=list)

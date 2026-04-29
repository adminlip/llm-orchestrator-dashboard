from __future__ import annotations

import os
from dataclasses import dataclass

import httpx

from app.models import ModelConfig, PlatformConfig, WorkerResult


@dataclass
class PlatformExecutionContext:
    platform: PlatformConfig
    model: ModelConfig


class PlatformAdapter:
    def run(self, ctx: PlatformExecutionContext, prompt: str) -> WorkerResult:
        raise NotImplementedError()


class MockAdapter(PlatformAdapter):
    def run(self, ctx: PlatformExecutionContext, prompt: str) -> WorkerResult:
        content = (
            f"[{ctx.platform.name}/{ctx.model.name}] analyzed prompt: {prompt[:120]}\n"
            f"Result: Mock execution result (no API key configured for {ctx.platform.api_key_env or 'this platform'})."
        )
        return WorkerResult(
            model_id=ctx.model.id,
            model_name=ctx.model.name,
            output=content,
            latency_ms=0,
            success=True,
        )


class OpenAICompatibleAdapter(PlatformAdapter):
    def run(self, ctx: PlatformExecutionContext, prompt: str) -> WorkerResult:
        api_key = os.getenv(ctx.platform.api_key_env or "", "") if ctx.platform.api_key_env else ""
        base_url = (ctx.platform.base_url or "").rstrip("/")
        if not api_key or not base_url:
            return MockAdapter().run(ctx, prompt)

        messages = []
        if ctx.model.system_prompt:
            messages.append({"role": "system", "content": ctx.model.system_prompt})
        messages.append({"role": "user", "content": prompt})

        payload = {
            "model": ctx.model.model_name,
            "messages": messages,
            "temperature": ctx.model.temperature,
            "max_tokens": ctx.model.max_tokens,
        }

        try:
            resp = httpx.post(
                f"{base_url}/chat/completions",
                headers={"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"},
                json=payload,
                timeout=60,
            )
            resp.raise_for_status()
            data = resp.json()
            content = data["choices"][0]["message"]["content"]
            return WorkerResult(
                model_id=ctx.model.id,
                model_name=ctx.model.name,
                output=content,
                success=True,
            )
        except httpx.HTTPStatusError as exc:
            return WorkerResult(
                model_id=ctx.model.id,
                model_name=ctx.model.name,
                output="",
                success=False,
                error=f"HTTP {exc.response.status_code}: {exc.response.text[:200]}",
            )
        except Exception as exc:
            return WorkerResult(
                model_id=ctx.model.id,
                model_name=ctx.model.name,
                output="",
                success=False,
                error=str(exc)[:200],
            )


def build_adapter(platform: PlatformConfig) -> PlatformAdapter:
    if platform.kind in ("openai_compatible", "hermes", "openclew", "codeclue", "custom"):
        api_key = os.getenv(platform.api_key_env or "", "") if platform.api_key_env else ""
        if api_key and platform.base_url:
            return OpenAICompatibleAdapter()
    return MockAdapter()

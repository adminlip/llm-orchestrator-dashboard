from __future__ import annotations

from time import perf_counter
from uuid import uuid4

from app.models import OrchestrationResult, TaskRequest, WorkerResult
from app.platforms import PlatformExecutionContext, build_adapter
from app.registry import RegistryService


class OrchestratorService:
    def __init__(self, registry: RegistryService):
        self.registry = registry

    def run(self, request: TaskRequest) -> OrchestrationResult:
        primary = self.registry.get_model(request.primary_model_id) if request.primary_model_id else self.registry.get_active_primary()
        if primary is None:
            raise ValueError("No primary model configured")

        state = self.registry.load()
        platform_map = {p.id: p for p in state.platforms}
        workers = []
        if request.worker_model_ids:
            workers = [m for m in state.models if m.id in request.worker_model_ids]
        else:
            workers = self.registry.list_workers()

        worker_results: list[WorkerResult] = []
        for worker in workers:
            platform = platform_map.get(worker.platform_id)
            if platform is None or not platform.enabled:
                worker_results.append(
                    WorkerResult(
                        model_id=worker.id,
                        model_name=worker.name,
                        success=False,
                        output="",
                        error="Platform unavailable",
                    )
                )
                continue
            adapter = build_adapter(platform)
            started = perf_counter()
            result = adapter.run(PlatformExecutionContext(platform=platform, model=worker), request.prompt)
            result.latency_ms = int((perf_counter() - started) * 1000)
            worker_results.append(result)

        summary_lines = [
            f"Primary model: {primary.name}",
            f"Strategy: {request.strategy}",
            "",
            "Worker summaries:",
        ]
        for result in worker_results:
            prefix = "OK" if result.success else "FAIL"
            summary_lines.append(f"- [{prefix}] {result.model_name}: {result.output[:180]}")
        summary_lines.append("")
        summary_lines.append("Final summary:")
        summary_lines.append("主模型已读取全部子代理结果，并生成本次汇总结论。这里是 MVP 演示结果，可继续接入真实模型调用。")

        orchestration = OrchestrationResult(
            request_id=str(uuid4()),
            primary_model_id=primary.id,
            primary_model_name=primary.name,
            strategy=request.strategy,
            summary="\n".join(summary_lines),
            worker_results=worker_results,
        )

        state.recent_runs = [orchestration, *state.recent_runs][:20]
        self.registry.save(state)
        return orchestration

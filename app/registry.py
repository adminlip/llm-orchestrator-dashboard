from __future__ import annotations

from pathlib import Path
from uuid import uuid4

from app.models import FailoverEvent, ModelConfig, PlatformConfig, RegistryState
from app.store import JsonStore


class RegistryService:
    def __init__(self, data_path: Path):
        self.store = JsonStore(data_path)
        self._default = RegistryState()

    def load(self) -> RegistryState:
        return self.store.load_model(RegistryState, self._default)

    def save(self, state: RegistryState) -> None:
        self.store.save_model(state)

    def get_platform(self, platform_id: str) -> PlatformConfig | None:
        state = self.load()
        return next((p for p in state.platforms if p.id == platform_id), None)

    def get_model(self, model_id: str) -> ModelConfig | None:
        state = self.load()
        return next((m for m in state.models if m.id == model_id), None)

    def list_primary_candidates(self) -> list[ModelConfig]:
        state = self.load()
        return [m for m in state.models if m.role in ("primary", "backup") and m.status != "disabled"]

    def get_active_primary(self) -> ModelConfig | None:
        state = self.load()
        primary = next((m for m in state.models if m.role == "primary" and m.status == "active"), None)
        if primary:
            return primary
        backups = sorted(
            [m for m in state.models if m.role == "backup" and m.status in ("standby", "promoted", "active")],
            key=lambda item: item.priority,
        )
        return backups[0] if backups else None

    def list_workers(self) -> list[ModelConfig]:
        state = self.load()
        return sorted(
            [m for m in state.models if m.role == "worker" and m.status != "disabled"],
            key=lambda item: item.priority,
        )

    def _enforce_single_active_primary(self, state: RegistryState, active_model_id: str) -> None:
        for model in state.models:
            if model.id == active_model_id:
                model.role = "primary"
                model.status = "active"
            elif model.role == "primary":
                model.role = "backup"
                if model.status == "active":
                    model.status = "standby"

    def set_primary(self, model_id: str, reason: str = "manual switch") -> ModelConfig | None:
        state = self.load()
        target = next((m for m in state.models if m.id == model_id), None)
        if target is None or target.status == "disabled":
            return None

        current = next((m for m in state.models if m.role == "primary" and m.status == "active"), None)
        self._enforce_single_active_primary(state, target.id)

        if current and current.id != target.id:
            state.failover_events.append(
                FailoverEvent(
                    id=str(uuid4()),
                    from_model_id=current.id,
                    to_model_id=target.id,
                    reason=reason,
                )
            )

        self.save(state)
        return target

    def promote_backup(self, reason: str) -> FailoverEvent | None:
        state = self.load()
        current_primary = next((m for m in state.models if m.role == "primary" and m.status == "active"), None)
        candidate = next(
            (m for m in sorted(state.models, key=lambda x: x.priority) if m.role == "backup" and m.status in ("standby", "active")),
            None,
        )
        if not current_primary or not candidate:
            return None

        current_primary.status = "failed"
        current_primary.last_error = reason
        current_primary.fail_count += 1
        current_primary.role = "backup"
        self._enforce_single_active_primary(state, candidate.id)

        event = FailoverEvent(
            id=str(uuid4()),
            from_model_id=current_primary.id,
            to_model_id=candidate.id,
            reason=reason,
        )
        state.failover_events.append(event)
        self.save(state)
        return event

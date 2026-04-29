from __future__ import annotations

import json
from pathlib import Path
from typing import TypeVar

from pydantic import BaseModel

T = TypeVar("T", bound=BaseModel)


class JsonStore:
    def __init__(self, path: Path):
        self.path = path
        self.path.parent.mkdir(parents=True, exist_ok=True)

    def load_raw(self) -> dict:
        if not self.path.exists():
            return {}
        return json.loads(self.path.read_text(encoding="utf-8"))

    def save_raw(self, data: dict) -> None:
        self.path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")

    def load_model(self, model_type: type[T], default: T) -> T:
        if not self.path.exists():
            return default
        return model_type.model_validate(self.load_raw())

    def save_model(self, model: BaseModel) -> None:
        self.save_raw(model.model_dump(mode="json"))

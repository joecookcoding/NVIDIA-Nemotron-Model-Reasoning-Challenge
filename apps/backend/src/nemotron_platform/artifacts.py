from __future__ import annotations

import json
from pathlib import Path
from typing import Any


class ArtifactStore:
    def __init__(self, root: Path):
        self.root = root

    def ensure_root(self) -> None:
        self.root.mkdir(parents=True, exist_ok=True)

    def write_json(self, scope: str, identifier: str, name: str, payload: Any) -> str:
        target_dir = self.root / scope / identifier
        target_dir.mkdir(parents=True, exist_ok=True)
        target_path = target_dir / name
        with target_path.open("w", encoding="utf-8") as handle:
            json.dump(payload, handle, indent=2, sort_keys=True, default=str)
        return str(target_path.relative_to(self.root.parent))

    def write_text(self, scope: str, identifier: str, name: str, payload: str) -> str:
        target_dir = self.root / scope / identifier
        target_dir.mkdir(parents=True, exist_ok=True)
        target_path = target_dir / name
        target_path.write_text(payload, encoding="utf-8")
        return str(target_path.relative_to(self.root.parent))


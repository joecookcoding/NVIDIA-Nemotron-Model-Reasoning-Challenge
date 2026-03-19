#!/usr/bin/env python3
from __future__ import annotations

import json
from pathlib import Path
import sys


def main() -> int:
    if len(sys.argv) != 2:
        print("usage: dedupe_jsonl.py <file.jsonl>")
        return 1

    path = Path(sys.argv[1]).resolve()
    seen: set[str] = set()
    deduped: list[str] = []
    for line in path.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        record = json.loads(line)
        key = str(record.get("prompt", "")).strip().casefold()
        if key in seen:
            continue
        seen.add(key)
        deduped.append(json.dumps(record))

    path.write_text("\n".join(deduped) + ("\n" if deduped else ""), encoding="utf-8")
    print(f"Wrote {len(deduped)} deduplicated records to {path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())


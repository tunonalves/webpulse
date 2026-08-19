#!/usr/bin/env bash
set -euo pipefail
STAMP=$(date +%Y%m%d-%H%M%S)
cp -a configs "configs.backup-${STAMP}"
python3 - <<'PY'
from pathlib import Path
import yaml
for path in Path("configs").glob("*.yaml"):
    data = yaml.safe_load(path.read_text(encoding="utf-8"))
    data.setdefault("reading", {})["min_wait_seconds"] = 3.0
    data["reading"]["max_wait_seconds"] = 6.0
    data.setdefault("session", {})["min_restart_wait_seconds"] = 60
    data["session"]["max_restart_wait_seconds"] = 120
    data.setdefault("browser", {})["headless"] = True
    path.write_text(yaml.safe_dump(data, sort_keys=False, allow_unicode=True), encoding="utf-8")
PY
./manage.sh down || true
./manage.sh up

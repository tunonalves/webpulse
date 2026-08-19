#!/usr/bin/env bash
set -euo pipefail

PROFILES=(latecla mardelplata patagonia revistaque cadenario)
ARGS=()
for p in "${PROFILES[@]}"; do
  ARGS+=(--profile "$p")
done

case "${1:-}" in
  up)
    docker compose "${ARGS[@]}" up -d
    ;;
  down)
    docker compose "${ARGS[@]}" down
    ;;
  ps)
    docker compose "${ARGS[@]}" ps
    ;;
  logs)
    docker compose "${ARGS[@]}" logs --tail="${2:-200}"
    ;;
  follow)
    docker compose "${ARGS[@]}" logs -f
    ;;
  stats)
    docker stats
    ;;
  inspect)
    docker inspect -f '{{.Name}} RestartCount={{.RestartCount}} OOMKilled={{.State.OOMKilled}} ExitCode={{.State.ExitCode}}' $(docker ps -aq)
    ;;
  *)
    echo "Uso: $0 {up|down|ps|logs [N]|follow|stats|inspect}"
    exit 1
    ;;
esac

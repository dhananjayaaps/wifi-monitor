#!/usr/bin/env bash
set -euo pipefail

# Check status of WiFi Monitor services (agent, backend, frontend).

SERVICES=(
  wifi-monitor-agent.service
  wifi-monitor-backend.service
  wifi-monitor-frontend.service
)

for svc in "${SERVICES[@]}"; do
  echo "=== $svc ==="
  systemctl status --no-pager "$svc" || true
  echo
  systemctl is-enabled "$svc" 2>/dev/null || true
  systemctl is-active "$svc" 2>/dev/null || true
  echo ""
done

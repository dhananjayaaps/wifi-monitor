#!/usr/bin/env bash
set -euo pipefail

# Restart WiFi Monitor services (agent, backend, frontend).

SERVICES=(
  wifi-monitor-agent.service
  wifi-monitor-backend.service
  wifi-monitor-frontend.service
)

for svc in "${SERVICES[@]}"; do
  echo "Restarting $svc ..."
  systemctl restart "$svc"
  systemctl is-active "$svc" 2>/dev/null || true
  echo ""
done

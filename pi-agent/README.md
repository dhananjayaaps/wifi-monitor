# Raspberry Pi Agent

This directory holds the Raspberry Pi agent that performs device scanning, traffic monitoring, local caching, and periodic sync to the backend.

Structure:
- src/
  - scanner/ (device discovery)
  - monitor/ (packet capture & aggregation)
  - cache/ (local buffering)
  - config/ (settings)
  - scheduler/ (periodic tasks)
  - utils/ (helpers)
- systemd/ (service unit for autostart)
- tests/ (unit/integration tests)
- logs/ (agent logs)

Next steps:
- Create a Python venv and install `requirements.txt`.
- Implement scanning & monitoring modules.
- Configure systemd service for startup.

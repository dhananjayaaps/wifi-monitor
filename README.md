# WiFi Monitor - IoT Network Usage Monitoring System

An IoT-based solution using Raspberry Pi to monitor Wi-Fi network usage, track devices, and send smart notifications.

## Project Structure

```
wifi-monitor/
├── backend/          # Flask/Django REST API
├── pi-agent/         # Raspberry Pi monitoring agent
├── mobile/           # Flutter mobile application
├── infra/            # Docker, nginx, monitoring configs
├── docs/             # Documentation
├── config/           # Configuration files
├── scripts/          # Utility scripts
└── tests/            # Test suites
```

## Quick Start

### Using Docker
```bash
cd infra
docker-compose up -d
```

### Manual Setup
See [Installation Guide](docs/guides/installation.md)

## Features
- Real-time device detection
- Per-device data usage tracking
- Smart alerts & notifications
- Mobile app (iOS/Android)
- Privacy-focused (no content inspection)

## Documentation
- [Architecture](ARCHITECTURE.md)
- [API Reference](docs/API_REFERENCE.md)
- [Database Schema](docs/DATABASE_SCHEMA.md)
- [Security Guidelines](docs/SECURITY.md)

## Tech Stack
- **Hardware**: Raspberry Pi 3/4
- **Backend**: Flask + PostgreSQL + Redis
- **Mobile**: Flutter
- **Monitoring**: Prometheus + Grafana
- **Notifications**: Firebase Cloud Messaging

## License
TBD

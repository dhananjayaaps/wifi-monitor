# Installation Guide

## Prerequisites
- Raspberry Pi 3/4 with Raspbian OS
- Python 3.9+
- PostgreSQL 13+
- Redis 6+
- Flutter SDK (for mobile)

## Backend Setup
```bash
cd backend
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

## Pi Agent Setup
```bash
cd pi-agent
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
sudo systemctl enable /path/to/systemd/wifi-monitor.service
sudo systemctl start wifi-monitor
```

## Docker Deployment
```bash
cd infra
docker-compose up -d
```

See detailed guides in `/docs/guides/`.

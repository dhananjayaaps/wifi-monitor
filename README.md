# WiFi Monitor - IoT Network Usage Monitoring System

A comprehensive IoT-based solution using Raspberry Pi to monitor WiFi network usage, track device consumption, and provide intelligent analytics for network management.

## 🌟 Project Overview

This system enables real-time monitoring of WiFi usage across all connected devices in a network. Built with a Raspberry Pi agent that collects network metrics and sends them to a centralized backend for processing, analytics, and visualization.

## 🏗️ System Architecture

```
┌─────────────────┐    HTTP/REST    ┌─────────────────┐    HTTP/REST    ┌─────────────────┐
│   Raspberry Pi  │ ──────────────► │     Backend     │ ◄────────────── │   Next.js Web   │
│     Agent       │                 │   (Flask API)   │                 │    Dashboard    │
│                 │                 │                 │                 │                 │
│ • Network Scan  │                 │ • Authentication│                 │ • Device Mgmt   │
│ • Traffic Mon   │                 │ • Device Mgmt   │                 │ • Usage Analytics│
│ • Metrics Coll  │                 │ • Data Caps     │                 │ • Alerts        │
│ • Data Upload   │                 │ • Analytics     │                 │ • Reports       │
└─────────────────┘                 │ • Agent Mgmt    │                 └─────────────────┘
                                    └─────────────────┘
                                             │
                                             ▼
                                    ┌─────────────────┐
                                    │    Database     │
                                    │  (PostgreSQL)   │
                                    │                 │
                                    │ • Users         │
                                    │ • Devices       │
                                    │ • Usage Data    │
                                    │ • Agents        │
                                    │ • Alerts        │
                                    └─────────────────┘
```

## 📁 Project Structure

```
wifi-monitor/
├── backend/              # Flask REST API Backend
│   ├── app/
│   │   ├── api/routes/  # API endpoints (auth, devices, usage, etc.)
│   │   ├── models/      # Database models
│   │   ├── services/    # Business logic
│   │   └── schemas/     # Data validation schemas
│   ├── config/          # Configuration files
│   └── tests/           # Backend tests
├── pi-agent/            # Raspberry Pi Monitoring Agent
│   ├── src/
│   │   ├── agent.py     # Main agent logic
│   │   ├── collector.py # Data collection
│   │   ├── scanner.py   # Network scanning
│   │   └── client.py    # Backend communication
│   ├── config/          # Agent configuration
│   └── systemd/         # Service configuration
├── admin-frontend/      # Next.js Admin Dashboard
│   ├── src/
│   │   ├── app/         # Next.js app router
│   │   ├── components/  # React components
│   │   └── lib/         # Utilities and API client
│   └── public/          # Static assets
├── mobile/              # Future Flutter Mobile App
├── infra/               # Infrastructure (Docker, Nginx, Monitoring)
│   ├── docker/          # Dockerfiles
│   ├── nginx/           # Nginx configuration
│   └── prometheus/      # Monitoring config
├── docs/                # Documentation
└── scripts/             # Development and deployment scripts
```

## ✨ Current Features

### Backend (Flask API)
- **Authentication & Authorization**: JWT-based user management
- **Device Management**: Track and manage network devices with data caps
- **Usage Monitoring**: Real-time and historical usage data collection
- **Agent Management**: Register and monitor Raspberry Pi agents
- **Analytics & Statistics**: Usage trends and insights
- **Alert System**: Configurable notifications for usage thresholds
- **RESTful API**: Comprehensive endpoints for all functionalities

### Pi Agent (Current: Simulator)
- **Network Scanning**: Device discovery and identification
- **Traffic Monitoring**: Real-time bandwidth usage collection
- **Metric Collection**: System health and network statistics
- **Backend Communication**: Secure data transmission to central server
- **Configurable**: Customizable scan intervals and monitoring parameters

### Frontend (Next.js Dashboard)
- **Device Dashboard**: View all connected devices and their usage
- **Real-time Monitoring**: Live usage statistics and graphs
- **Data Cap Management**: Set and monitor device-specific limits
- **Alert Management**: Configure and view system notifications
- **Agent Status**: Monitor connected Raspberry Pi agents
- **Analytics Views**: Usage trends and historical data

## 🚀 Quick Start

### Prerequisites
- Python 3.8+
- Node.js 18+
- PostgreSQL
- Raspberry Pi (for full deployment)

### Using Docker (Recommended)
```bash
cd infra
docker-compose up -d
```

### Manual Development Setup

#### Backend
```bash
cd backend
pip install -r requirements.txt
python run.py
```

#### Frontend
```bash
cd admin-frontend
npm install
npm run dev
```

#### Pi Agent (Simulator)
```bash
cd pi-agent
pip install -r requirements.txt
python run.py
```

## 📊 Tech Stack

### Current Implementation
- **Hardware**: Raspberry Pi 3/4 (planned)
- **Backend**: Flask + SQLAlchemy + PostgreSQL
- **Frontend**: Next.js + TypeScript + Tailwind CSS
- **Agent**: Python + Network Libraries
- **Infrastructure**: Docker + Nginx + Prometheus

### Monitoring & Analytics
- **Metrics**: Custom Flask metrics endpoints
- **Visualization**: Next.js charts and dashboards
- **Alerting**: Built-in notification system

## 🔮 Future Roadmap

### Phase 1: Core Enhancement (Q1 2026)
- [ ] Deploy to actual Raspberry Pi hardware
- [ ] Implement real network traffic monitoring
- [ ] Enhanced device identification and classification
- [ ] Advanced analytics and reporting

### Phase 2: Mobile & Intelligence (Q2 2026)
- [ ] Flutter mobile application
- [ ] Machine Learning prediction models for monthly usage forecasting
- [ ] Advanced anomaly detection
- [ ] Real-time push notifications

### Phase 3: Scale & Features (Q3-Q4 2026)
- [ ] Multi-location support
- [ ] Advanced user roles and permissions
- [ ] API integrations with router firmware
- [ ] Historical data analysis and insights
- [ ] Cost tracking and billing features

## 📚 Documentation

- [System Architecture](ARCHITECTURE.md) - Detailed technical architecture
- [API Reference](docs/API_REFERENCE.md) - Complete API documentation
- [Database Schema](docs/DATABASE_SCHEMA.md) - Database design
- [Security Guidelines](docs/SECURITY.md) - Security implementation
- [Installation Guide](docs/guides/installation.md) - Setup instructions
- [Configuration Guide](docs/guides/configuration.md) - System configuration

## 🛡️ Security & Privacy

- **Privacy-First**: No deep packet inspection or content monitoring
- **Secure Communication**: HTTPS/TLS for all API communications
- **Authentication**: JWT tokens with proper expiration
- **Data Protection**: Encrypted storage of sensitive information
- **Local Processing**: Network scanning performed locally on Pi

## License
TBD

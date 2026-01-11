# Project Folder Structure

```
wifi-monitor/
│
├── ARCHITECTURE.md                    # Detailed system architecture
├── README.md                          # Project overview
├── .gitignore                         # Git ignore patterns
│
├── backend/                           # Backend REST API
│   ├── README.md
│   ├── requirements.txt               # Python dependencies
│   ├── app/
│   │   ├── __init__.py
│   │   ├── api/                       # API routes
│   │   │   ├── __init__.py
│   │   │   └── routes/                # Endpoint handlers
│   │   ├── models/                    # Database models (ORM)
│   │   │   └── __init__.py
│   │   ├── services/                  # Business logic
│   │   │   └── __init__.py
│   │   ├── schemas/                   # Request/response schemas
│   │   │   └── __init__.py
│   │   ├── tasks/                     # Background jobs (Celery)
│   │   │   └── __init__.py
│   │   └── config/                    # Configuration
│   │       └── settings.py
│   ├── migrations/                    # Database migrations
│   │   └── README.md
│   ├── tests/                         # Backend tests
│   └── logs/                          # Application logs
│
├── pi-agent/                          # Raspberry Pi monitoring agent
│   ├── README.md
│   ├── requirements.txt               # Python dependencies
│   ├── src/
│   │   ├── __init__.py
│   │   ├── main.py                    # Entry point
│   │   ├── scanner/                   # Device discovery
│   │   ├── monitor/                   # Traffic monitoring
│   │   ├── cache/                     # Local buffering
│   │   ├── config/                    # Configuration
│   │   │   └── settings.yaml
│   │   ├── scheduler/                 # Task scheduling
│   │   └── utils/                     # Helper utilities
│   ├── systemd/                       # Systemd service files
│   │   └── wifi-monitor.service
│   ├── tests/                         # Pi agent tests
│   └── logs/                          # Agent logs
│
├── mobile/                            # Flutter mobile app
│   ├── README.md
│   └── docs/                          # Mobile app documentation
│
├── infra/                             # Infrastructure & deployment
│   ├── docker-compose.yml             # Docker orchestration
│   ├── docker/
│   │   ├── backend/
│   │   │   └── Dockerfile
│   │   └── pi-agent/
│   │       └── Dockerfile
│   ├── nginx/                         # Nginx reverse proxy config
│   │   └── default.conf
│   ├── prometheus/                    # Prometheus monitoring
│   │   └── prometheus.yml
│   ├── grafana/                       # Grafana dashboards
│   │   └── dashboards.json
│   └── scripts/                       # Deployment scripts
│       └── deploy.sh
│
├── docs/                              # Documentation
│   ├── API_REFERENCE.md               # API documentation
│   ├── DATABASE_SCHEMA.md             # Database schema
│   ├── SECURITY.md                    # Security guidelines
│   ├── guides/                        # User guides
│   │   ├── installation.md
│   │   └── configuration.md
│   ├── api/                           # API endpoint docs
│   ├── dev/                           # Developer docs
│   └── architecture/                  # Architecture diagrams
│
├── config/                            # Global configuration
│   └── .env.example                   # Environment variables template
│
├── scripts/                           # Utility scripts
│   └── dev/                           # Development scripts
│       ├── setup.sh                   # Dev environment setup
│       ├── run_backend.sh             # Run backend locally
│       └── run_pi_agent.sh            # Run Pi agent locally
│
└── tests/                             # Integration tests
    ├── backend/                       # Backend test suites
    │   └── test_placeholder.py
    └── pi-agent/                      # Pi agent test suites
        └── test_placeholder.py
```

## Key Directories Explained

### Backend (`/backend`)
Contains the Flask REST API with modular structure:
- **api/routes**: HTTP endpoint handlers
- **models**: SQLAlchemy ORM models
- **services**: Business logic layer
- **schemas**: Pydantic validation schemas
- **tasks**: Celery background jobs

### Pi Agent (`/pi-agent`)
Raspberry Pi monitoring service:
- **scanner**: Network device detection (nmap/ARP)
- **monitor**: Packet capture & traffic analysis (Scapy)
- **cache**: Local buffering (e.g., SQLite/file-based)
- **scheduler**: Periodic task execution

### Mobile (`/mobile`)
Flutter cross-platform app (iOS/Android) - to be scaffolded with `flutter create`

### Infrastructure (`/infra`)
Deployment and operations:
- Docker containers for all services
- Nginx reverse proxy configuration
- Prometheus + Grafana monitoring stack
- Deployment automation scripts

### Documentation (`/docs`)
Comprehensive project documentation:
- API reference
- Database schema
- Security policies
- User guides
- Developer guides

## Next Steps

1. **Backend**: Implement API routes, models, and services
2. **Pi Agent**: Develop scanner and monitor modules
3. **Mobile**: Run `flutter create .` in `/mobile` directory
4. **Database**: Create migration scripts
5. **Testing**: Expand test coverage
6. **CI/CD**: Set up GitHub Actions workflows

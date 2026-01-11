# IoT Wi-Fi Usage Monitoring System - Detailed Architecture

## 1. System Overview

### High-Level Architecture Diagram
```
┌─────────────────────────────────────────────────────────────────┐
│                      IoT Wi-Fi Monitoring System                │
└─────────────────────────────────────────────────────────────────┘

┌──────────────────┐          ┌──────────────────────┐         ┌─────────────┐
│  HARDWARE LAYER  │          │   BACKEND LAYER      │         │ MOBILE LAYER│
├──────────────────┤          ├──────────────────────┤         ├─────────────┤
│                  │          │                      │         │             │
│ ┌──────────────┐ │          │ ┌──────────────────┐ │         │ Flutter App │
│ │ Raspberry Pi │ │◄─TCP/IP─►│ │   Flask/Django   │ │◄─REST──►│ (iOS/And.)  │
│ │              │ │          │ │   REST API       │ │         │             │
│ └──────────────┘ │          │ └──────────────────┘ │         │             │
│        │         │          │          │           │         │             │
│ ┌──────▼──────┐  │          │ ┌────────▼────────┐  │         │ ┌─────────┐ │
│ │ Network     │  │          │ │ SQLite/         │  │         │ │Firebase │ │
│ │ Scanner     │  │          │ │ PostgreSQL DB   │  │         │ │ (FCM)   │ │
│ │ (nmap)      │  │          │ └────────────────┘  │         │ └─────────┘ │
│ │             │  │          │                      │         │             │
│ │ Traffic     │  │          │ ┌──────────────────┐ │         │ ┌─────────┐ │
│ │ Monitor     │  │          │ │ Data Processing  │ │         │ │Analytics│ │
│ │ (Scapy)     │  │          │ │ Engine           │ │         │ │Dashboard│ │
│ │             │  │          │ └──────────────────┘ │         │ └─────────┘ │
│ └─────────────┘  │          │                      │         │             │
│                  │          │ ┌──────────────────┐ │         │             │
│ ┌──────────────┐ │          │ │ Task Scheduler   │ │         │             │
│ │Config File   │ │          │ │ (Celery/APSchedul)         │             │
│ │(JSON/YAML)   │ │          │ └──────────────────┘ │         │             │
│ └──────────────┘ │          │                      │         │             │
└──────────────────┘          └──────────────────────┘         └─────────────┘
```

---

## 2. Layered Architecture

### 2.1 Hardware Layer (Raspberry Pi)

**Responsibilities:**
- Network device detection and scanning
- Real-time packet capture and analysis
- Local traffic monitoring
- Configuration management
- System health monitoring

**Sub-Components:**

```
┌─────────────────────────────────────────────┐
│         HARDWARE LAYER                      │
├─────────────────────────────────────────────┤
│                                             │
│  ┌──────────────────────────────────────┐   │
│  │ Network Scanner Module               │   │
│  ├──────────────────────────────────────┤   │
│  │ • Device Discovery (nmap, ARP scan) │   │
│  │ • MAC/IP Mapping                    │   │
│  │ • Device State Management           │   │
│  │ • Unknown Device Detection          │   │
│  └──────────────────────────────────────┘   │
│                                             │
│  ┌──────────────────────────────────────┐   │
│  │ Traffic Monitor Module               │   │
│  ├──────────────────────────────────────┤   │
│  │ • Packet Capture (Scapy/tcpdump)    │   │
│  │ • Per-Device Traffic Aggregation    │   │
│  │ • Bandwidth Calculation (U/D)       │   │
│  │ • Flow Analysis                     │   │
│  └──────────────────────────────────────┘   │
│                                             │
│  ┌──────────────────────────────────────┐   │
│  │ Local Cache & Queue Manager          │   │
│  ├──────────────────────────────────────┤   │
│  │ • In-Memory Data Buffer (Redis)     │   │
│  │ • Offline Queue (SQLite)            │   │
│  │ • Sync Scheduler                    │   │
│  └──────────────────────────────────────┘   │
│                                             │
│  ┌──────────────────────────────────────┐   │
│  │ Configuration Manager                │   │
│  ├──────────────────────────────────────┤   │
│  │ • Local Config Persistence          │   │
│  │ • Device Naming & Whitelisting      │   │
│  │ • Scan Interval Management          │   │
│  │ • Router Credentials (encrypted)    │   │
│  └──────────────────────────────────────┘   │
│                                             │
│  ┌──────────────────────────────────────┐   │
│  │ System Monitor                       │   │
│  ├──────────────────────────────────────┤   │
│  │ • CPU/Memory/Disk Usage             │   │
│  │ • Network Interface Health          │   │
│  │ • Service Status                    │   │
│  │ • Logs & Telemetry                  │   │
│  └──────────────────────────────────────┘   │
│                                             │
└─────────────────────────────────────────────┘
```

---

### 2.2 Backend API Layer (Flask/Django + PostgreSQL)

**Responsibilities:**
- RESTful API endpoints for mobile app
- Data aggregation and processing
- User management and authentication
- Notification triggers
- Historical data queries

**Sub-Components:**

```
┌────────────────────────────────────────────────────┐
│         BACKEND API LAYER                          │
├────────────────────────────────────────────────────┤
│                                                    │
│  ┌──────────────────────────────────────────────┐  │
│  │ API Gateway & Request Handler                │  │
│  ├──────────────────────────────────────────────┤  │
│  │ • Route Management                           │  │
│  │ • Request Validation (Pydantic/Marshmallow) │  │
│  │ • Rate Limiting & Throttling                │  │
│  │ • Error Handling & Logging                  │  │
│  └──────────────────────────────────────────────┘  │
│                                                    │
│  ┌──────────────────────────────────────────────┐  │
│  │ Authentication & Authorization Module        │  │
│  ├──────────────────────────────────────────────┤  │
│  │ • JWT Token Management                       │  │
│  │ • User Session Management                    │  │
│  │ • Role-Based Access Control (RBAC)          │  │
│  │ • OAuth 2.0 Integration (optional)          │  │
│  └──────────────────────────────────────────────┘  │
│                                                    │
│  ┌──────────────────────────────────────────────┐  │
│  │ Data Processing Engine                       │  │
│  ├──────────────────────────────────────────────┤  │
│  │ • Real-time Data Aggregation                │  │
│  │ • Statistical Analysis (avg, peak, etc.)    │  │
│  │ • Time-Series Data Processing               │  │
│  │ • Data Normalization & Validation           │  │
│  └──────────────────────────────────────────────┘  │
│                                                    │
│  ┌──────────────────────────────────────────────┐  │
│  │ Business Logic Services                      │  │
│  ├──────────────────────────────────────────────┤  │
│  │ • Device Management Service                 │  │
│  │ • Usage Tracking Service                    │  │
│  │ • Alert & Notification Service              │  │
│  │ • Device Grouping & Categorization Service  │  │
│  │ • Historical Report Generation Service      │  │
│  └──────────────────────────────────────────────┘  │
│                                                    │
│  ┌──────────────────────────────────────────────┐  │
│  │ Task Scheduler & Background Jobs             │  │
│  ├──────────────────────────────────────────────┤  │
│  │ • Celery/APScheduler for Async Tasks        │  │
│  │ • Periodic Data Cleanup                     │  │
│  │ • Report Generation Jobs                    │  │
│  │ • Database Optimization Tasks               │  │
│  └──────────────────────────────────────────────┘  │
│                                                    │
│  ┌──────────────────────────────────────────────┐  │
│  │ Caching Layer                                │  │
│  ├──────────────────────────────────────────────┤  │
│  │ • Redis Cache for Frequent Queries          │  │
│  │ • Cache Invalidation Strategy               │  │
│  │ • Session Cache                             │  │
│  └──────────────────────────────────────────────┘  │
│                                                    │
└────────────────────────────────────────────────────┘
```

---

### 2.3 Data Layer (PostgreSQL + SQLite)

**Responsibilities:**
- Persistent data storage
- Data integrity and ACID compliance
- Efficient querying and indexing
- Backup and recovery

**Database Structure:**

```
┌─────────────────────────────────────────────────┐
│         DATABASE LAYER                          │
├─────────────────────────────────────────────────┤
│                                                 │
│  PostgreSQL (Primary - Backend)                 │
│  ├─ users (user profiles, preferences)         │
│  ├─ devices (discovered network devices)       │
│  ├─ device_stats (hourly/daily aggregates)     │
│  ├─ traffic_logs (raw/processed traffic data)  │
│  ├─ alerts (user-defined alert rules)          │
│  ├─ alert_history (triggered alerts log)       │
│  ├─ notifications (push notification logs)     │
│  ├─ device_metadata (names, groups, tags)      │
│  ├─ system_config (global settings)            │
│  └─ audit_logs (system activity tracking)      │
│                                                 │
│  SQLite (Local - Raspberry Pi)                  │
│  ├─ local_devices (cached device info)         │
│  ├─ offline_queue (pending sync data)          │
│  ├─ cache_traffic (temporary traffic data)     │
│  └─ local_config (device configuration)        │
│                                                 │
└─────────────────────────────────────────────────┘
```

---

### 2.4 Mobile Application Layer (Flutter)

**Responsibilities:**
- User interface and experience
- Real-time data visualization
- Local device state management
- Push notification handling
- Offline capability

**Sub-Components:**

```
┌────────────────────────────────────────────┐
│      MOBILE APPLICATION LAYER              │
├────────────────────────────────────────────┤
│                                            │
│  ┌──────────────────────────────────────┐  │
│  │ UI/Presentation Layer                │  │
│  ├──────────────────────────────────────┤  │
│  │ • Dashboard (real-time overview)     │  │
│  │ • Device List Screen                 │  │
│  │ • Usage Charts & Analytics           │  │
│  │ • Settings & Configuration           │  │
│  │ • Alert Management Screen            │  │
│  │ • Device Details & History           │  │
│  └──────────────────────────────────────┘  │
│                                            │
│  ┌──────────────────────────────────────┐  │
│  │ State Management (Riverpod/Bloc)     │  │
│  ├──────────────────────────────────────┤  │
│  │ • App State Providers                │  │
│  │ • Device State Management            │  │
│  │ • Auth State Management              │  │
│  │ • Real-time Data Sync                │  │
│  └──────────────────────────────────────┘  │
│                                            │
│  ┌──────────────────────────────────────┐  │
│  │ Data Access Layer                    │  │
│  ├──────────────────────────────────────┤  │
│  │ • REST Client (Dio)                  │  │
│  │ • Local Database (Hive/SQLite)       │  │
│  │ • Secure Storage (Flutter Secure)    │  │
│  │ • WebSocket for Real-time Updates    │  │
│  └──────────────────────────────────────┘  │
│                                            │
│  ┌──────────────────────────────────────┐  │
│  │ Services & Utils                     │  │
│  ├──────────────────────────────────────┤  │
│  │ • Firebase Push Notification Handler │  │
│  │ • Offline Sync Manager               │  │
│  │ • Local Notification Service         │  │
│  │ • Analytics & Crash Reporting        │  │
│  │ • Device Info & Permissions          │  │
│  └──────────────────────────────────────┘  │
│                                            │
└────────────────────────────────────────────┘
```

---

### 2.5 Notification Layer (Firebase Cloud Messaging)

**Responsibilities:**
- Push notification delivery
- Notification persistence
- Real-time alert triggering
- Notification analytics

**Flow:**
```
┌─────────────────────────────────────────────────┐
│      NOTIFICATION LAYER                         │
├─────────────────────────────────────────────────┤
│                                                 │
│  Backend Alert Service                          │
│        ↓                                        │
│  ┌──────────────────────────────────────────┐   │
│  │ Alert Evaluation Engine                  │   │
│  │ • Check usage against limits             │   │
│  │ • Evaluate custom conditions             │   │
│  │ • Throttle duplicate alerts              │   │
│  └──────────────────────────────────────────┘   │
│        ↓                                        │
│  ┌──────────────────────────────────────────┐   │
│  │ Firebase Cloud Messaging                 │   │
│  │ • Topic-based subscriptions              │   │
│  │ • Device-specific targets                │   │
│  │ • Notification queuing & retry           │   │
│  └──────────────────────────────────────────┘   │
│        ↓                                        │
│  ┌──────────────────────────────────────────┐   │
│  │ Mobile App FCM Handler                   │   │
│  │ • Foreground/Background handling         │   │
│  │ • Deep linking to relevant screens       │   │
│  │ • Local notification display             │   │
│  └──────────────────────────────────────────┘   │
│                                                 │
└─────────────────────────────────────────────────┘
```

---

## 3. Data Flow Architecture

### 3.1 Device Detection & Tracking Flow

```
┌──────────────────┐
│  Network Scan    │ (Every 5-10 mins)
│  (nmap/ARP)      │
└────────┬─────────┘
         │
         ▼
┌──────────────────────────┐
│ Device Discovery Engine  │
│ • Get MAC addresses      │
│ • Get IP addresses       │
│ • Resolve hostnames      │
│ • Check manufacturer     │
└────────┬─────────────────┘
         │
         ▼
┌──────────────────────────────────┐
│ Local Cache (Redis/SQLite)       │
│ • Store detected devices         │
│ • Compare with previous state    │
│ • Detect new/removed devices     │
└────────┬─────────────────────────┘
         │
         ├─────────────┬────────────────┐
         │             │                │
         ▼             ▼                ▼
    [New Devices] [Changed] [Removed]
         │             │                │
         ▼             ▼                ▼
    ┌─────────────────────────────────────────┐
    │ Backend API Sync                        │
    │ • Persist to PostgreSQL                 │
    │ • Trigger notifications for new devices │
    │ • Update device status                  │
    └─────────────────────────────────────────┘
         │
         ▼
    ┌─────────────────────────────────────────┐
    │ Mobile App Update                       │
    │ • WebSocket push notification           │
    │ • Device list refresh                   │
    │ • Badge/indicator update                │
    └─────────────────────────────────────────┘
```

### 3.2 Traffic Monitoring & Data Usage Flow

```
┌────────────────────────────────┐
│ Packet Capture (Scapy/tcpdump) │ (Continuous)
│ • Capture all network packets  │
│ • Filter DNS, DHCP, etc.       │
└────────┬───────────────────────┘
         │
         ▼
┌────────────────────────────────┐
│ Flow Aggregation               │
│ • Parse IP headers             │
│ • Match packets to devices     │
│ • Determine direction (U/D)    │
│ • Aggregate by time window     │
└────────┬───────────────────────┘
         │
         ▼
┌────────────────────────────────────────┐
│ Local Statistics Accumulation          │
│ (Every 1-5 seconds)                    │
│ • Per-device bytes (upload/download)   │
│ • Session tracking                     │
│ • Flow duration                        │
└────────┬───────────────────────────────┘
         │
         ▼
┌────────────────────────────────────┐
│ Local Cache & Queue (Redis/SQLite) │
│ • Buffer data (1-hour window)      │
│ • Offline persistence             │
└────────┬───────────────────────────┘
         │
    (Every 1-5 minutes - Periodic Sync)
         │
         ▼
┌────────────────────────────────────┐
│ Backend API - Data Upload          │
│ • Send aggregated stats            │
│ • Timestamp & device mapping       │
│ • Compression for efficiency       │
└────────┬───────────────────────────┘
         │
         ▼
┌────────────────────────────────────────┐
│ Data Processing Pipeline               │
│ • Store raw data points                │
│ • Calculate hourly/daily aggregates    │
│ • Compute peak usage, trends           │
│ • Update rolling window statistics     │
└────────┬───────────────────────────────┘
         │
         ▼
┌────────────────────────────────────────┐
│ Alert Evaluation Engine                │
│ • Check against user-defined limits    │
│ • Compare usage thresholds             │
│ • Trigger notifications if threshold   │
└────────┬───────────────────────────────┘
         │
         ▼
┌────────────────────────────────────────┐
│ Mobile App - Real-time Updates         │
│ • WebSocket push new data              │
│ • Update charts/statistics             │
│ • Display alerts/warnings              │
└────────────────────────────────────────┘
```

---

## 4. REST API Architecture

### 4.1 API Endpoints Structure

```
/api/v1/
├── /auth
│   ├── POST   /register
│   ├── POST   /login
│   ├── POST   /logout
│   ├── POST   /refresh-token
│   └── POST   /verify-token
│
├── /devices
│   ├── GET    /                    (list all devices)
│   ├── GET    /{id}                (get device details)
│   ├── PUT    /{id}                (update device info)
│   ├── DELETE /{id}                (remove device)
│   ├── POST   /{id}/group          (add to group)
│   └── GET    /{id}/history        (device usage history)
│
├── /usage
│   ├── GET    /current             (real-time usage)
│   ├── GET    /hourly              (hourly aggregates)
│   ├── GET    /daily               (daily aggregates)
│   ├── GET    /monthly             (monthly aggregates)
│   ├── GET    /device/{id}         (per-device usage)
│   └── GET    /export              (export data)
│
├── /alerts
│   ├── GET    /                    (list alerts)
│   ├── POST   /                    (create alert rule)
│   ├── PUT    /{id}                (update alert rule)
│   ├── DELETE /{id}                (delete alert rule)
│   └── GET    /history             (alert trigger history)
│
├── /notifications
│   ├── GET    /                    (list notifications)
│   ├── PUT    /{id}/read           (mark as read)
│   ├── DELETE /{id}                (delete notification)
│   └── POST   /subscribe           (FCM subscription)
│
├── /stats
│   ├── GET    /bandwidth           (current bandwidth usage)
│   ├── GET    /top-devices         (top data users)
│   ├── GET    /trends              (usage trends)
│   └── GET    /reports             (generate reports)
│
├── /system
│   ├── GET    /health              (system status)
│   ├── GET    /config              (current config)
│   ├── PUT    /config              (update config)
│   └── GET    /logs                (system logs)
│
└── /admin
    ├── GET    /users               (user management)
    ├── DELETE /users/{id}          (delete user)
    └── GET    /audit-logs          (audit trail)
```

### 4.2 Real-time Communication (WebSocket)

```
WebSocket Connection Path: /ws/notifications

Events:
├── device.connected         (new device detected)
├── device.disconnected      (device left network)
├── device.usage.updated     (real-time usage update)
├── alert.triggered          (alert notification)
├── usage.threshold_exceeded (limit exceeded warning)
└── system.config_changed    (config update notification)

Message Format:
{
  "event": "event_type",
  "timestamp": "2026-01-10T10:30:00Z",
  "deviceId": "00:1A:2B:3C:4D:5E",
  "data": { ... event_specific_data ... }
}
```

---

## 5. Module Dependencies & Communication

### 5.1 Module Interaction Diagram

```
┌─────────────────────────────────────────────────────────────┐
│                   SYSTEM ARCHITECTURE                       │
└─────────────────────────────────────────────────────────────┘

                    ┌──────────────────┐
                    │   Mobile App     │
                    │   (Flutter)      │
                    └────────┬─────────┘
                             │
                    (REST API + WebSocket)
                             │
        ┌────────────────────┼────────────────────┐
        │                    │                    │
        ▼                    ▼                    ▼
┌──────────────┐  ┌──────────────────┐  ┌──────────────┐
│ Notification │  │  Backend API     │  │ Task         │
│ Service      │  │  (Flask/Django)  │  │ Scheduler    │
│ (FCM)        │  │                  │  │ (Celery)     │
└──────────────┘  └────────┬─────────┘  └──────────────┘
                           │
                ┌──────────┴──────────┐
                │                    │
                ▼                    ▼
        ┌──────────────┐    ┌──────────────┐
        │   Database   │    │ Cache Layer  │
        │ PostgreSQL   │    │  (Redis)     │
        └──────────────┘    └──────────────┘
                │
      ┌─────────┴────────┐
      │                  │
      ▼                  ▼
┌────────────────┐  ┌──────────────────────┐
│ Raspberry Pi   │  │ Alert Evaluation     │
│ Local Services │  │ Engine               │
│                │  │                      │
│ • Scanner      │  │ • Usage Checking     │
│ • Traffic Mon. │  │ • Alert Triggering   │
│ • Local Cache  │  │ • Notification Queue │
└────────────────┘  └──────────────────────┘
```

---

## 6. Security Architecture

### 6.1 Security Layers

```
┌──────────────────────────────────────────────┐
│         SECURITY ARCHITECTURE                │
├──────────────────────────────────────────────┤
│                                              │
│  NETWORK LAYER SECURITY                      │
│  ├─ HTTPS/TLS for all API communication     │
│  ├─ WebSocket Secure (WSS)                  │
│  ├─ VPN/SSH tunneling for RaspberryPi       │
│  └─ Firewall rules (ufw on Pi)              │
│                                              │
│  AUTHENTICATION & AUTHORIZATION              │
│  ├─ JWT tokens (access + refresh)           │
│  ├─ Password hashing (bcrypt)               │
│  ├─ OAuth 2.0 integration                   │
│  ├─ Role-Based Access Control (RBAC)        │
│  └─ Multi-factor authentication (optional)  │
│                                              │
│  DATA PROTECTION                             │
│  ├─ Database encryption at rest             │
│  ├─ Sensitive data encryption (AES-256)     │
│  ├─ Secure credential storage               │
│  ├─ PII anonymization where possible        │
│  └─ SQL injection prevention                │
│                                              │
│  API SECURITY                                │
│  ├─ Rate limiting & DDoS protection         │
│  ├─ Input validation & sanitization         │
│  ├─ CORS configuration                      │
│  ├─ API versioning                          │
│  └─ Security headers (HSTS, CSP)            │
│                                              │
│  DEVICE/PI SECURITY                          │
│  ├─ SSH key-based authentication only       │
│  ├─ Service isolation (systemd)             │
│  ├─ Minimal port exposure                   │
│  ├─ Regular security updates                │
│  └─ Audit logging                           │
│                                              │
│  APPLICATION SECURITY                        │
│  ├─ Secure dependencies (SBOM scanning)     │
│  ├─ Code security analysis (SonarQube)      │
│  ├─ Secrets management (HashiCorp Vault)    │
│  └─ Penetration testing                     │
│                                              │
└──────────────────────────────────────────────┘
```

### 6.2 Data Privacy

```
PRIVACY MEASURES:
├─ No content inspection (only metadata)
├─ No URL/browsing history capture
├─ Device anonymization options
├─ User consent for data collection
├─ GDPR/data retention compliance
├─ Data deletion policies
├─ Audit trails for access
└─ Transparent privacy policy
```

---

## 7. Scalability & Performance

### 7.1 Performance Optimization

```
┌─────────────────────────────────────────┐
│    PERFORMANCE OPTIMIZATION STRATEGY    │
├─────────────────────────────────────────┤
│                                         │
│  DATA AGGREGATION                       │
│  ├─ 1-min: Raw packet level            │
│  ├─ 5-min: Device aggregation          │
│  ├─ 1-hour: Time-bucket aggregation    │
│  └─ 1-day: Daily rollups (delete raw)  │
│                                         │
│  CACHING STRATEGY                       │
│  ├─ Redis for frequent queries         │
│  ├─ Cache TTL by data freshness need   │
│  ├─ Invalidation on data changes       │
│  └─ Cache warming for common queries   │
│                                         │
│  DATABASE OPTIMIZATION                  │
│  ├─ Strategic indexing on timestamp    │
│  ├─ Partitioning by date               │
│  ├─ Materialized views for reports     │
│  ├─ Connection pooling                 │
│  └─ Query optimization & analysis      │
│                                         │
│  NETWORK OPTIMIZATION                   │
│  ├─ Data compression (gzip)            │
│  ├─ Pagination for list endpoints      │
│  ├─ Lazy loading of data               │
│  ├─ Delta updates instead of full      │
│  └─ Binary protocols for efficiency    │
│                                         │
│  PROCESSING OPTIMIZATION                │
│  ├─ Async background jobs              │
│  ├─ Worker pools for parallel proc.    │
│  ├─ Rate limiting to prevent overload  │
│  └─ Resource monitoring & alerts       │
│                                         │
└─────────────────────────────────────────┘
```

### 7.2 Scalability Path

```
PHASE 1: SINGLE HOUSEHOLD (Current)
└─ 1 Raspberry Pi
└─ SQLite local + PostgreSQL cloud
└─ Flask simple deployment
└─ Supports ~50-100 devices

PHASE 2: MULTI-HOUSEHOLD
└─ Multiple Raspberry Pi instances
└─ Managed PostgreSQL
└─ Docker containerization
└─ Load balancing
└─ Supports 100-1000 homes

PHASE 3: ENTERPRISE SCALE
└─ Kubernetes orchestration
└─ Distributed database (sharding)
└─ Message queues (RabbitMQ/Kafka)
└─ Dedicated analytics cluster
└─ Supports 1000+ installations
```

---

## 8. Technology Stack Rationale

### 8.1 Stack Selection

| Component | Technology | Rationale |
|-----------|-----------|-----------|
| **Hardware** | Raspberry Pi 4 | Low cost, sufficient processing, energy efficient |
| **Network Scanning** | nmap + Scapy | Accurate device detection, Python integration |
| **Traffic Capture** | tcpdump + Scapy | Reliable packet capture, granular analysis |
| **Backend API** | Flask + Flask-RESTful | Lightweight, flexible, Python ecosystem |
| **Database** | PostgreSQL | ACID compliance, rich query capabilities, scaling |
| **Cache** | Redis | Fast in-memory operations, perfect for real-time data |
| **Task Scheduling** | Celery + APScheduler | Background jobs, periodic tasks, distributed |
| **Mobile** | Flutter | Cross-platform (iOS/Android), single codebase |
| **Notifications** | Firebase FCM | Reliable, free tier, cross-platform, topic-based |
| **ORM** | SQLAlchemy | Flexible, migration support, relationship management |
| **API Validation** | Pydantic | Type safety, auto-documentation, validation |
| **Containerization** | Docker | Consistent environments, easy deployment |
| **CI/CD** | GitHub Actions | Free, integrated with GitHub, simple setup |
| **Monitoring** | Prometheus + Grafana | Open source, real-time metrics, alerting |

---

## 9. Deployment Architecture

### 9.1 Development Environment

```
┌─────────────────────────────────────────┐
│      DEVELOPMENT ENVIRONMENT            │
├─────────────────────────────────────────┤
│                                         │
│  LOCAL DEVELOPMENT                      │
│  ├─ Raspberry Pi (staging)              │
│  ├─ Docker Compose (local services)     │
│  ├─ Mock network traffic data           │
│  └─ SQLite for local testing            │
│                                         │
│  CI/CD PIPELINE                         │
│  ├─ GitHub Actions workflows            │
│  ├─ Automated testing                   │
│  ├─ Code quality checks                 │
│  ├─ Security scanning                   │
│  └─ Automated deployment                │
│                                         │
│  STAGING ENVIRONMENT                    │
│  ├─ Separate Raspberry Pi               │
│  ├─ PostgreSQL staging instance         │
│  ├─ Redis cache instance                │
│  └─ Mobile app staging build            │
│                                         │
└─────────────────────────────────────────┘
```

### 9.2 Production Deployment

```
┌──────────────────────────────────────────────────┐
│      PRODUCTION ENVIRONMENT                      │
├──────────────────────────────────────────────────┤
│                                                  │
│  RASPBERRY PI                                    │
│  ├─ systemd service management                  │
│  ├─ Auto-restart on failure                     │
│  ├─ Log aggregation (syslog)                    │
│  └─ Health monitoring                           │
│                                                  │
│  BACKEND INFRASTRUCTURE                         │
│  ├─ VPS/Cloud instance (AWS/DigitalOcean)      │
│  ├─ Gunicorn + Nginx reverse proxy              │
│  ├─ SSL/TLS certificates (Let's Encrypt)        │
│  ├─ Auto-scaling based on load                  │
│  └─ Database backup strategy (daily)            │
│                                                  │
│  DATABASE                                       │
│  ├─ Managed PostgreSQL (RDS/managed service)    │
│  ├─ Automated backups                           │
│  ├─ High availability (read replicas)           │
│  └─ Connection pooling (PgBouncer)              │
│                                                  │
│  MONITORING & LOGGING                           │
│  ├─ Prometheus for metrics                      │
│  ├─ ELK/Splunk for logs                         │
│  ├─ Grafana dashboards                          │
│  ├─ Sentry for error tracking                   │
│  └─ Uptime monitoring (UptimeRobot)            │
│                                                  │
│  BACKUP & DISASTER RECOVERY                     │
│  ├─ Automated daily backups                     │
│  ├─ Geographic redundancy                       │
│  ├─ Regular restore testing                     │
│  └─ RTO/RPO targets defined                     │
│                                                  │
└──────────────────────────────────────────────────┘
```

---

## 10. Configuration Management

### 10.1 Configuration Hierarchy

```
┌──────────────────────────────────────────────────┐
│      CONFIGURATION MANAGEMENT                    │
├──────────────────────────────────────────────────┤
│                                                  │
│  SYSTEM CONFIG (Immutable in code)              │
│  ├─ Default alert thresholds                    │
│  ├─ Scan intervals                              │
│  ├─ Data retention policies                     │
│  └─ API rate limits                             │
│                                                  │
│  ENVIRONMENT CONFIG (Deployment-specific)       │
│  ├─ Database URLs (local vs cloud)              │
│  ├─ API endpoint URLs                           │
│  ├─ Log levels                                  │
│  ├─ Feature flags                               │
│  └─ Stored in .env (not in git)                 │
│                                                  │
│  DYNAMIC CONFIG (User-configurable)             │
│  ├─ Device names & groups                       │
│  ├─ Data limits per device                      │
│  ├─ Custom alert rules                          │
│  ├─ Notification preferences                    │
│  └─ Stored in database (persistent)             │
│                                                  │
│  CONFIG DISTRIBUTION                            │
│  ├─ Pi pulls from backend on startup            │
│  ├─ Real-time updates via WebSocket             │
│  ├─ Graceful fallback to cached config          │
│  └─ Version control for auditing                │
│                                                  │
└──────────────────────────────────────────────────┘
```

---

## 11. Error Handling & Resilience

### 11.1 Resilience Patterns

```
┌─────────────────────────────────────────────┐
│      ERROR HANDLING & RESILIENCE            │
├─────────────────────────────────────────────┤
│                                             │
│  NETWORK FAILURES                           │
│  ├─ Retry logic with exponential backoff    │
│  ├─ Circuit breaker pattern                 │
│  ├─ Fallback to local cache                 │
│  ├─ Queue failed uploads for later retry    │
│  └─ Graceful degradation                    │
│                                             │
│  DATABASE FAILURES                          │
│  ├─ Connection pooling & retries            │
│  ├─ Read replicas for failover              │
│  ├─ Local cache for critical data           │
│  ├─ Transaction rollback on errors          │
│  └─ Alerting on failures                    │
│                                             │
│  SERVICE FAILURES                           │
│  ├─ Health check endpoints                  │
│  ├─ Automatic service restart               │
│  ├─ Dead-letter queues for failed jobs      │
│  ├─ Graceful shutdown procedures            │
│  └─ Log aggregation & alerting              │
│                                             │
│  DATA VALIDATION & CONSISTENCY              │
│  ├─ Input validation at API boundary        │
│  ├─ Data type checking                      │
│  ├─ Range validation                        │
│  ├─ Duplicate detection                     │
│  └─ Reconciliation jobs                     │
│                                             │
│  MONITORING & ALERTING                      │
│  ├─ Real-time dashboards                    │
│  ├─ Threshold-based alerts                  │
│  ├─ Error rate monitoring                   │
│  ├─ Performance degradation detection       │
│  └─ On-call escalation policies             │
│                                             │
└─────────────────────────────────────────────┘
```

---

## 12. API Design Principles

### 12.1 RESTful Principles

```
CONSISTENCY:
├─ Versioned API (/api/v1/, /api/v2/)
├─ Consistent naming conventions
├─ Standard HTTP methods (GET, POST, PUT, DELETE)
├─ Standard status codes (200, 201, 400, 401, 403, 404, 500)
└─ Consistent response format

PAGINATION:
├─ Limit/Offset pattern for lists
├─ Default limit: 20, max: 100
├─ Cursor-based for large datasets
└─ Include total count in metadata

FILTERING & SORTING:
├─ Query parameters for filters
├─ Field-based sorting (?sort=created_at:desc)
├─ Multi-field filtering
└─ Field selection (?fields=id,name)

ERROR RESPONSES:
├─ Consistent error format
├─ Error codes for categorization
├─ Descriptive messages
└─ Request ID for tracking

EXAMPLE REQUEST/RESPONSE:
GET /api/v1/devices?limit=10&offset=0&sort=name:asc

Response:
{
  "status": "success",
  "data": [ ... device objects ... ],
  "meta": {
    "total": 45,
    "limit": 10,
    "offset": 0,
    "has_more": true
  },
  "timestamp": "2026-01-10T10:30:00Z"
}
```

---

## 13. Testing Architecture

### 13.1 Testing Strategy

```
┌─────────────────────────────────────────────┐
│         TESTING ARCHITECTURE                │
├─────────────────────────────────────────────┤
│                                             │
│  UNIT TESTS                                 │
│  ├─ Individual function testing             │
│  ├─ Coverage target: >80%                   │
│  ├─ pytest framework                        │
│  └─ Mock external dependencies              │
│                                             │
│  INTEGRATION TESTS                          │
│  ├─ Module interaction testing              │
│  ├─ Database operations                     │
│  ├─ API endpoint testing                    │
│  └─ Test database with fixtures             │
│                                             │
│  END-TO-END TESTS                           │
│  ├─ Full workflow testing                   │
│  ├─ Mobile app UI testing                   │
│  ├─ Real device detection flow              │
│  └─ Alert triggering workflow               │
│                                             │
│  PERFORMANCE TESTS                          │
│  ├─ Load testing (k6/Locust)               │
│  ├─ Stress testing                          │
│  ├─ Baseline latency measurements           │
│  └─ Resource usage profiling                │
│                                             │
│  SECURITY TESTS                             │
│  ├─ SQL injection testing                   │
│  ├─ XSS prevention                          │
│  ├─ Authentication bypass attempts          │
│  └─ OWASP Top 10 compliance                 │
│                                             │
│  DEVICE TESTS (Raspberry Pi)                │
│  ├─ Network scanning accuracy               │
│  ├─ Packet capture reliability              │
│  ├─ Sync reliability                        │
│  └─ Resource consumption tests              │
│                                             │
└─────────────────────────────────────────────┘
```

---

## 14. Monitoring & Observability

### 14.1 Observability Strategy

```
┌─────────────────────────────────────────────────┐
│      MONITORING & OBSERVABILITY                 │
├─────────────────────────────────────────────────┤
│                                                 │
│  METRICS (Prometheus)                           │
│  ├─ Application Metrics                         │
│  │  ├─ API response time (p50, p95, p99)       │
│  │  ├─ Request rate & error rate               │
│  │  ├─ Data processing latency                 │
│  │  └─ Queue depth & processing time           │
│  │                                             │
│  ├─ System Metrics                             │
│  │  ├─ CPU/Memory/Disk usage                   │
│  │  ├─ Network bandwidth                       │
│  │  ├─ Database connection pool stats          │
│  │  └─ Cache hit/miss rates                    │
│  │                                             │
│  ├─ Business Metrics                           │
│  │  ├─ Active users                            │
│  │  ├─ Devices monitored                       │
│  │  ├─ Data points collected                   │
│  │  └─ Alerts triggered                        │
│  │                                             │
│  └─ Alerting Rules                             │
│     ├─ High error rate (>5%)                   │
│     ├─ High latency (p95 > 1s)                 │
│     ├─ Service unavailability                  │
│     ├─ Database connection exhaustion          │
│     └─ Disk space critical                     │
│                                                 │
│  LOGGING (ELK Stack)                            │
│  ├─ Application logs (structured JSON)         │
│  ├─ Access logs                                │
│  ├─ Error logs with stack traces               │
│  ├─ Audit logs for compliance                  │
│  └─ Log aggregation & analysis                 │
│                                                 │
│  DISTRIBUTED TRACING (Jaeger)                   │
│  ├─ Request flow tracing                       │
│  ├─ Service dependency mapping                 │
│  ├─ Performance bottleneck identification      │
│  └─ Distributed error tracking                 │
│                                                 │
│  DASHBOARDS (Grafana)                           │
│  ├─ System health dashboard                    │
│  ├─ Application performance dashboard          │
│  ├─ User activity dashboard                    │
│  └─ Custom business metrics dashboard          │
│                                                 │
│  ALERTING                                       │
│  ├─ Slack/Email notifications                  │
│  ├─ PagerDuty integration (on-call)           │
│  ├─ Escalation policies                        │
│  └─ Post-incident analytics                    │
│                                                 │
└─────────────────────────────────────────────────┘
```

---

## 15. Documentation & Knowledge Base

### 15.1 Documentation Structure

```
/docs
├── ARCHITECTURE.md              (this file)
├── API_REFERENCE.md             (API documentation)
├── DATABASE_SCHEMA.md           (schema details)
├── DEPLOYMENT.md                (deployment guide)
├── SECURITY.md                  (security policies)
├── TROUBLESHOOTING.md           (common issues)
├── CONTRIBUTING.md              (dev guidelines)
│
├── /guides
│   ├── installation.md
│   ├── configuration.md
│   ├── monitoring_setup.md
│   └── scaling_guide.md
│
├── /api
│   ├── authentication.md
│   ├── devices.md
│   ├── usage.md
│   ├── alerts.md
│   └── notifications.md
│
├── /dev
│   ├── local_setup.md
│   ├── testing_guide.md
│   ├── debugging.md
│   └── release_process.md
│
└── /architecture
    ├── data_flow.md
    ├── system_design.md
    └── security_architecture.md
```

---

## 16. Project Timeline & Milestones

### 16.1 Development Phases

```
PHASE 1: FOUNDATION (Weeks 1-4)
├─ Raspberry Pi setup & network tools
├─ Device detection module
├─ Local data storage (SQLite)
├─ Basic configuration management
└─ Deliverable: Basic device scanner

PHASE 2: BACKEND CORE (Weeks 5-8)
├─ Flask API scaffold
├─ Database schema & migrations
├─ Traffic capture & aggregation
├─ Data persistence layer
└─ Deliverable: Backend API with data collection

PHASE 3: FRONTEND & REAL-TIME (Weeks 9-12)
├─ Flutter mobile app UI
├─ API integration (REST + WebSocket)
├─ Real-time data visualization
├─ Local state management
└─ Deliverable: Functional mobile app (beta)

PHASE 4: ALERTS & NOTIFICATIONS (Weeks 13-15)
├─ Alert rule engine
├─ Firebase FCM integration
├─ Notification service
├─ Mobile notification handling
└─ Deliverable: Full alert system

PHASE 5: TESTING & OPTIMIZATION (Weeks 16-18)
├─ Unit & integration tests
├─ Load testing
├─ Security testing
├─ Performance optimization
└─ Deliverable: Test coverage >80%, stable release

PHASE 6: DEPLOYMENT & DOCS (Weeks 19-20)
├─ Production environment setup
├─ Deployment automation (CI/CD)
├─ Documentation
├─ User guides
└─ Deliverable: Production-ready system
```

---

## Summary

This architecture provides:

✅ **Scalability**: From single household to multiple installations
✅ **Reliability**: Redundancy, failover, and error handling
✅ **Security**: Multi-layer security with privacy focus
✅ **Performance**: Optimized data flow and caching strategies
✅ **Maintainability**: Clear module separation and documentation
✅ **Extensibility**: Modular design for future features
✅ **Observability**: Comprehensive monitoring and logging
✅ **User Experience**: Real-time updates, responsive UI, smart notifications

The architecture balances complexity with practicality, suitable for an IoT system at scale while remaining implementable with standard technologies.

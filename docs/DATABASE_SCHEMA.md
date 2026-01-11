# Database Schema

## Tables

### users
- id (PK)
- email
- password_hash
- created_at
- updated_at

### devices
- id (PK)
- mac_address (unique)
- ip_address
- hostname
- manufacturer
- device_type
- first_seen
- last_seen
- is_active

### device_stats
- id (PK)
- device_id (FK)
- timestamp
- bytes_uploaded
- bytes_downloaded
- total_bytes
- session_duration

### alerts
- id (PK)
- user_id (FK)
- device_id (FK, nullable)
- alert_type
- threshold_value
- is_enabled

### alert_history
- id (PK)
- alert_id (FK)
- device_id (FK)
- triggered_at
- resolved_at
- value_at_trigger

### notifications
- id (PK)
- user_id (FK)
- message
- notification_type
- is_read
- created_at

See detailed schema in `backend/migrations/`.

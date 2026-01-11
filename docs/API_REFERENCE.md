# API Reference

See `/docs/api/` for detailed endpoint documentation:
- [Authentication](./authentication.md)
- [Devices](./devices.md)
- [Usage](./usage.md)
- [Alerts](./alerts.md)
- [Notifications](./notifications.md)

Base URL: `http://your-server:8000/api/v1`

All requests require Bearer token authentication:
```
Authorization: Bearer <your_jwt_token>
```

Response format:
```json
{
  "status": "success",
  "data": {...},
  "meta": {...},
  "timestamp": "2026-01-10T10:30:00Z"
}
```

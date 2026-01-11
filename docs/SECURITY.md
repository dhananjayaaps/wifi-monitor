# Security Guidelines

## Authentication
- JWT tokens with expiration
- Refresh token rotation
- Strong password policies (bcrypt hashing)

## Network Security
- All traffic over HTTPS/TLS
- WebSocket connections over WSS
- Firewall rules on Raspberry Pi

## Data Protection
- No content inspection (metadata only)
- MAC address anonymization options
- Encrypted database connections
- Secure credential storage

## API Security
- Rate limiting (100 req/min per user)
- Input validation on all endpoints
- SQL injection prevention (ORM)
- CORS configuration

## Pi Agent Security
- SSH key-based authentication only
- Minimal port exposure
- Service isolation
- Regular security updates

## Privacy Compliance
- User consent required
- Data retention policies (90 days)
- GDPR-compliant data deletion
- Transparent privacy policy

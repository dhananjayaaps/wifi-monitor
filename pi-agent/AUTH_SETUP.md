# Pi Agent Authentication Setup

The Pi Agent now uses username/password authentication instead of hardcoded API keys.

## How It Works

1. **Configure Credentials**: Set your backend user credentials in `config.yaml`
2. **Automatic Login**: On startup, the agent:
   - Logs in with email/password to get a JWT token
   - Registers itself as an agent using the JWT
   - Receives a fresh API key
   - Uses that API key for all subsequent requests

## Configuration

Edit [config.yaml](config.yaml):

```yaml
# Authentication credentials
auth:
  email: "your-email@example.com"
  password: "your-password"
```

## Environment Variables (Optional)

You can also use the `.env.example` file as a template for environment-based configuration.

## First-Time Setup

1. **Create a backend user account**:
   ```bash
   curl -X POST http://localhost:5000/api/v1/auth/register \
     -H "Content-Type: application/json" \
     -d '{"email": "admin@wifi.com", "password": "admin123"}'
   ```

2. **Update config.yaml** with those credentials

3. **Run the agent**:
   ```bash
   python run.py
   ```

The agent will automatically authenticate and start monitoring.

## Security Notes

- API keys are generated fresh on each agent startup
- Keys are created via the backend's secure `secrets.token_urlsafe(32)` method
- Credentials should be stored securely (use environment variables in production)
- Each agent registration creates a new API key linked to your user account

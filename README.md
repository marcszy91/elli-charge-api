# Elli Charging API

A reverse-engineered API for the Elli Wallbox, based on traffic analysis of the iPhone app.

## Features

- OAuth2 PKCE authentication
- Query charging stations
- Retrieve charging sessions (active and historical)
- Current charging power and energy consumption
- FastAPI backend for easy integration
- Docker support for containerized deployment
- Production-ready setup with Nginx reverse proxy

## Quick Start

### Local Development

1. Clone the repository

2. Install dependencies:
```bash
pip install -r requirements.txt
```

3. Create `.env` file:
```bash
cp .env.example .env
```

4. Add your credentials to `.env`:
```env
ELLI_EMAIL=your.email@example.com
ELLI_PASSWORD=your_password
```

5. Run the test client:
```bash
python scripts/test_client.py
```

### Development with VSCode

This project includes VSCode configuration for an optimal development experience:

- **Auto-formatting**: Code is automatically formatted with Black on save
- **Auto-linting**: Flake8 runs automatically to catch issues
- **Import sorting**: isort organizes imports on save
- **Debug configurations**: Press F5 to debug the FastAPI server

Required VSCode extensions (will be recommended automatically):
- Python
- Black Formatter
- isort
- Flake8
- Docker

### Docker Deployment

#### Development Mode

Simple setup without Nginx:

```bash
docker-compose up -d
```

#### Production Mode

Production-ready setup with Nginx reverse proxy, rate limiting, and security headers:

```bash
docker-compose -f docker-compose.production.yml up -d
```

Or build manually:

```bash
docker build -f Dockerfile.production -t elli-charging-api:production .
docker run -p 80:80 --env-file .env elli-charging-api:production
```

**Production features:**
- Nginx reverse proxy with rate limiting
- 4 Uvicorn workers for better performance
- Security headers (X-Frame-Options, CSP, etc.)
- Gzip compression
- Health check endpoint
- Supervisor for process management
- Resource limits (CPU/Memory)

## API Documentation

Start the FastAPI server:

```bash
cd src
uvicorn api.main:app --reload
```

Or set PYTHONPATH:

```bash
export PYTHONPATH=src  # On Windows: set PYTHONPATH=src
uvicorn api.main:app --reload
```

Interactive API documentation is available at:
- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

## Project Structure

```
elli-charge-api/
├── src/
│   ├── elli_api_client/       # Core API client package
│   │   ├── __init__.py       # Package exports
│   │   ├── client.py         # Elli API Client with OAuth2 PKCE
│   │   ├── models.py         # Pydantic data models
│   │   └── config.py         # Settings management
│   └── api/                   # FastAPI application
│       ├── __init__.py
│       └── main.py           # FastAPI routes and endpoints
├── scripts/
│   └── test_client.py        # Test/demo script
├── tests/                     # Unit tests (future)
├── docker/
│   ├── nginx.conf            # Nginx configuration
│   └── supervisord.conf      # Supervisor configuration
├── .vscode/                  # VSCode configuration
│   ├── launch.json          # Debug configurations
│   ├── settings.json        # Editor settings
│   └── extensions.json      # Recommended extensions
├── .github/workflows/        # CI/CD pipelines
│   ├── ci.yml              # Linting and formatting checks
│   ├── docker-build.yml    # Docker image builds
│   └── release-please.yml  # Automated releases
├── requirements.txt          # Python dependencies
├── requirements-dev.txt      # Development dependencies
├── Dockerfile                # Development Docker image
├── Dockerfile.production     # Production Docker image with Nginx
├── docker-compose.yml        # Development compose
├── docker-compose.production.yml # Production compose
├── .pre-commit-config.yaml  # Pre-commit hooks
├── pyproject.toml           # Python project config
├── .env.example             # Environment template
└── README.md                # This file
```

## Technical Details

### Authentication

The Elli API uses Auth0 with OAuth2 PKCE flow:

1. **Authorization Request** with PKCE challenge
2. **Username/Password Login** via Auth0
3. **Authorization Code** is returned
4. **Token Exchange** with PKCE verifier for access token

### API Endpoints (Original)

Base URL: `https://api.elli.eco`

- `GET /chargeathome/v1/stations` - Charging stations
- `GET /chargeathome/v1/charging-sessions` - Charging sessions
- `GET /chargeathome/v1/charging-sessions/accumulated` - Accumulated data
- `GET /chargeathome/v1/locations` - Locations
- `GET /scheduler-consumer/v1/stations/{id}/scheduled-charging-settings` - Scheduled charging

### Production Architecture

```
┌─────────────┐
│   Client    │
└──────┬──────┘
       │
       │ HTTP/HTTPS
       │
┌──────▼──────────────────────────┐
│     Nginx (Port 80/443)         │
│  - Rate Limiting                │
│  - Security Headers             │
│  - Gzip Compression             │
│  - SSL Termination (if enabled) │
└──────┬──────────────────────────┘
       │
       │ HTTP (127.0.0.1:8000)
       │
┌──────▼──────────────────────────┐
│   Uvicorn (4 workers)           │
│   FastAPI Application           │
└─────────────────────────────────┘
```

## MID Meter & Billing

The Elli Wallbox has a MID-certified meter for legally compliant measurements. The API provides:

- `accumulated_energy_wh`: Charged energy in Wh
- RFID card assignment for user-specific billing
- Start/End timestamps for charging sessions

This data can be used for company expense reports.

## Development

### Pre-commit Hooks

Install pre-commit hooks to ensure code quality:

```bash
pip install -r requirements-dev.txt
pre-commit install --hook-type commit-msg --hook-type pre-commit
```

This will automatically:
- Format code with Black
- Sort imports with isort
- Lint with Flake8
- Validate conventional commits

### Running Checks Manually

```bash
# Format code
black .
isort .

# Lint
flake8 .

# All pre-commit hooks
pre-commit run --all-files
```

## PyPI Package

The `elli_api_client` is available as a standalone Python package on PyPI:

```bash
pip install elli-api-client
```

**Use in your projects:**
```python
from elli_api_client import ElliAPIClient

client = ElliAPIClient()
token = client.login("email@example.com", "password")
stations = client.get_stations()
```

See [PYPI_PUBLISHING.md](PYPI_PUBLISHING.md) for publishing details.

## Roadmap

- [x] PyPI package publication
- [ ] Refresh token handling
- [ ] Start/stop charging features
- [ ] WebSocket support for live updates
- [ ] Historical data and statistics
- [ ] Unit tests with mocked API calls

## Contributing

This project uses conventional commits for changelog generation and versioning.

Please follow the [Conventional Commits](https://www.conventionalcommits.org/) specification for all commit messages.

See [CONTRIBUTING.md](CONTRIBUTING.md) for detailed guidelines.

## Disclaimer

- This API was created through reverse engineering of the official Elli iPhone app
- Not officially supported by Elli/Volkswagen
- Use at your own risk
- Client ID and other constants may change

## License

MIT

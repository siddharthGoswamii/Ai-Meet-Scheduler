# Teams Meeting Scheduler - Backend API

FastAPI backend for Microsoft Teams Meeting Scheduler with Microsoft Graph API integration.

## Features

- ✅ Microsoft OAuth 2.0 authentication
- ✅ Microsoft Graph API integration for Teams meetings
- ✅ RESTful API endpoints for meeting management
- ✅ PostgreSQL database with async SQLAlchemy
- ✅ JWT token-based authentication
- ✅ Encrypted token storage
- ✅ Comprehensive error handling
- ✅ API documentation with Swagger/OpenAPI

## Tech Stack

- **Framework**: FastAPI 0.109.0
- **Database**: PostgreSQL with asyncpg
- **ORM**: SQLAlchemy 2.0 (async)
- **Authentication**: MSAL (Microsoft Authentication Library)
- **API Client**: httpx (async)
- **Validation**: Pydantic v2
- **Security**: python-jose, cryptography

## Project Structure

```
backend/
├── app/
│   ├── api/              # API endpoints
│   │   ├── auth.py       # Authentication endpoints
│   │   └── meetings.py   # Meeting CRUD endpoints
│   ├── core/             # Core configuration
│   │   └── config.py     # Settings management
│   ├── db/               # Database configuration
│   │   └── database.py   # DB session and engine
│   ├── models/           # SQLAlchemy models
│   │   ├── user.py
│   │   ├── meeting.py
│   │   ├── meeting_attendee.py
│   │   └── meeting_reminder.py
│   ├── schemas/          # Pydantic schemas
│   │   ├── user.py
│   │   └── meeting.py
│   ├── services/         # Business logic
│   │   ├── auth_service.py
│   │   └── graph_service.py
│   └── main.py           # Application entry point
├── tests/                # Test files
├── .env.example          # Environment variables template
├── requirements.txt      # Python dependencies
└── README.md            # This file
```

## Prerequisites

- Python 3.10 or higher
- PostgreSQL 14 or higher
- Microsoft Azure AD application (for OAuth)
- Microsoft 365 account with Teams

## Setup Instructions

### 1. Clone and Navigate

```bash
cd backend
```

### 2. Create Virtual Environment

```bash
# Windows
python -m venv venv
venv\Scripts\activate

# Linux/Mac
python3 -m venv venv
source venv/bin/activate
```

### 3. Install Dependencies

```bash
pip install -r requirements.txt
```

### 4. Set Up PostgreSQL Database

```bash
# Create database
createdb teams_scheduler

# Or using psql
psql -U postgres
CREATE DATABASE teams_scheduler;
\q
```

### 5. Configure Environment Variables

Copy `.env.example` to `.env` and update values:

```bash
cp .env.example .env
```

Edit `.env` with your configuration:

```env
# Application
APP_NAME=Teams Meeting Scheduler
DEBUG=True
ENVIRONMENT=development

# Database
DATABASE_URL=postgresql+asyncpg://username:password@localhost:5432/teams_scheduler

# Microsoft Azure AD (Get from Azure Portal)
AZURE_CLIENT_ID=your_client_id
AZURE_CLIENT_SECRET=your_client_secret
AZURE_TENANT_ID=your_tenant_id
AZURE_REDIRECT_URI=http://localhost:8000/api/auth/callback

# JWT Secret (Generate a secure random string)
SECRET_KEY=your_secret_key_here

# Encryption Key (Generate using: python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())")
ENCRYPTION_KEY=your_32_byte_encryption_key

# CORS
CORS_ORIGINS=http://localhost:3000,http://localhost:5173
```

### 6. Generate Encryption Key

```bash
python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"
```

Copy the output to `ENCRYPTION_KEY` in `.env`

### 7. Register Azure AD Application

1. Go to [Azure Portal](https://portal.azure.com)
2. Navigate to **Azure Active Directory** > **App registrations**
3. Click **New registration**
4. Configure:
   - Name: `Teams Meeting Scheduler`
   - Supported account types: `Accounts in this organizational directory only`
   - Redirect URI: `Web` - `http://localhost:8000/api/auth/callback`
5. Click **Register**
6. Copy **Application (client) ID** → `AZURE_CLIENT_ID`
7. Copy **Directory (tenant) ID** → `AZURE_TENANT_ID`
8. Go to **Certificates & secrets** > **New client secret**
9. Copy the secret value → `AZURE_CLIENT_SECRET`
10. Go to **API permissions**:
    - Add **Microsoft Graph** permissions:
      - `User.Read` (Delegated)
      - `Calendars.ReadWrite` (Delegated)
      - `OnlineMeetings.ReadWrite` (Delegated)
    - Click **Grant admin consent**

### 8. Run Database Migrations

The application will automatically create tables on startup. Alternatively, use Alembic:

```bash
# Initialize Alembic (first time only)
alembic init alembic

# Create migration
alembic revision --autogenerate -m "Initial migration"

# Apply migration
alembic upgrade head
```

### 9. Run the Application

```bash
# Development mode with auto-reload
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

# Or using Python
python -m app.main
```

The API will be available at:
- API: http://localhost:8000
- Swagger Docs: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

## API Endpoints

### Authentication

- `GET /api/auth/login` - Get Microsoft OAuth login URL
- `GET /api/auth/callback` - OAuth callback handler
- `POST /api/auth/refresh` - Refresh access token
- `POST /api/auth/logout` - Logout user

### Meetings

- `POST /api/meetings` - Create new meeting
- `GET /api/meetings` - List meetings (with filters and pagination)
- `GET /api/meetings/{meeting_id}` - Get meeting details
- `PATCH /api/meetings/{meeting_id}` - Update meeting
- `DELETE /api/meetings/{meeting_id}` - Cancel meeting

### Health Check

- `GET /` - Root endpoint
- `GET /health` - Health check

## API Usage Examples

### 1. Login Flow

```bash
# Step 1: Get authorization URL
curl http://localhost:8000/api/auth/login

# Step 2: User visits the URL and authorizes
# Step 3: User is redirected to callback with code
# Step 4: Exchange code for tokens (automatic)
```

### 2. Create Meeting

```bash
curl -X POST http://localhost:8000/api/meetings \
  -H "Authorization: Bearer YOUR_JWT_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "title": "Team Standup",
    "description": "Daily standup meeting",
    "start_time": "2024-05-15T10:00:00Z",
    "end_time": "2024-05-15T10:30:00Z",
    "timezone": "UTC",
    "attendees": [
      {
        "email": "user@example.com",
        "display_name": "John Doe",
        "is_required": true
      }
    ],
    "is_online": true
  }'
```

### 3. List Meetings

```bash
curl -X GET "http://localhost:8000/api/meetings?page=1&page_size=20" \
  -H "Authorization: Bearer YOUR_JWT_TOKEN"
```

### 4. Cancel Meeting

```bash
curl -X DELETE http://localhost:8000/api/meetings/{meeting_id} \
  -H "Authorization: Bearer YOUR_JWT_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "cancellation_message": "Meeting cancelled due to conflict",
    "send_cancellation": true
  }'
```

## Testing

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=app --cov-report=html

# Run specific test file
pytest tests/test_meetings.py
```

## Deployment

### Production Checklist

1. ✅ Set `DEBUG=False` in `.env`
2. ✅ Use strong `SECRET_KEY` and `ENCRYPTION_KEY`
3. ✅ Configure production database
4. ✅ Set up HTTPS/SSL
5. ✅ Update `AZURE_REDIRECT_URI` to production URL
6. ✅ Configure CORS for production frontend
7. ✅ Set up logging and monitoring
8. ✅ Use environment-specific configurations
9. ✅ Enable database connection pooling
10. ✅ Set up backup strategy

### Docker Deployment

```dockerfile
# Dockerfile
FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

```bash
# Build and run
docker build -t teams-scheduler-api .
docker run -p 8000:8000 --env-file .env teams-scheduler-api
```

### Using Gunicorn (Production)

```bash
# Install gunicorn
pip install gunicorn

# Run with gunicorn
gunicorn app.main:app -w 4 -k uvicorn.workers.UvicornWorker --bind 0.0.0.0:8000
```

## Environment Variables Reference

| Variable | Description | Required | Default |
|----------|-------------|----------|---------|
| `APP_NAME` | Application name | No | Teams Meeting Scheduler |
| `DEBUG` | Debug mode | No | False |
| `DATABASE_URL` | PostgreSQL connection string | Yes | - |
| `AZURE_CLIENT_ID` | Azure AD client ID | Yes | - |
| `AZURE_CLIENT_SECRET` | Azure AD client secret | Yes | - |
| `AZURE_TENANT_ID` | Azure AD tenant ID | Yes | - |
| `AZURE_REDIRECT_URI` | OAuth redirect URI | Yes | - |
| `SECRET_KEY` | JWT secret key | Yes | - |
| `ENCRYPTION_KEY` | Token encryption key | Yes | - |
| `CORS_ORIGINS` | Allowed CORS origins | No | http://localhost:3000 |
| `LOG_LEVEL` | Logging level | No | INFO |

## Troubleshooting

### Database Connection Issues

```bash
# Check PostgreSQL is running
pg_isready

# Test connection
psql -U username -d teams_scheduler
```

### Azure AD Authentication Issues

1. Verify redirect URI matches exactly in Azure Portal
2. Check API permissions are granted
3. Ensure client secret hasn't expired
4. Verify tenant ID is correct

### Token Encryption Issues

```bash
# Regenerate encryption key
python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"
```

## Security Best Practices

1. **Never commit `.env` file** - Add to `.gitignore`
2. **Rotate secrets regularly** - Update client secrets and keys
3. **Use HTTPS in production** - Encrypt data in transit
4. **Implement rate limiting** - Prevent abuse
5. **Enable audit logging** - Track all operations
6. **Validate all inputs** - Use Pydantic schemas
7. **Keep dependencies updated** - Regular security patches

## Contributing

1. Create feature branch
2. Make changes
3. Write tests
4. Run linting: `flake8 app/`
5. Run tests: `pytest`
6. Submit pull request

## License

MIT License - See LICENSE file for details

## Support

For issues and questions:
- GitHub Issues: [Create an issue]
- Documentation: [API Docs](http://localhost:8000/docs)
- Email: support@example.com
# Windows Setup Guide for Teams Meeting Scheduler

## Database Setup on Windows

Since you're on Windows, here are the correct steps to create the PostgreSQL database:

### Method 1: Using pgAdmin (Recommended for Windows)

1. **Open pgAdmin** (PostgreSQL GUI tool)
2. **Connect to your PostgreSQL server**
3. **Right-click on "Databases"** → **Create** → **Database**
4. **Enter database name**: `teams_scheduler`
5. **Click Save**

### Method 2: Using psql Command Line

1. **Open Command Prompt or PowerShell**
2. **Navigate to PostgreSQL bin directory** (usually):
   ```powershell
   cd "C:\Program Files\PostgreSQL\14\bin"
   ```
   (Replace `14` with your PostgreSQL version)

3. **Connect to PostgreSQL**:
   ```powershell
   .\psql -U postgres
   ```
   Enter your PostgreSQL password when prompted

4. **Create the database**:
   ```sql
   CREATE DATABASE teams_scheduler;
   ```

5. **Verify database was created**:
   ```sql
   \l
   ```

6. **Exit psql**:
   ```sql
   \q
   ```

### Method 3: Using SQL Script

1. **Open Command Prompt or PowerShell**
2. **Navigate to PostgreSQL bin directory**:
   ```powershell
   cd "C:\Program Files\PostgreSQL\14\bin"
   ```

3. **Run the setup script**:
   ```powershell
   .\psql -U postgres -f "C:\Users\AasthaSaha\Downloads\ItsBob\backend\setup_database.sql"
   ```

### Method 4: Using Python Script

Create and run this Python script:

```python
# create_database.py
import psycopg2
from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT

# Connect to PostgreSQL server
conn = psycopg2.connect(
    host="localhost",
    user="postgres",
    password="your_password_here"  # Replace with your password
)
conn.set_isolation_level(ISOLATION_LEVEL_AUTOCOMMIT)

# Create database
cursor = conn.cursor()
cursor.execute("CREATE DATABASE teams_scheduler")
cursor.close()
conn.close()

print("Database 'teams_scheduler' created successfully!")
```

Run it:
```powershell
python create_database.py
```

## Complete Setup Steps

### 1. Install PostgreSQL (if not installed)
Download from: https://www.postgresql.org/download/windows/

### 2. Create Database (use one of the methods above)

### 3. Update Environment Variables

Create `.env` file in `backend` directory:

```env
# Database
DATABASE_URL=postgresql+asyncpg://postgres:your_password@localhost:5432/teams_scheduler

# Azure AD (get from Azure Portal)
AZURE_CLIENT_ID=your_client_id
AZURE_CLIENT_SECRET=your_client_secret
AZURE_TENANT_ID=your_tenant_id
AZURE_REDIRECT_URI=http://localhost:8000/api/auth/callback

# Security (generate these)
SECRET_KEY=your_secret_key_here
ENCRYPTION_KEY=your_encryption_key_here

# API
GRAPH_API_ENDPOINT=https://graph.microsoft.com/v1.0
AUTHORITY=https://login.microsoftonline.com

# CORS
CORS_ORIGINS=http://localhost:3000,http://localhost:8000

# App Settings
APP_NAME=Teams Meeting Scheduler
APP_VERSION=1.0.0
ENVIRONMENT=development
DEBUG=true
LOG_LEVEL=INFO
HOST=0.0.0.0
PORT=8000
```

**Generate encryption key**:
```powershell
python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"
```

### 4. Install Python Dependencies

```powershell
# Navigate to backend directory
cd C:\Users\AasthaSaha\Downloads\ItsBob\backend

# Create virtual environment
python -m venv venv

# Activate virtual environment
.\venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

### 5. Initialize Database Tables

```powershell
# Make sure virtual environment is activated
.\venv\Scripts\activate

# Run the application (it will create tables automatically)
python -m uvicorn app.main:app --reload
```

Or use Alembic for migrations:

```powershell
# Initialize Alembic (first time only)
alembic init alembic

# Create migration
alembic revision --autogenerate -m "Initial migration"

# Apply migration
alembic upgrade head
```

### 6. Verify Setup

Open browser and go to:
- API Docs: http://localhost:8000/docs
- Health Check: http://localhost:8000/health

## Troubleshooting

### PostgreSQL Not in PATH

If `psql` command is not recognized, add PostgreSQL to your PATH:

1. **Open System Properties** → **Environment Variables**
2. **Edit "Path" variable**
3. **Add**: `C:\Program Files\PostgreSQL\14\bin`
4. **Restart Command Prompt/PowerShell**

### Connection Refused

Check if PostgreSQL service is running:

```powershell
# Check service status
Get-Service -Name postgresql*

# Start service if stopped
Start-Service -Name postgresql-x64-14
```

### Permission Denied

Run Command Prompt or PowerShell as Administrator.

### Database Already Exists

If you get "database already exists" error:

```sql
-- Connect to PostgreSQL
psql -U postgres

-- Drop existing database
DROP DATABASE teams_scheduler;

-- Create new database
CREATE DATABASE teams_scheduler;
```

## Quick Start Commands

```powershell
# 1. Navigate to backend
cd C:\Users\AasthaSaha\Downloads\ItsBob\backend

# 2. Activate virtual environment
.\venv\Scripts\activate

# 3. Run the application
uvicorn app.main:app --reload

# 4. Open in browser
start http://localhost:8000/docs
```

## AI Scheduling System

The AI scheduling system is now fully integrated! Check out:
- **Guide**: `C:\Users\AasthaSaha\Downloads\ItsBob\AI_SCHEDULING_GUIDE.md`
- **Examples**: `C:\Users\AasthaSaha\Downloads\ItsBob\backend\examples\ai_scheduling_examples.py`
- **API Docs**: http://localhost:8000/docs (when running)

## Need Help?

If you encounter any issues:
1. Check PostgreSQL is installed and running
2. Verify database credentials in `.env`
3. Ensure all dependencies are installed
4. Check the logs for error messages

---

**Made with Bob** - Windows Setup Guide
# Running the App Locally

## Prerequisites

1. **Python 3.11+** (check with `python --version`)
2. **PostgreSQL database** (local or remote Lakebase instance)
3. **Database credentials** configured in `app.yaml`

## Quick Start

### 1. Activate Virtual Environment

```bash
# On macOS/Linux
source venv/bin/activate

# On Windows
venv\Scripts\activate
```

### 2. Install Dependencies

```bash
pip install -r requirements.txt
```

### 3. Configure Database

Make sure `app.yaml` has your database credentials:

```yaml
database:
  host: "your-database-host"
  port: 5432
  database: "your-database-name"
  user: "your-username"
  password: "your-password"
```

### 4. Set Environment Variables (Matching Databricks Apps)

Set the same environment variables that Databricks Apps will set (from `app.yaml`):

```bash
export PYTHONPATH=./workspace
export PYTHONUNBUFFERED=1
export WORKSPACE_DIR=$(pwd)
export PORT=8000
export HOST=0.0.0.0
```

### 5. Run the App (Exactly Like Databricks Apps)

Databricks Apps runs: `python app.py` (as specified in `app.yaml`)

```bash
python app.py
```

The app will:
- Connect to the database (using config from `app.yaml`)
- Run migrations automatically (create tables if needed)
- Start the FastAPI server on port 8000

### 6. Access the App

- **File Operations**: http://localhost:8000/
- **TODO App**: http://localhost:8000/todos
- **API Docs**: http://localhost:8000/docs
- **Health Check**: http://localhost:8000/api/healthcheck

## Running Like Databricks Apps

This setup exactly matches how Databricks Apps will run your app:
- ✅ Same command: `python app.py`
- ✅ Same environment variables (from `app.yaml`)
- ✅ Same working directory structure
- ✅ Database config read from `app.yaml`

If it works locally this way, it will work in Databricks Apps!

## Troubleshooting

### Database Connection Errors

If you see connection errors:
1. Verify database credentials in `app.yaml`
2. Check database is running and accessible
3. Verify network connectivity (firewall, VPN, etc.)

### Migration Errors

If migrations fail:
- Check database user has CREATE/ALTER permissions
- Verify Alembic version table exists: `SELECT * FROM alembic_version;`
- Check logs for specific error messages

### Port Already in Use

If port 8000 is busy:
```bash
export PORT=8001
python app.py
```

Then access at http://localhost:8001

## Development Workflow

1. **Make code changes**
2. **Restart the app** (Ctrl+C, then `python app.py`)
3. **Migrations run automatically** on startup
4. **Test changes** in browser

## Creating New Migrations

When you modify `db_schema.py`:

```bash
# Generate migration
alembic revision --autogenerate -m "description of changes"

# Review the generated file in alembic/versions/

# Test migration
alembic upgrade head

# Run app to verify
python app.py
```


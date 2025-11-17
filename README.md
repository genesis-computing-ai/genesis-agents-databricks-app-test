# Databricks File Access Test Application

A minimal FastAPI application for testing file read/write operations in Databricks Apps.

## Purpose

This application is designed to diagnose file access issues in Databricks Apps by providing:
- Simple file read operations
- Simple file write operations
- File listing
- File deletion
- Environment information display

## Local Testing

### Using Docker

```bash
# Build the image
docker build -t file-test-app:latest .

# Run the container
docker run -p 8000:8000 file-test-app:latest

# Access the app at http://localhost:8000
```

### Using Python directly

```bash
# Install dependencies
pip install -r requirements.txt

# Set environment variables
export WORKSPACE_DIR=$(pwd)
export PORT=8000
export HOST=0.0.0.0

# Run the app
python app.py
```

## Databricks Apps Deployment

1. **Build and push Docker image** to Databricks container registry
2. **Update `app.yaml`** with your workspace/catalog/schema information
3. **Deploy using Databricks Apps CLI** or UI
4. **Access the application** via the provided endpoint URL

## API Endpoints

- `GET /` - HTML interface for testing
- `GET /api/healthcheck` - Health check endpoint
- `GET /api/env` - Environment information
- `GET /api/read/{filename}` - Read a file
- `POST /api/write/{filename}` - Write a file (JSON body: `{"content": "..."}`)
- `GET /api/list` - List all files
- `DELETE /api/delete/{filename}` - Delete a file

## Testing File Access

1. Open the web interface at `/`
2. Use the "Write File" section to create a test file
3. Use the "Read File" section to verify the file was written
4. Check the "Environment Information" section to verify paths and permissions
5. Use "List Files" to see all files in the workspace

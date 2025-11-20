# Agent Instructions: TODO API

This guide provides instructions for AI agents to start the server and interact with the TODO API.

## Prerequisites

- Virtual environment `myenv311` already exists
- PostgreSQL/Lakebase database credentials configured in `app.yaml`

## Start the Server

```bash
# Activate virtual environment
source myenv311/bin/activate

# Run the launcher script (reads config from app.yaml)
./run.sh
```

The script will:
- Read environment variables from `app.yaml`
- Initialize the database (create tables if needed)
- Start the FastAPI server on port 8000

### Verify Server is Running

You should see:
```
INFO:     Started server process [PID]
INFO:     Waiting for application startup.
INFO:db_init:Initializing database...
INFO:     Application startup complete.
INFO:     Uvicorn running on http://0.0.0.0:8000 (Press CTRL+C to quit)
```

## Access the Application

- **Web UI (TODO App)**: http://localhost:8000/todos
- **Interactive API Docs**: http://localhost:8000/docs
- **OpenAPI Schema**: http://localhost:8000/openapi.json

## TODO API Endpoints

### Base URL
```
http://localhost:8000
```

### 1. List All TODOs
```http
GET /api/todo?completed=false&priority=1
```

**Query Parameters:**
- `completed` (optional): Filter by completion status (`true`/`false`)
- `priority` (optional): Filter by priority (0-4)

**Example:**
```bash
# Get all incomplete high-priority TODOs
curl "http://localhost:8000/api/todo?completed=false&priority=1"
```

**Response:**
```json
[
  {
    "id": 1,
    "title": "Complete project",
    "description": "Finish the TODO app",
    "completed": false,
    "priority": 1,
    "due_date": "2024-12-31T23:59:59",
    "created_at": "2024-01-01T00:00:00",
    "updated_at": "2024-01-01T00:00:00"
  }
]
```

### 2. Get Single TODO
```http
GET /api/todo/{todo_id}
```

**Example:**
```bash
curl http://localhost:8000/api/todo/1
```

**Response:**
```json
{
  "id": 1,
  "title": "Complete project",
  "description": "Finish the TODO app",
  "completed": false,
  "priority": 1,
  "due_date": "2024-12-31T23:59:59",
  "created_at": "2024-01-01T00:00:00",
  "updated_at": "2024-01-01T00:00:00"
}
```

### 3. Create TODO
```http
POST /api/todo
Content-Type: application/json

{
  "title": "New TODO item",
  "description": "Optional description",
  "priority": 2,
  "due_date": "2024-12-31T23:59:59"
}
```

**Example:**
```bash
curl -X POST http://localhost:8000/api/todo \
  -H "Content-Type: application/json" \
  -d '{
    "title": "Review code",
    "description": "Review the TODO API implementation",
    "priority": 1,
    "due_date": "2024-12-25T10:00:00"
  }'
```

**Request Body Fields:**
- `title` (required): TODO title (1-255 characters)
- `description` (optional): TODO description
- `priority` (optional): Priority level (0-4, default: 2)
  - 0 = Critical
  - 1 = High
  - 2 = Medium (default)
  - 3 = Low
  - 4 = Backlog
- `due_date` (optional): Due date in ISO 8601 format

**Response:**
```json
{
  "id": 2,
  "title": "Review code",
  "description": "Review the TODO API implementation",
  "completed": false,
  "priority": 1,
  "due_date": "2024-12-25T10:00:00",
  "created_at": "2024-01-01T12:00:00",
  "updated_at": "2024-01-01T12:00:00"
}
```

### 4. Update TODO
```http
PUT /api/todo/{todo_id}
Content-Type: application/json

{
  "title": "Updated title",
  "completed": true,
  "priority": 0
}
```

**Example:**
```bash
curl -X PUT http://localhost:8000/api/todo/1 \
  -H "Content-Type: application/json" \
  -d '{
    "title": "Updated TODO",
    "completed": true,
    "priority": 0
  }'
```

**Request Body Fields (all optional):**
- `title`: Updated title
- `description`: Updated description
- `completed`: Completion status (`true`/`false`)
- `priority`: Updated priority (0-4)
- `due_date`: Updated due date

**Response:**
```json
{
  "id": 1,
  "title": "Updated TODO",
  "description": "Original description",
  "completed": true,
  "priority": 0,
  "due_date": null,
  "created_at": "2024-01-01T00:00:00",
  "updated_at": "2024-01-01T12:30:00"
}
```

### 5. Delete TODO
```http
DELETE /api/todo/{todo_id}
```

**Example:**
```bash
curl -X DELETE http://localhost:8000/api/todo/1
```

**Response:**
- Status: `204 No Content` (success)
- Status: `404 Not Found` (TODO doesn't exist)

## Error Responses

All endpoints return standard HTTP status codes:

- `200 OK`: Successful GET/PUT request
- `201 Created`: Successful POST request
- `204 No Content`: Successful DELETE request
- `400 Bad Request`: Invalid request data
- `404 Not Found`: Resource not found
- `500 Internal Server Error`: Server error

**Error Response Format:**
```json
{
  "detail": "Error message describing what went wrong"
}
```

**Example:**
```json
{
  "detail": "TODO with ID 999 not found"
}
```

## Complete Workflow Example

### 1. Start Server
```bash
source myenv311/bin/activate
./run.sh
```

The server will start on http://localhost:8000

### 2. Create a TODO
```bash
curl -X POST http://localhost:8000/api/todo \
  -H "Content-Type: application/json" \
  -d '{
    "title": "Test TODO",
    "description": "This is a test",
    "priority": 1
  }'
```

### 3. List All TODOs
```bash
curl http://localhost:8000/api/todo
```

### 4. Update TODO (mark as completed)
```bash
curl -X PUT http://localhost:8000/api/todo/1 \
  -H "Content-Type: application/json" \
  -d '{"completed": true}'
```

### 5. Get Specific TODO
```bash
curl http://localhost:8000/api/todo/1
```

### 6. Delete TODO
```bash
curl -X DELETE http://localhost:8000/api/todo/1
```

## Python Client Example

```python
import requests

BASE_URL = "http://localhost:8000"

# Create a TODO
response = requests.post(
    f"{BASE_URL}/api/todo",
    json={
        "title": "Python TODO",
        "description": "Created via Python",
        "priority": 1
    }
)
todo = response.json()
print(f"Created TODO: {todo['id']}")

# List all TODOs
response = requests.get(f"{BASE_URL}/api/todo")
todos = response.json()
print(f"Found {len(todos)} TODOs")

# Update TODO
response = requests.put(
    f"{BASE_URL}/api/todo/{todo['id']}",
    json={"completed": True}
)
updated = response.json()
print(f"Updated TODO: {updated['title']}")

# Delete TODO
response = requests.delete(f"{BASE_URL}/api/todo/{todo['id']}")
print(f"Deleted TODO: {response.status_code == 204}")
```

## Troubleshooting

### Port Already in Use
```bash
# Find and kill process on port 8000
lsof -ti:8000 | xargs kill -9
```

### Database Connection Error
- Verify database credentials in `app.yaml`
- Check database is accessible from your network
- Ensure database user has CREATE/ALTER permissions

### Virtual Environment Not Activated
```bash
# Activate virtual environment
source myenv311/bin/activate
```

## Stopping the Server

Press `Ctrl+C` in the terminal where the server is running.

## Additional Resources

- **Interactive API Documentation**: http://localhost:8000/docs
- **OpenAPI Schema**: http://localhost:8000/openapi.json
- **Web UI**: http://localhost:8000/todos

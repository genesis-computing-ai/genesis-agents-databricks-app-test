"""
Standalone FastAPI application for testing file access in Databricks Apps.

This app provides:
- File read operations (GET endpoint)
- File write operations (POST endpoint)
- Simple HTML UI for testing
- Health check endpoint
"""

import os
import json
from pathlib import Path
from typing import Optional
from fastapi import FastAPI, HTTPException, Form, File, UploadFile
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles

app = FastAPI(title="Databricks File Access Test", version="1.0.0")

# Base directory for file operations
# In Databricks Apps, this will be the workspace directory
BASE_DIR = Path(os.getenv("WORKSPACE_DIR", "/workspace"))
FILES_DIR = BASE_DIR / "files"

# Ensure files directory exists
FILES_DIR.mkdir(parents=True, exist_ok=True)


@app.get("/", response_class=HTMLResponse)
async def root():
    """Main HTML interface for testing file operations."""
    html_content = """
    <!DOCTYPE html>
    <html>
    <head>
        <title>Databricks File Access Test</title>
        <style>
            body {
                font-family: Arial, sans-serif;
                max-width: 800px;
                margin: 50px auto;
                padding: 20px;
                background-color: #f5f5f5;
            }
            .container {
                background: white;
                padding: 30px;
                border-radius: 8px;
                box-shadow: 0 2px 4px rgba(0,0,0,0.1);
            }
            h1 {
                color: #333;
                border-bottom: 2px solid #0066cc;
                padding-bottom: 10px;
            }
            .section {
                margin: 30px 0;
                padding: 20px;
                background-color: #f9f9f9;
                border-radius: 5px;
            }
            label {
                display: block;
                margin-bottom: 5px;
                font-weight: bold;
                color: #555;
            }
            input[type="text"], textarea {
                width: 100%;
                padding: 8px;
                margin-bottom: 10px;
                border: 1px solid #ddd;
                border-radius: 4px;
                box-sizing: border-box;
            }
            button {
                background-color: #0066cc;
                color: white;
                padding: 10px 20px;
                border: none;
                border-radius: 4px;
                cursor: pointer;
                font-size: 14px;
            }
            button:hover {
                background-color: #0052a3;
            }
            .result {
                margin-top: 15px;
                padding: 10px;
                border-radius: 4px;
                white-space: pre-wrap;
                font-family: monospace;
                font-size: 12px;
            }
            .success {
                background-color: #d4edda;
                border: 1px solid #c3e6cb;
                color: #155724;
            }
            .error {
                background-color: #f8d7da;
                border: 1px solid #f5c6cb;
                color: #721c24;
            }
            .info {
                background-color: #d1ecf1;
                border: 1px solid #bee5eb;
                color: #0c5460;
            }
        </style>
    </head>
    <body>
        <div class="container">
            <h1>Databricks File Access Test Application</h1>
            
            <div class="section">
                <h2>Environment Information</h2>
                <div id="env-info" class="result info">Loading...</div>
            </div>
            
            <div class="section">
                <h2>Read File</h2>
                <label for="read-filename">Filename (relative to /workspace/files):</label>
                <input type="text" id="read-filename" placeholder="test.txt" value="test.txt">
                <button onclick="readFile()">Read File</button>
                <div id="read-result" class="result" style="display:none;"></div>
            </div>
            
            <div class="section">
                <h2>Write File</h2>
                <label for="write-filename">Filename (relative to /workspace/files):</label>
                <input type="text" id="write-filename" placeholder="test.txt" value="test.txt">
                <label for="write-content">Content:</label>
                <textarea id="write-content" rows="5" placeholder="Enter file content here...">Hello from Databricks Apps!
This is a test file write operation.
Timestamp: </textarea>
                <button onclick="writeFile()">Write File</button>
                <div id="write-result" class="result" style="display:none;"></div>
            </div>
            
            <div class="section">
                <h2>List Files</h2>
                <button onclick="listFiles()">List All Files</button>
                <div id="list-result" class="result" style="display:none;"></div>
            </div>
            
            <div class="section">
                <h2>Delete File</h2>
                <label for="delete-filename">Filename (relative to /workspace/files):</label>
                <input type="text" id="delete-filename" placeholder="test.txt" value="test.txt">
                <button onclick="deleteFile()">Delete File</button>
                <div id="delete-result" class="result" style="display:none;"></div>
            </div>
        </div>
        
        <script>
            // Load environment info on page load
            window.onload = function() {
                fetch('/api/env')
                    .then(r => r.json())
                    .then(data => {
                        document.getElementById('env-info').textContent = JSON.stringify(data, null, 2);
                    })
                    .catch(err => {
                        document.getElementById('env-info').textContent = 'Error: ' + err.message;
                        document.getElementById('env-info').className = 'result error';
                    });
            };
            
            function showResult(elementId, data, isError) {
                const element = document.getElementById(elementId);
                element.style.display = 'block';
                element.textContent = typeof data === 'string' ? data : JSON.stringify(data, null, 2);
                element.className = 'result ' + (isError ? 'error' : 'success');
            }
            
            async function readFile() {
                const filename = document.getElementById('read-filename').value;
                try {
                    const response = await fetch(`/api/read/${encodeURIComponent(filename)}`);
                    const data = await response.json();
                    showResult('read-result', data, !response.ok);
                } catch (err) {
                    showResult('read-result', 'Error: ' + err.message, true);
                }
            }
            
            async function writeFile() {
                const filename = document.getElementById('write-filename').value;
                const content = document.getElementById('write-content').value;
                try {
                    const response = await fetch(`/api/write/${encodeURIComponent(filename)}`, {
                        method: 'POST',
                        headers: {'Content-Type': 'application/json'},
                        body: JSON.stringify({content: content})
                    });
                    const data = await response.json();
                    showResult('write-result', data, !response.ok);
                } catch (err) {
                    showResult('write-result', 'Error: ' + err.message, true);
                }
            }
            
            async function listFiles() {
                try {
                    const response = await fetch('/api/list');
                    const data = await response.json();
                    showResult('list-result', data, !response.ok);
                } catch (err) {
                    showResult('list-result', 'Error: ' + err.message, true);
                }
            }
            
            async function deleteFile() {
                const filename = document.getElementById('delete-filename').value;
                try {
                    const response = await fetch(`/api/delete/${encodeURIComponent(filename)}`, {
                        method: 'DELETE'
                    });
                    const data = await response.json();
                    showResult('delete-result', data, !response.ok);
                } catch (err) {
                    showResult('delete-result', 'Error: ' + err.message, true);
                }
            }
        </script>
    </body>
    </html>
    """
    return html_content


@app.get("/api/healthcheck")
async def healthcheck():
    """Health check endpoint for Databricks Apps readiness probe."""
    return {
        "status": "healthy",
        "base_dir": str(BASE_DIR),
        "files_dir": str(FILES_DIR),
        "base_dir_exists": BASE_DIR.exists(),
        "files_dir_exists": FILES_DIR.exists(),
        "base_dir_writable": os.access(BASE_DIR, os.W_OK) if BASE_DIR.exists() else False,
        "files_dir_writable": os.access(FILES_DIR, os.W_OK) if FILES_DIR.exists() else False,
    }


@app.get("/api/env")
async def get_env():
    """Get environment information for debugging."""
    return {
        "workspace_dir": os.getenv("WORKSPACE_DIR", "NOT SET"),
        "base_dir": str(BASE_DIR),
        "files_dir": str(FILES_DIR),
        "pythonpath": os.getenv("PYTHONPATH", "NOT SET"),
        "port": os.getenv("PORT", "NOT SET"),
        "cwd": os.getcwd(),
        "user": os.getenv("USER", "NOT SET"),
        "base_dir_exists": BASE_DIR.exists(),
        "files_dir_exists": FILES_DIR.exists(),
    }


@app.get("/api/read/{filename:path}")
async def read_file(filename: str):
    """
    Read a file from the files directory.
    
    Args:
        filename: Relative path to file within /workspace/files
    """
    try:
        # Sanitize filename to prevent directory traversal
        file_path = FILES_DIR / filename
        file_path = file_path.resolve()
        
        # Ensure the resolved path is still within FILES_DIR
        if not str(file_path).startswith(str(FILES_DIR.resolve())):
            raise HTTPException(status_code=400, detail="Invalid file path")
        
        if not file_path.exists():
            raise HTTPException(status_code=404, detail=f"File not found: {filename}")
        
        if not file_path.is_file():
            raise HTTPException(status_code=400, detail=f"Path is not a file: {filename}")
        
        content = file_path.read_text(encoding='utf-8')
        stat = file_path.stat()
        
        return {
            "success": True,
            "filename": filename,
            "path": str(file_path),
            "content": content,
            "size": stat.st_size,
            "modified": stat.st_mtime,
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error reading file: {str(e)}")


@app.post("/api/write/{filename:path}")
async def write_file(filename: str, content: dict):
    """
    Write content to a file in the files directory.
    
    Args:
        filename: Relative path to file within /workspace/files
        content: JSON object with 'content' key containing file content
    """
    try:
        # Sanitize filename to prevent directory traversal
        file_path = FILES_DIR / filename
        file_path = file_path.resolve()
        
        # Ensure the resolved path is still within FILES_DIR
        if not str(file_path).startswith(str(FILES_DIR.resolve())):
            raise HTTPException(status_code=400, detail="Invalid file path")
        
        # Ensure parent directory exists
        file_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Write content
        file_content = content.get("content", "")
        file_path.write_text(file_content, encoding='utf-8')
        
        stat = file_path.stat()
        
        return {
            "success": True,
            "filename": filename,
            "path": str(file_path),
            "size": stat.st_size,
            "message": f"File written successfully: {filename}",
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error writing file: {str(e)}")


@app.get("/api/list")
async def list_files():
    """List all files in the files directory."""
    try:
        files = []
        if FILES_DIR.exists():
            for item in FILES_DIR.rglob("*"):
                if item.is_file():
                    stat = item.stat()
                    rel_path = item.relative_to(FILES_DIR)
                    files.append({
                        "name": str(rel_path),
                        "path": str(item),
                        "size": stat.st_size,
                        "modified": stat.st_mtime,
                    })
        
        return {
            "success": True,
            "files_dir": str(FILES_DIR),
            "count": len(files),
            "files": files,
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error listing files: {str(e)}")


@app.delete("/api/delete/{filename:path}")
async def delete_file(filename: str):
    """
    Delete a file from the files directory.
    
    Args:
        filename: Relative path to file within /workspace/files
    """
    try:
        # Sanitize filename to prevent directory traversal
        file_path = FILES_DIR / filename
        file_path = file_path.resolve()
        
        # Ensure the resolved path is still within FILES_DIR
        if not str(file_path).startswith(str(FILES_DIR.resolve())):
            raise HTTPException(status_code=400, detail="Invalid file path")
        
        if not file_path.exists():
            raise HTTPException(status_code=404, detail=f"File not found: {filename}")
        
        if not file_path.is_file():
            raise HTTPException(status_code=400, detail=f"Path is not a file: {filename}")
        
        file_path.unlink()
        
        return {
            "success": True,
            "filename": filename,
            "message": f"File deleted successfully: {filename}",
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error deleting file: {str(e)}")


if __name__ == "__main__":
    import uvicorn
    
    # Get port from environment (Databricks Apps provides this)
    port = int(os.getenv("PORT", "8000"))
    host = os.getenv("HOST", "0.0.0.0")
    
    uvicorn.run(
        app,
        host=host,
        port=port,
        log_level="info",
    )


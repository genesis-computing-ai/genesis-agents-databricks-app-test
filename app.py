"""
Standalone FastAPI application for testing file access in Databricks Apps.

This app provides:
- File read operations (GET endpoint)
- File write operations (POST endpoint)
- Simple HTML UI for testing
- Health check endpoint
- Filesystem discovery endpoint for finding writable directories
"""

import os
import json
import stat
import tempfile
from pathlib import Path
from typing import Optional, Dict, List, Any
from fastapi import FastAPI, HTTPException, Form, File, UploadFile
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles

app = FastAPI(title="Databricks File Access Test", version="1.0.0")

# Base directory for file operations (lazy initialization - not accessed at startup)
# In Databricks Apps, this will be the workspace directory
def get_base_dir() -> Path:
    """Get base directory from environment variable."""
    return Path(os.getenv("WORKSPACE_DIR", "/workspace"))

def get_files_dir() -> Path:
    """Get files directory (lazy - doesn't create on startup)."""
    return get_base_dir() / "files"


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
                <h2>Filesystem Discovery</h2>
                <p>Discover all directories with write access on the runtime system.</p>
                <button onclick="discoverFilesystem()">Discover Writable Directories</button>
                <div id="discover-result" class="result" style="display:none;"></div>
            </div>
            
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
                <label for="write-filename">Filename (written directly to WORKSPACE_DIR):</label>
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
            
            async function discoverFilesystem() {
                try {
                    const response = await fetch('/api/discover');
                    const data = await response.json();
                    showResult('discover-result', data, !response.ok);
                } catch (err) {
                    showResult('discover-result', 'Error: ' + err.message, true);
                }
            }
            
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
    base_dir = get_base_dir()
    files_dir = get_files_dir()
    return {
        "status": "healthy",
        "base_dir": str(base_dir),
        "files_dir": str(files_dir),
        "base_dir_exists": base_dir.exists(),
        "files_dir_exists": files_dir.exists(),
        "base_dir_writable": os.access(base_dir, os.W_OK) if base_dir.exists() else False,
        "files_dir_writable": os.access(files_dir, os.W_OK) if files_dir.exists() else False,
    }


@app.get("/api/env")
async def get_env():
    """Get environment information for debugging."""
    base_dir = get_base_dir()
    files_dir = get_files_dir()
    return {
        "workspace_dir": os.getenv("WORKSPACE_DIR", "NOT SET"),
        "base_dir": str(base_dir),
        "files_dir": str(files_dir),
        "pythonpath": os.getenv("PYTHONPATH", "NOT SET"),
        "port": os.getenv("PORT", "NOT SET"),
        "cwd": os.getcwd(),
        "user": os.getenv("USER", "NOT SET"),
        "base_dir_exists": base_dir.exists(),
        "files_dir_exists": files_dir.exists(),
    }


@app.get("/api/discover")
async def discover_filesystem():
    """
    Discover all directories with write access by scanning the entire runtime system.
    
    This endpoint:
    - Scans common mount points (/Volumes/, /dbfs/, /Workspace/, /tmp/, etc.)
    - Tests read/write access on each directory
    - Checks /proc/mounts for mounted filesystems
    - Lists directory contents where accessible
    - Returns comprehensive information about accessible paths
    """
    results = {
        "scan_summary": {
            "total_paths_tested": 0,
            "readable_paths": 0,
            "writable_paths": 0,
            "mount_points_found": 0,
        },
        "environment": {
            "cwd": os.getcwd(),
            "user": os.getenv("USER", "unknown"),
            "workspace_dir": os.getenv("WORKSPACE_DIR", "NOT SET"),
            "pythonpath": os.getenv("PYTHONPATH", "NOT SET"),
        },
        "mounts": [],
        "paths_tested": [],
        "writable_paths": [],
        "errors": [],
    }
    
    # Common paths to test
    common_paths = [
        "/",
        "/Volumes",
        "/Volumes/genesis-data-agents-storage",
        "/Volumes/genesis-data-agents-storage/default",
        "/Volumes/genesis-data-agents-storage/default/genesis-app-data",
        "/dbfs",
        "/dbfs/mnt",
        "/Workspace",
        "/tmp",
        "/workspace",
        "/app",
        "/home",
        "/opt",
        "/usr",
        "/var",
        os.getcwd(),
        os.getenv("WORKSPACE_DIR", ""),
        os.getenv("HOME", ""),
        tempfile.gettempdir(),
    ]
    
    # Remove empty paths
    common_paths = [p for p in common_paths if p]
    
    # Read /proc/mounts if accessible
    try:
        with open("/proc/mounts", "r") as f:
            mounts = f.readlines()
            results["scan_summary"]["mount_points_found"] = len(mounts)
            for line in mounts:
                parts = line.split()
                if len(parts) >= 2:
                    mount_point = parts[1]
                    filesystem = parts[0]
                    if mount_point not in common_paths:
                        common_paths.append(mount_point)
                    results["mounts"].append({
                        "device": filesystem,
                        "mount_point": mount_point,
                        "filesystem": parts[2] if len(parts) > 2 else "unknown",
                    })
    except (PermissionError, FileNotFoundError, OSError) as e:
        results["errors"].append(f"Could not read /proc/mounts: {str(e)}")
    
    # Test each path
    tested_paths = set()
    
    def test_path(path_str: str, depth: int = 0, max_depth: int = 3) -> Dict[str, Any]:
        """Test a path for read/write access and return information."""
        if depth > max_depth or path_str in tested_paths:
            return None
        
        tested_paths.add(path_str)
        results["scan_summary"]["total_paths_tested"] += 1
        
        path_info = {
            "path": path_str,
            "exists": False,
            "is_directory": False,
            "is_file": False,
            "readable": False,
            "writable": False,
            "executable": False,
            "error": None,
            "children": [],
            "stat_info": None,
        }
        
        try:
            path = Path(path_str)
            path_info["exists"] = path.exists()
            
            if not path_info["exists"]:
                return path_info
            
            path_info["is_directory"] = path.is_dir()
            path_info["is_file"] = path.is_file()
            
            # Test permissions
            path_info["readable"] = os.access(path_str, os.R_OK)
            path_info["writable"] = os.access(path_str, os.W_OK)
            path_info["executable"] = os.access(path_str, os.X_OK)
            
            # Get stat info
            try:
                stat_info = path.stat()
                path_info["stat_info"] = {
                    "size": stat_info.st_size if path.is_file() else None,
                    "mode": oct(stat_info.st_mode),
                    "uid": stat_info.st_uid,
                    "gid": stat_info.st_gid,
                }
            except Exception as e:
                path_info["error"] = f"Could not stat: {str(e)}"
            
            # Test write access by attempting to create a test file
            if path_info["writable"] and path_info["is_directory"]:
                test_file = path / ".databricks_app_test_write"
                try:
                    test_file.write_text("test")
                    test_file.unlink()
                    path_info["writable"] = True
                except Exception as e:
                    path_info["writable"] = False
                    path_info["error"] = f"Write test failed: {str(e)}"
            
            # List children if directory and readable
            if path_info["is_directory"] and path_info["readable"] and depth < max_depth:
                try:
                    children = []
                    for child in path.iterdir():
                        child_str = str(child)
                        # Limit children listing to avoid huge responses
                        if len(children) < 50:
                            children.append({
                                "name": child.name,
                                "path": child_str,
                                "is_dir": child.is_dir(),
                                "is_file": child.is_file(),
                            })
                        else:
                            children.append({
                                "name": "... (truncated, more than 50 items)",
                                "path": None,
                            })
                            break
                    path_info["children"] = children
                except PermissionError:
                    path_info["error"] = "Permission denied listing children"
                except Exception as e:
                    path_info["error"] = f"Error listing children: {str(e)}"
            
            # Track readable/writable paths
            if path_info["readable"]:
                results["scan_summary"]["readable_paths"] += 1
            if path_info["writable"]:
                results["scan_summary"]["writable_paths"] += 1
                results["writable_paths"].append({
                    "path": path_str,
                    "is_directory": path_info["is_directory"],
                    "is_file": path_info["is_file"],
                })
            
        except Exception as e:
            path_info["error"] = str(e)
            results["errors"].append(f"Error testing {path_str}: {str(e)}")
        
        return path_info
    
    # Test all common paths
    for path_str in common_paths:
        path_info = test_path(path_str)
        if path_info:
            results["paths_tested"].append(path_info)
            
            # If it's a directory, also test some subdirectories
            if path_info["is_directory"] and path_info["readable"]:
                try:
                    path = Path(path_str)
                    for child in path.iterdir():
                        if child.is_dir() and len(results["paths_tested"]) < 200:  # Limit total paths
                            child_info = test_path(str(child), depth=1)
                            if child_info:
                                results["paths_tested"].append(child_info)
                except Exception:
                    pass
    
    # Sort writable paths by path length (shorter = likely more important)
    results["writable_paths"].sort(key=lambda x: len(x["path"]))
    
    return results


@app.get("/api/read/{filename:path}")
async def read_file(filename: str):
    """
    Read a file from the files directory.
    
    Args:
        filename: Relative path to file within /workspace/files
    """
    try:
        files_dir = get_files_dir()
        # Sanitize filename to prevent directory traversal
        file_path = files_dir / filename
        file_path = file_path.resolve()
        
        # Ensure the resolved path is still within FILES_DIR
        if not str(file_path).startswith(str(files_dir.resolve())):
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
    Write content to a file directly in WORKSPACE_DIR.
    
    Args:
        filename: Filename to write (will be written directly to WORKSPACE_DIR)
        content: JSON object with 'content' key containing file content
    """
    try:
        base_dir = get_base_dir()
        
        # Sanitize filename - use only the basename to prevent directory traversal
        # Remove any path separators and use only the filename
        safe_filename = os.path.basename(filename)
        if not safe_filename or safe_filename in ('.', '..'):
            raise HTTPException(status_code=400, detail="Invalid filename")
        
        # Write directly to WORKSPACE_DIR
        file_path = base_dir / safe_filename
        file_path = file_path.resolve()
        
        # Ensure the resolved path is still within BASE_DIR
        if not str(file_path).startswith(str(base_dir.resolve())):
            raise HTTPException(status_code=400, detail="Invalid file path")
        
        # Write content directly (no subdirectory creation)
        file_content = content.get("content", "")
        file_path.write_text(file_content, encoding='utf-8')
        
        stat = file_path.stat()
        
        return {
            "success": True,
            "filename": safe_filename,
            "path": str(file_path),
            "size": stat.st_size,
            "message": f"File written successfully: {safe_filename}",
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error writing file: {str(e)}")


@app.get("/api/list")
async def list_files():
    """List all files directly in WORKSPACE_DIR."""
    try:
        base_dir = get_base_dir()
        base_dir_str = str(base_dir)
        
        # Debug info
        debug_info = {
            "WORKSPACE_DIR_env": os.getenv("WORKSPACE_DIR"),
            "base_dir_str": base_dir_str,
            "os.path.exists": os.path.exists(base_dir_str),
            "os.access_R_OK": os.access(base_dir_str, os.R_OK),
            "os.access_W_OK": os.access(base_dir_str, os.W_OK),
            "cwd": os.getcwd(),
        }
        
        # Try to list with error details
        try:
            result = os.listdir(base_dir_str)
            debug_info["listdir_success"] = True
            debug_info["listdir_result"] = result
        except Exception as e:
            debug_info["listdir_error"] = str(e)
            debug_info["listdir_error_type"] = type(e).__name__
        
        return {
            "debug": debug_info,
            "workspace_dir": base_dir_str,
        }
        
    except Exception as e:
        return {
            "error": str(e),
            "error_type": type(e).__name__,
            "WORKSPACE_DIR": os.getenv("WORKSPACE_DIR"),
        }


@app.delete("/api/delete/{filename:path}")
async def delete_file(filename: str):
    """
    Delete a file from the files directory.
    
    Args:
        filename: Relative path to file within /workspace/files
    """
    try:
        files_dir = get_files_dir()
        # Sanitize filename to prevent directory traversal
        file_path = files_dir / filename
        file_path = file_path.resolve()
        
        # Ensure the resolved path is still within FILES_DIR
        if not str(file_path).startswith(str(files_dir.resolve())):
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


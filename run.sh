#!/bin/bash
# Launcher script that reads environment variables from app.yaml and runs the app
# Usage: ./run.sh [local|databricks]
#   local      - Connect to local PostgreSQL database
#   databricks - Connect to Databricks PostgreSQL database (default)

set -e

# Parse command line argument for database environment
DB_ENV_ARG=""
if [ "$1" = "local" ]; then
    DB_ENV_ARG="local"
    echo "Using LOCAL PostgreSQL database"
elif [ "$1" = "databricks" ]; then
    DB_ENV_ARG="databricks"
    echo "Using DATABRICKS PostgreSQL database"
elif [ -n "$1" ]; then
    echo "Error: Unknown argument '$1'. Use 'local' or 'databricks'"
    echo "Usage: $0 [local|databricks]"
    exit 1
else
    DB_ENV_ARG="databricks"
    echo "Using DATABRICKS PostgreSQL database (default)"
fi

# Get the directory where this script is located
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
cd "$SCRIPT_DIR"

# Check if app.yaml exists
if [ ! -f "app.yaml" ]; then
    echo "Error: app.yaml not found in $SCRIPT_DIR"
    exit 1
fi

# Export DB_ENV so Python script can use it
export DB_ENV="$DB_ENV_ARG"

# Use Python to parse app.yaml, set environment variables, and run the app
exec python3 << 'PYTHON_SCRIPT'
import yaml
import os
import sys
import subprocess
from pathlib import Path

# Load app.yaml
yaml_path = Path("app.yaml")
if not yaml_path.exists():
    print("Error: app.yaml not found", file=sys.stderr)
    sys.exit(1)

with open(yaml_path, "r") as f:
    config = yaml.safe_load(f) or {}

# Preserve DB_ENV if set from command line argument
db_env = os.environ.get("DB_ENV", "databricks")
os.environ["DB_ENV"] = db_env

# Extract and set environment variables from env section
if "env" in config:
    for env_item in config.get("env", []):
        if "name" in env_item:
            var_name = env_item["name"]
            # Only set variables that have a 'value' (skip 'valueFrom' which are secrets)
            if "value" in env_item:
                os.environ[var_name] = env_item["value"]
            # For WORKSPACE_DIR with valueFrom: volume, use current directory as fallback
            elif "valueFrom" in env_item and var_name == "WORKSPACE_DIR":
                os.environ[var_name] = os.getcwd()

# Log which database environment is being used
print(f"Database environment: {db_env}", file=sys.stderr)

# Get the command to run
if "command" in config and config["command"]:
    cmd = config["command"]
else:
    cmd = ["python", "app.py"]

# Run the command
sys.exit(subprocess.run(cmd).returncode)
PYTHON_SCRIPT

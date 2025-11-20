#!/bin/bash
# Deploy Genesis to Databricks Apps
# This script uploads only the necessary files for deployment

set -e

# Configuration
PROFILE="dbc-cf175ac8-d315"
WORKSPACE_PATH="/Workspace/genesis"
APP_NAME="genesis-data-agents-file-test"
STAGING_DIR="/tmp/genesis-deploy-$$"
MAX_FILE_SIZE=10485760  # 10MB in bytes

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# Cleanup function
cleanup() {
    if [ -d "$STAGING_DIR" ]; then
        echo -e "${YELLOW}Cleaning up staging directory...${NC}"
        rm -rf "$STAGING_DIR"
    fi
}
trap cleanup EXIT

# Function to copy directory while excluding large files, databases, and __pycache__
copy_dir_filtered() {
    local src_dir="$1"
    local dst_base="$2"
    local dir_name=$(basename "$src_dir")
    local dst_dir="$dst_base/$dir_name"
    
    echo "    Copying $dir_name (excluding large files, databases, and __pycache__)..."
    mkdir -p "$dst_dir"
    
    # Use find to copy files, excluding:
    # - Files larger than MAX_FILE_SIZE (10MB)
    # - Database files (.sqlite, .db, .db-shm, .db-wal)
    # - __pycache__ directories
    find "$src_dir" -type f \( \
        -size -${MAX_FILE_SIZE}c \
        -not -name "*.sqlite" \
        -not -name "*.db" \
        -not -name "*.db-shm" \
        -not -name "*.db-wal" \
        -not -path "*__pycache__*" \
    \) | while read -r src_file; do
        rel_path="${src_file#$src_dir/}"
        dst_file="$dst_dir/$rel_path"
        mkdir -p "$(dirname "$dst_file")"
        cp "$src_file" "$dst_file"
    done
    
    # Also ensure directory structure is preserved (for empty dirs), excluding __pycache__
    find "$src_dir" -type d -not -path "*__pycache__*" | while read -r src_subdir; do
        rel_path="${src_subdir#$src_dir/}"
        if [ -n "$rel_path" ]; then
            mkdir -p "$dst_dir/$rel_path"
        fi
    done
}

echo -e "${GREEN}Deploying Genesis to Databricks Apps${NC}"
echo "Profile: $PROFILE"
echo "Workspace Path: $WORKSPACE_PATH"
echo "App Name: $APP_NAME"
echo ""

# Get the script directory (project root)
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
cd "$SCRIPT_DIR"

# Create staging directory
echo -e "${YELLOW}Step 1: Creating staging directory${NC}"
mkdir -p "$STAGING_DIR"

echo -e "${YELLOW}Step 2: Copying files to staging directory (excluding large files)${NC}"

# Copy root-level files
echo "  - Copying root files..."
# Copy all Python files from root (includes app.py and all modules)
for py_file in *.py; do
    if [ -f "$py_file" ]; then
        cp "$py_file" "$STAGING_DIR/" 2>/dev/null || true
    fi
done
# Copy configuration and other non-Python files
cp app.yaml "$STAGING_DIR/" 2>/dev/null || true
cp requirements.txt "$STAGING_DIR/" 2>/dev/null || true
cp Dockerfile "$STAGING_DIR/" 2>/dev/null || true
cp alembic.ini "$STAGING_DIR/" 2>/dev/null || true

# Copy all directories with filtering (includes all .py files from subdirectories automatically)
echo "  - Copying all directories (filtering large files, databases, and __pycache__)..."
# Find all top-level directories, excluding virtual environments, git, and hidden directories
for dir in */; do
    if [ -d "$dir" ]; then
        dir_name=$(basename "$dir")
        # Skip virtual environments, git, hidden directories, and __pycache__
        skip=false
        case "$dir_name" in
            __pycache__|venv|.git)
                skip=true
                ;;
            .*)
                # Skip hidden directories
                skip=true
                ;;
            myenv*)
                # Skip virtual environment directories starting with myenv
                skip=true
                ;;
        esac
        if [ "$skip" = false ]; then
            copy_dir_filtered "$dir" "$STAGING_DIR"
        fi
    fi
done

# Verify no large files, databases, or __pycache__ directories were copied
echo "  - Verifying no large files, databases, or __pycache__ directories were copied..."
LARGE_FILES=$(find "$STAGING_DIR" -type f \( -size +${MAX_FILE_SIZE}c -o -name "*.sqlite" -o -name "*.db" -o -name "*.db-shm" -o -name "*.db-wal" \) 2>/dev/null | wc -l)
PYCACHE_DIRS=$(find "$STAGING_DIR" -type d -name "__pycache__" 2>/dev/null | wc -l)
if [ "$LARGE_FILES" -gt 0 ]; then
    echo -e "${YELLOW}  Warning: Found $LARGE_FILES large files or databases, removing them...${NC}"
    find "$STAGING_DIR" -type f \( -size +${MAX_FILE_SIZE}c -o -name "*.sqlite" -o -name "*.db" -o -name "*.db-shm" -o -name "*.db-wal" \) -delete 2>/dev/null
fi
if [ "$PYCACHE_DIRS" -gt 0 ]; then
    echo -e "${YELLOW}  Warning: Found $PYCACHE_DIRS __pycache__ directories, removing them...${NC}"
    find "$STAGING_DIR" -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
fi

echo -e "${YELLOW}Step 3: Removing old workspace directory${NC}"
# Delete the old directory to ensure clean state
databricks workspace delete "$WORKSPACE_PATH" --profile "$PROFILE" --recursive 2>&1 || echo "Directory may not exist or already deleted"

echo -e "${YELLOW}Step 4: Creating workspace directory${NC}"
databricks workspace mkdirs "$WORKSPACE_PATH" --profile "$PROFILE" 2>&1 || echo "Directory may already exist"

echo -e "${YELLOW}Step 5: Uploading files from staging directory${NC}"

# Upload from staging directory
databricks workspace import-dir "$STAGING_DIR" "$WORKSPACE_PATH" --profile "$PROFILE" --overwrite

echo ""
echo -e "${GREEN}Upload complete!${NC}"
echo ""
echo -e "${YELLOW}Step 6: Deploying app${NC}"
echo "Deploying app '$APP_NAME' from $WORKSPACE_PATH..."

databricks apps deploy "$APP_NAME" \
  --source-code-path "$WORKSPACE_PATH" \
  --profile "$PROFILE" \
  --mode SNAPSHOT

echo ""
echo -e "${GREEN}Deployment initiated!${NC}"
echo "Check the Databricks Apps UI for deployment status."
echo "App URL will be shown in the Databricks Apps UI after deployment completes."


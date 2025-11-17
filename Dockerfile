FROM python:3.11-slim

WORKDIR /workspace

# Copy requirements and install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY app.py .

# Create files directory
RUN mkdir -p /workspace/files

# Expose port
EXPOSE 8000

# Set environment variables
ENV PYTHONPATH=/workspace
ENV PYTHONUNBUFFERED=1
ENV WORKSPACE_DIR=/workspace
ENV PORT=8000
ENV HOST=0.0.0.0

# Run the application
CMD ["python", "app.py"]


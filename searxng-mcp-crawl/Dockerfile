FROM python:3.11-slim

LABEL maintainer="damin25soka7"
LABEL description="MCP SearXNG Server with Plugin System"

WORKDIR /app

# Copy requirements and install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application files
COPY . .

# Expose the server port
EXPOSE 32769

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
  CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:32769/health')"

# Run the server
CMD ["python", "server.py"]

# Deployment Guide

This guide covers deploying the MCP SearXNG server for production use.

## Table of Contents
1. [Quick Start](#quick-start)
2. [Local Development](#local-development)
3. [Production Deployment](#production-deployment)
4. [Docker Deployment](#docker-deployment)
5. [Configuration](#configuration)
6. [Monitoring](#monitoring)
7. [Security](#security)

## Quick Start

### Prerequisites
- Python 3.8+
- SearXNG instance (optional, can use public instance)
- Linux/macOS/Windows with Python support

### 1. Clone and Setup

```bash
# Clone repository
git clone https://github.com/damin25soka7/asdaadas.git
cd asdaadas/searxng-mcp-crawl

# Create virtual environment
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Configure environment
cp .env.example .env
# Edit .env with your settings

# Start server
python server.py
```

The server will be available at `http://localhost:32769`

## Local Development

### Running the Server

```bash
cd searxng-mcp-crawl
python server.py
```

### Testing

```bash
# Run test suite
python test_server.py

# Check health
curl http://localhost:32769/health

# Test a plugin
curl -X POST http://localhost:32769 \
  -H "Content-Type: application/json" \
  -d '{
    "jsonrpc": "2.0",
    "id": 1,
    "method": "tools/call",
    "params": {
      "name": "get_current_datetime",
      "arguments": {"timezone": "Asia/Seoul"}
    }
  }'
```

### Development Tips

- Server auto-reloads plugins on file changes (requires manual restart)
- Use `CTRL+C` to stop the server gracefully
- Check logs for debugging information
- Test plugins individually before integration

## Production Deployment

### Option 1: systemd (Linux)

1. **Create service file** `/etc/systemd/system/mcp-server.service`:

```ini
[Unit]
Description=MCP SearXNG Server
After=network.target

[Service]
Type=simple
User=www-data
Group=www-data
WorkingDirectory=/opt/mcp-server/searxng-mcp-crawl
Environment="PATH=/opt/mcp-server/venv/bin"
ExecStart=/opt/mcp-server/venv/bin/python server.py
Restart=always
RestartSec=10

# Security
NoNewPrivileges=true
PrivateTmp=true
ProtectSystem=strict
ProtectHome=true
ReadWritePaths=/opt/mcp-server

[Install]
WantedBy=multi-user.target
```

2. **Deploy**:

```bash
# Copy files to production location
sudo mkdir -p /opt/mcp-server
sudo cp -r . /opt/mcp-server/
cd /opt/mcp-server/searxng-mcp-crawl

# Setup virtual environment
sudo python3 -m venv /opt/mcp-server/venv
sudo /opt/mcp-server/venv/bin/pip install -r requirements.txt

# Configure
sudo cp .env.example .env
sudo nano .env  # Edit configuration

# Set permissions
sudo chown -R www-data:www-data /opt/mcp-server

# Enable and start service
sudo systemctl daemon-reload
sudo systemctl enable mcp-server
sudo systemctl start mcp-server

# Check status
sudo systemctl status mcp-server

# View logs
sudo journalctl -u mcp-server -f
```

### Option 2: Nginx Reverse Proxy

1. **Install Nginx**:

```bash
sudo apt install nginx
```

2. **Create Nginx configuration** `/etc/nginx/sites-available/mcp-server`:

```nginx
server {
    listen 80;
    server_name mcp.yourdomain.com;

    location / {
        proxy_pass http://127.0.0.1:32769;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection 'upgrade';
        proxy_set_header Host $host;
        proxy_cache_bypass $http_upgrade;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        
        # Timeouts
        proxy_connect_timeout 60s;
        proxy_send_timeout 60s;
        proxy_read_timeout 60s;
    }

    # Health check endpoint
    location /health {
        proxy_pass http://127.0.0.1:32769/health;
        access_log off;
    }
}
```

3. **Enable and configure**:

```bash
# Enable site
sudo ln -s /etc/nginx/sites-available/mcp-server /etc/nginx/sites-enabled/

# Test configuration
sudo nginx -t

# Restart Nginx
sudo systemctl restart nginx
```

4. **Add SSL with Let's Encrypt**:

```bash
sudo apt install certbot python3-certbot-nginx
sudo certbot --nginx -d mcp.yourdomain.com
```

## Docker Deployment

### Single Container

1. **Build image**:

```bash
cd searxng-mcp-crawl
docker build -t mcp-server:latest .
```

2. **Run container**:

```bash
docker run -d \
  --name mcp-server \
  -p 32769:32769 \
  -e SEARXNG_BASE_URL=http://your-searxng:8080 \
  -e HOST=0.0.0.0 \
  -e PORT=32769 \
  --restart unless-stopped \
  mcp-server:latest
```

### Docker Compose (with SearXNG)

1. **Use provided docker-compose.yml**:

```bash
cd asdaadas
docker-compose up -d
```

2. **Check status**:

```bash
docker-compose ps
docker-compose logs -f mcp-server
```

3. **Stop services**:

```bash
docker-compose down
```

### Docker with External Network

```yaml
version: '3.8'

services:
  mcp-server:
    image: mcp-server:latest
    ports:
      - "32769:32769"
    environment:
      - SEARXNG_BASE_URL=https://public-searxng-instance.com
    networks:
      - web
    labels:
      - "traefik.enable=true"
      - "traefik.http.routers.mcp.rule=Host(`mcp.yourdomain.com`)"

networks:
  web:
    external: true
```

## Configuration

### Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `SEARXNG_BASE_URL` | SearXNG instance URL | `http://localhost:32768` |
| `HOST` | Server bind address | `0.0.0.0` |
| `PORT` | Server port | `32769` |
| `CONTENT_MAX_LENGTH` | Max content length | `10000` |
| `SEARCH_RESULT_LIMIT` | Default search limit | `10` |

### Plugin Configuration

Plugins are automatically loaded from `searxng-mcp-crawl/plugins/`.

To disable a plugin, rename it to start with underscore: `_disabled_plugin.py`

To add a plugin, create a new `.py` file in the plugins directory.

## Monitoring

### Health Checks

```bash
# Simple health check
curl http://localhost:32769/health

# Detailed check with jq
curl -s http://localhost:32769/health | jq
```

### Logging

Server logs include:
- Plugin loading status
- Request/response information
- Error messages and stack traces

```bash
# systemd logs
sudo journalctl -u mcp-server -f

# Docker logs
docker logs -f mcp-server
```

### Monitoring Tools

**Prometheus metrics** (future enhancement):
```python
# Add to server.py
from prometheus_client import Counter, Histogram
requests_total = Counter('mcp_requests_total', 'Total requests')
request_duration = Histogram('mcp_request_duration_seconds', 'Request duration')
```

## Security

### Best Practices

1. **Network Security**:
   - Use firewall to restrict access
   - Deploy behind reverse proxy
   - Use HTTPS in production
   - Enable rate limiting

2. **API Security**:
   ```python
   # Add authentication (future)
   from starlette.middleware import Middleware
   from starlette.middleware.authentication import AuthenticationMiddleware
   ```

3. **System Security**:
   - Run as non-root user
   - Use systemd hardening options
   - Keep dependencies updated
   - Monitor for vulnerabilities

4. **Data Security**:
   - Don't log sensitive data
   - Validate all inputs
   - Sanitize outputs
   - Use environment variables for secrets

### Firewall Configuration

```bash
# Allow only specific IPs
sudo ufw allow from 192.168.1.0/24 to any port 32769

# Or allow from localhost only
sudo ufw deny 32769
# Access via reverse proxy only
```

### Rate Limiting with Nginx

```nginx
limit_req_zone $binary_remote_addr zone=mcp_limit:10m rate=10r/s;

server {
    location / {
        limit_req zone=mcp_limit burst=20 nodelay;
        proxy_pass http://127.0.0.1:32769;
    }
}
```

## Backup and Recovery

### Backup

```bash
# Backup plugin configurations
tar -czf mcp-backup-$(date +%Y%m%d).tar.gz \
  searxng-mcp-crawl/plugins/ \
  searxng-mcp-crawl/.env

# Backup with Docker volumes
docker run --rm \
  -v mcp_data:/data \
  -v $(pwd):/backup \
  alpine tar czf /backup/mcp-data-backup.tar.gz /data
```

### Recovery

```bash
# Restore files
tar -xzf mcp-backup-20250116.tar.gz

# Restart service
sudo systemctl restart mcp-server
```

## Scaling

### Horizontal Scaling

Run multiple instances behind load balancer:

```nginx
upstream mcp_backend {
    least_conn;
    server 127.0.0.1:32769;
    server 127.0.0.1:32770;
    server 127.0.0.1:32771;
}

server {
    location / {
        proxy_pass http://mcp_backend;
    }
}
```

### Performance Tuning

1. **Increase workers** (future enhancement):
```python
# In server.py
uvicorn.run(app, host=config.HOST, port=config.PORT, workers=4)
```

2. **Add caching**:
```python
from starlette.middleware import Middleware
from starlette.middleware.httpsredirect import HTTPSRedirectMiddleware
```

3. **Database for state** (if needed):
```python
# Add Redis for caching
import redis
cache = redis.Redis(host='localhost', port=6379, db=0)
```

## Troubleshooting

### Common Issues

| Issue | Solution |
|-------|----------|
| Port already in use | Change PORT in .env or stop conflicting service |
| SearXNG connection failed | Check SEARXNG_BASE_URL is correct and accessible |
| Plugin not loading | Check Python syntax and import errors |
| Permission denied | Check file permissions and user ownership |
| High memory usage | Reduce CONTENT_MAX_LENGTH and limits |

### Debug Mode

Add verbose logging:
```python
import logging
logging.basicConfig(level=logging.DEBUG)
```

### Service Won't Start

```bash
# Check service status
sudo systemctl status mcp-server

# Check logs
sudo journalctl -u mcp-server -n 50 --no-pager

# Test manually
cd /opt/mcp-server/searxng-mcp-crawl
/opt/mcp-server/venv/bin/python server.py
```

## Maintenance

### Update Dependencies

```bash
cd searxng-mcp-crawl
source venv/bin/activate
pip install --upgrade -r requirements.txt
sudo systemctl restart mcp-server
```

### Update Server

```bash
git pull origin main
sudo systemctl restart mcp-server
```

### Monitor Logs

```bash
# Follow logs
sudo journalctl -u mcp-server -f

# Check errors
sudo journalctl -u mcp-server -p err -n 50
```

## Support

For issues and questions:
- GitHub Issues: https://github.com/damin25soka7/asdaadas/issues
- Check logs first
- Include server version and error messages
- Provide minimal reproduction steps

## Next Steps

- Set up monitoring with Prometheus/Grafana
- Implement authentication
- Add rate limiting
- Create CI/CD pipeline
- Set up automated backups
- Configure alerting

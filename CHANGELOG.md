# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [1.0.0] - 2025-11-16

### Added

#### Core Features
- **RisuAI Bridge Plugin** (`risuai-mcp-bridge.js`)
  - Complete MCP protocol client implementation
  - Support for all 5 MCP server tools
  - Comprehensive error handling and logging
  - Health check and status monitoring
  - Command-based API for easy integration

#### MCP Server
- 5 core plugins pre-installed:
  - `search`: Web search via SearXNG
  - `fetch_webpage`: Advanced web crawling with auto-chunking
  - `get_current_datetime`: Timezone-aware datetime queries
  - `runLLM`: External LLM API integration
  - `tool_planner`: Intelligent tool selection and planning
- Plugin auto-discovery and loading system
- Health check endpoint (`/health`)
- MCP 2024-11-05 protocol support

#### Documentation
- **README.md**: Complete project overview and getting started guide
- **QUICKSTART.md**: 5-minute quick start guide
- **RISUAI_USAGE.md**: Comprehensive usage examples and patterns
- **DEPLOYMENT.md**: Production deployment guide with multiple options
- **CONTRIBUTING.md**: Contribution guidelines and plugin development guide
- **CHANGELOG.md**: This file

#### Testing & Quality
- Automated test suite (`test_server.py`)
  - Health check verification
  - Tool listing tests
  - Individual plugin tests
  - Integration tests
- All tests passing (6/6)
- CodeQL security scan (0 vulnerabilities)

#### Deployment
- **Docker Support**:
  - Dockerfile for server containerization
  - docker-compose.yml with SearXNG integration
  - Health check configuration
- **systemd Service**:
  - Service file template
  - Security hardening options
- **Nginx Configuration**:
  - Reverse proxy setup
  - SSL/TLS configuration example
  - Rate limiting configuration
- Environment configuration (`.env.example`)

#### Development Tools
- `.gitignore` for clean repository
- Virtual environment support
- Requirements management

### Technical Details

#### Dependencies
- Python 3.8+
- starlette >= 0.27.0
- uvicorn >= 0.23.0
- httpx >= 0.24.0
- python-dotenv >= 1.0.0
- beautifulsoup4 >= 4.12.0
- html5lib >= 1.1
- markdown >= 3.5

#### API Endpoints
- `GET /health`: Server health and status
- `POST /`: MCP protocol endpoint (JSON-RPC 2.0)
- `GET /`: Server-Sent Events connection
- `POST /message/{connection_id}`: SSE message handler

#### Environment Variables
- `SEARXNG_BASE_URL`: SearXNG instance URL (default: http://localhost:32768)
- `HOST`: Server bind address (default: 0.0.0.0)
- `PORT`: Server port (default: 32769)
- `CONTENT_MAX_LENGTH`: Max content length for crawling (default: 10000)
- `SEARCH_RESULT_LIMIT`: Default search result limit (default: 10)

### Configuration

#### Default Ports
- MCP Server: 32769
- SearXNG: 32768

#### Plugin System
- Auto-discovery from `plugins/` directory
- Hot reload support (via manual restart)
- Plugin manager for lifecycle management

### Known Limitations

- Search functionality requires working SearXNG instance
- Webpage fetching may fail on some protected sites
- No built-in authentication (use reverse proxy)
- No rate limiting (implement at proxy level)
- Server restart required for plugin updates

### Security

- CodeQL scan: 0 vulnerabilities found
- Input validation on all plugin parameters
- Error messages sanitized
- No hardcoded secrets

### Performance

- Async/await throughout for high concurrency
- Batch webpage fetching with configurable parallelism
- Auto-chunking for large content
- Response size limiting to prevent memory issues

### Compatibility

- **RisuAI**: Compatible with plugin system
- **MCP Protocol**: 2024-11-05 specification
- **SearXNG**: Any instance supporting standard API
- **Python**: 3.8, 3.9, 3.10, 3.11, 3.12
- **Operating Systems**: Linux, macOS, Windows

### Migration Notes

This is the initial release. No migration required.

## [Unreleased]

### Planned Features
- [ ] Authentication and API key support
- [ ] Built-in rate limiting
- [ ] Prometheus metrics endpoint
- [ ] Hot reload for plugins
- [ ] WebSocket support for real-time updates
- [ ] Plugin marketplace/registry
- [ ] Web UI for server management
- [ ] More built-in plugins (weather, translation, etc.)
- [ ] Caching layer for improved performance
- [ ] Database integration for state management

### Roadmap

#### v1.1.0 (Q1 2026)
- Authentication system
- Rate limiting
- More plugins (weather, translation)
- Performance improvements

#### v1.2.0 (Q2 2026)
- Web UI
- Plugin hot reload
- Metrics and monitoring
- Enhanced logging

#### v2.0.0 (Q3 2026)
- Plugin marketplace
- WebSocket support
- Distributed deployment
- Advanced caching

## Development Team

- **damin25soka7**: Lead Developer, Project Maintainer

## License

This project is licensed under the MIT License.

## Links

- **Repository**: https://github.com/damin25soka7/asdaadas
- **Issues**: https://github.com/damin25soka7/asdaadas/issues
- **Pull Requests**: https://github.com/damin25soka7/asdaadas/pulls

## Acknowledgments

- RisuAI community for plugin inspiration
- SearXNG project for search capabilities
- Model Context Protocol (MCP) specification
- All contributors and users

---

For more details on specific changes, see the [git commit history](https://github.com/damin25soka7/asdaadas/commits).

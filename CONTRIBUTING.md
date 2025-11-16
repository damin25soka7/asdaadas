# Contributing Guide

Thank you for your interest in contributing to the MCP SearXNG Bridge project!

## How to Contribute

### 1. Reporting Issues

- Check if the issue already exists
- Provide clear description and reproduction steps
- Include server logs and error messages
- Specify your environment (OS, Python version, etc.)

### 2. Suggesting Features

- Describe the feature and its use case
- Explain how it would benefit users
- Provide examples if possible

### 3. Contributing Code

#### Development Setup

```bash
# Fork and clone the repository
git clone https://github.com/YOUR_USERNAME/asdaadas.git
cd asdaadas

# Create a virtual environment
cd searxng-mcp-crawl
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Create a feature branch
git checkout -b feature/your-feature-name
```

#### Code Style

**Python:**
- Follow PEP 8 style guide
- Use type hints where possible
- Add docstrings to functions and classes
- Keep functions focused and small

**JavaScript:**
- Use ES6+ features
- Add JSDoc comments
- Handle errors gracefully
- Follow consistent naming conventions

#### Testing

```bash
# Run test suite
python test_server.py

# Test specific plugin
python -c "
import asyncio
from plugin_manager import PluginManager
pm = PluginManager()
result = asyncio.run(pm.execute_plugin('search', {'query': 'test'}))
print(result)
"
```

#### Creating a New Plugin

1. Create a new file in `searxng-mcp-crawl/plugins/`:

```python
from plugin_base import MCPPlugin
from typing import Dict, Any

class MyPlugin(MCPPlugin):
    @property
    def name(self) -> str:
        return "my_tool"
    
    @property
    def description(self) -> str:
        return "Description of what this tool does"
    
    @property
    def input_schema(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "param1": {
                    "type": "string",
                    "description": "First parameter"
                },
                "param2": {
                    "type": "integer",
                    "default": 10
                }
            },
            "required": ["param1"]
        }
    
    @property
    def version(self) -> str:
        return "1.0.0"
    
    @property
    def author(self) -> str:
        return "Your Name"
    
    async def execute(self, arguments: Dict[str, Any]) -> Dict[str, Any]:
        param1 = arguments.get("param1")
        param2 = arguments.get("param2", 10)
        
        # Validate inputs
        if not param1:
            return {
                "success": False,
                "error": "param1 is required"
            }
        
        try:
            # Your plugin logic here
            result = f"Processed: {param1} with {param2}"
            
            return {
                "success": True,
                "result": result
            }
        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }
```

2. Test your plugin:

```python
# test_my_plugin.py
import asyncio
from plugins.my_plugin import MyPlugin

async def test():
    plugin = MyPlugin()
    result = await plugin.execute({"param1": "test"})
    print(result)

asyncio.run(test())
```

3. Restart the server to load your plugin

#### Commit Guidelines

- Use clear, descriptive commit messages
- Start with a verb: "Add", "Fix", "Update", "Remove"
- Reference issue numbers when applicable

```bash
git commit -m "Add weather plugin for real-time weather data

- Implements OpenWeatherMap API integration
- Adds temperature and forecast support
- Includes error handling for API failures

Closes #123"
```

#### Pull Request Process

1. **Update Documentation**: Update README.md and relevant docs
2. **Add Tests**: Ensure your code is tested
3. **Check Style**: Run linters and formatters
4. **Create PR**: Provide clear description of changes

PR Template:
```markdown
## Description
[Describe what this PR does]

## Changes
- [ ] Feature 1
- [ ] Feature 2

## Testing
- [ ] All tests pass
- [ ] Manual testing completed

## Documentation
- [ ] Updated README.md
- [ ] Updated API documentation

## Screenshots (if applicable)
[Add screenshots]
```

### 4. Plugin Ideas

Here are some plugin ideas you could contribute:

**Data & APIs:**
- Weather plugin (OpenWeatherMap, WeatherAPI)
- Currency conversion (exchange rates)
- Stock market data
- Cryptocurrency prices
- Wikipedia search and summary

**Utilities:**
- File operations (read, write, list)
- Database queries (SQLite, PostgreSQL)
- Email sending (SMTP)
- QR code generation
- PDF processing

**AI & ML:**
- Image recognition
- Text summarization
- Translation services
- Sentiment analysis
- Text-to-speech

**Web Services:**
- GitHub API integration
- Twitter/X API
- YouTube data
- Reddit posts
- RSS feed reader

**Development Tools:**
- Code formatting
- Linting
- Package search
- Documentation lookup

### 5. Documentation Improvements

Documentation is always welcome! You can:

- Fix typos and grammar
- Add more examples
- Improve existing explanations
- Add troubleshooting tips
- Create video tutorials
- Translate documentation

### 6. Community

- Be respectful and inclusive
- Help others in discussions
- Share your use cases and examples
- Provide constructive feedback

## Development Tips

### Debugging

```python
# Add debug logging to your plugin
import logging
logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)

# In your plugin
logger.debug(f"Processing request: {arguments}")
```

### Testing with curl

```bash
# Test your plugin directly
curl -X POST http://localhost:32769 \
  -H "Content-Type: application/json" \
  -d '{
    "jsonrpc":"2.0",
    "id":1,
    "method":"tools/call",
    "params":{
      "name":"your_plugin",
      "arguments":{"param":"value"}
    }
  }' | jq
```

### Hot Reload (Future Feature)

Currently, plugins require server restart. We're working on hot reload:

```python
# Future: Reload without restart
POST /api/plugins/reload
```

## Code Review Process

1. Maintainers review all PRs
2. At least one approval required
3. All tests must pass
4. Documentation must be updated
5. Code must follow style guidelines

## Release Process

1. Version bump in relevant files
2. Update CHANGELOG.md
3. Create GitHub release
4. Tag version: `v1.0.0`
5. Build and publish Docker image

## Questions?

- Open a discussion on GitHub
- Check existing issues and PRs
- Read the documentation
- Ask in pull request comments

## Recognition

Contributors will be:
- Added to CONTRIBUTORS.md
- Mentioned in release notes
- Credited in documentation

Thank you for contributing! 🎉

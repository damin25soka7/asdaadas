# MCP (Model Context Protocol) 통합 가이드

## 📚 목차

1. [개요](#개요)
2. [MCP란 무엇인가?](#mcp란-무엇인가)
3. [아키텍처](#아키텍처)
4. [MCP 서버 작동 방식](#mcp-서버-작동-방식)
5. [플러그인 시스템](#플러그인-시스템)
6. [커스텀 MCP 도구 만들기](#커스텀-mcp-도구-만들기)
7. [챗봇에 MCP 통합하기](#챗봇에-mcp-통합하기)
8. [구현 예제](#구현-예제)
9. [다른 챗봇으로 이식하기](#다른-챗봇으로-이식하기)
10. [모범 사례](#모범-사례)

---

## 개요

이 가이드는 `searxng-mcp-crawl` 서버를 참조 구현으로 사용하여 챗봇 애플리케이션에 MCP(Model Context Protocol)를 통합하는 방법을 설명합니다. MCP는 AI 어시스턴트가 외부 도구 및 데이터 소스와 상호 작용할 수 있는 표준화된 방법을 제공합니다.

## MCP란 무엇인가?

**MCP(Model Context Protocol)**는 AI 모델이 다음을 수행할 수 있게 하는 프로토콜입니다:
- 사용 가능한 도구를 동적으로 발견
- 구조화된 매개변수로 외부 함수 호출
- 구조화된 응답 수신
- 여러 도구 호출에 걸쳐 컨텍스트 유지

### 주요 이점:
- **확장성**: 플러그인을 통해 새로운 기능 추가가 용이
- **표준화**: 도구 통합을 위한 일관된 인터페이스
- **모듈성**: 도구를 독립적으로 개발 및 배포 가능
- **동적 발견**: 챗봇이 런타임에 사용 가능한 도구를 발견 가능

---

## 아키텍처

### 전체 아키텍처

```
┌─────────────────┐
│   챗봇 UI       │
│  (예: LBI)      │
└────────┬────────┘
         │ HTTP/SSE
         ▼
┌─────────────────┐
│  MCP 서버       │
│  (server.py)    │
├─────────────────┤
│ 플러그인 매니저  │
├─────────────────┤
│   플러그인:      │
│   • search      │
│   • crawl       │
│   • runLLM      │
│   • planner     │
│   • datetime    │
└─────────────────┘
```

### 통신 흐름

1. **초기화**: 챗봇이 MCP 서버에 연결하고 기능을 가져옴
2. **도구 발견**: 챗봇이 사용 가능한 도구 목록을 요청
3. **도구 실행**: 챗봇이 매개변수와 함께 특정 도구를 호출
4. **응답**: MCP 서버가 플러그인을 실행하고 구조화된 결과를 반환

---

## MCP 서버 작동 방식

### 1. 서버 설정 (`server.py`)

MCP 서버는 Starlette로 구축되었으며 두 가지 통신 방법을 지원합니다:

#### HTTP POST (단순 요청/응답)
```python
POST / HTTP/1.1
Content-Type: application/json

{
  "jsonrpc": "2.0",
  "id": 1,
  "method": "tools/call",
  "params": {
    "name": "search",
    "arguments": {
      "query": "Python MCP",
      "limit": 10
    }
  }
}
```

#### 스트리밍을 위한 Server-Sent Events (SSE)
```python
GET / HTTP/1.1
Accept: text/event-stream
```

### 2. 핵심 MCP 메서드

| 메서드 | 목적 | 매개변수 |
|--------|------|----------|
| `initialize` | 연결 설정 | `protocolVersion` |
| `notifications/initialized` | 초기화 확인 | 없음 |
| `tools/list` | 사용 가능한 도구 가져오기 | 없음 |
| `tools/call` | 도구 실행 | `name`, `arguments` |
| `ping` | 상태 확인 | 없음 |

### 3. 응답 형식

```json
{
  "jsonrpc": "2.0",
  "id": 1,
  "result": {
    "content": [
      {
        "type": "text",
        "text": "{\"success\": true, \"data\": ...}"
      }
    ]
  }
}
```

---

## 플러그인 시스템

### 플러그인 아키텍처

MCP 서버는 각 도구가 별도의 플러그인인 플러그인 기반 아키텍처를 사용합니다:

```
plugins/
├── search_plugin.py       # 웹 검색 도구
├── crawl_plugin.py        # 웹페이지 크롤러
├── tool_planner_plugin.py # AI 기반 계획
├── datetime_plugin.py     # 날짜/시간 유틸리티
└── mcp_aiaccess_plugin.py # LLM 실행
```

### 플러그인 베이스 클래스

모든 플러그인은 `MCPPlugin`을 상속받습니다:

```python
from abc import ABC, abstractmethod
from typing import Dict, Any

class MCPPlugin(ABC):
    @property
    @abstractmethod
    def name(self) -> str:
        """도구 이름 (고유 식별자)"""
        pass
    
    @property
    @abstractmethod
    def description(self) -> str:
        """AI를 위한 도구 설명"""
        pass
    
    @property
    @abstractmethod
    def input_schema(self) -> Dict[str, Any]:
        """입력 검증을 위한 JSON 스키마"""
        pass
    
    @abstractmethod
    async def execute(self, arguments: Dict[str, Any]) -> Dict[str, Any]:
        """도구 로직 실행"""
        pass
    
    @property
    def version(self) -> str:
        return "1.0.0"
```

### 플러그인 매니저

`PluginManager` 클래스:
- `plugins/` 디렉토리에서 플러그인 자동 발견
- 시작 시 플러그인을 동적으로 로드
- 플러그인 목록 및 실행 제공
- 핫 리로딩 지원

```python
class PluginManager:
    def __init__(self, plugins_dir: str = "plugins"):
        self.plugins_dir = Path(plugins_dir)
        self.plugins: Dict[str, MCPPlugin] = {}
        self.load_plugins()
    
    def list_plugins(self) -> List[Dict[str, Any]]:
        """모든 사용 가능한 플러그인을 MCP 도구로 나열"""
        return [
            {
                "name": plugin.name,
                "description": plugin.description,
                "inputSchema": plugin.input_schema
            }
            for plugin in self.plugins.values()
        ]
    
    async def execute_plugin(self, name: str, arguments: Dict[str, Any]) -> Any:
        """이름으로 플러그인 실행"""
        if name not in self.plugins:
            return {"error": f"도구 '{name}'을 찾을 수 없습니다"}
        
        plugin = self.plugins[name]
        return await plugin.execute(arguments)
```

---

## 커스텀 MCP 도구 만들기

### 예제: 간단한 계산기 플러그인

```python
from plugin_base import MCPPlugin
from typing import Dict, Any

class CalculatorPlugin(MCPPlugin):
    @property
    def name(self) -> str:
        return "calculator"
    
    @property
    def description(self) -> str:
        return "기본 수학 연산 수행. 매개변수: operation (add/subtract/multiply/divide), a, b"
    
    @property
    def input_schema(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "operation": {
                    "type": "string",
                    "enum": ["add", "subtract", "multiply", "divide"]
                },
                "a": {"type": "number"},
                "b": {"type": "number"}
            },
            "required": ["operation", "a", "b"]
        }
    
    @property
    def version(self) -> str:
        return "1.0.0"
    
    async def execute(self, arguments: Dict[str, Any]) -> Dict[str, Any]:
        operation = arguments.get("operation")
        a = arguments.get("a")
        b = arguments.get("b")
        
        try:
            if operation == "add":
                result = a + b
            elif operation == "subtract":
                result = a - b
            elif operation == "multiply":
                result = a * b
            elif operation == "divide":
                if b == 0:
                    return {"success": False, "error": "0으로 나눌 수 없습니다"}
                result = a / b
            else:
                return {"success": False, "error": "잘못된 연산"}
            
            return {
                "success": True,
                "operation": operation,
                "a": a,
                "b": b,
                "result": result
            }
        except Exception as e:
            return {"success": False, "error": str(e)}
```

### 플러그인 개발 체크리스트

- ✅ `MCPPlugin` 상속
- ✅ 필수 속성 구현 (`name`, `description`, `input_schema`)
- ✅ `execute()` 메서드 구현
- ✅ I/O 작업에 async/await 사용
- ✅ 구조화된 JSON 응답 반환
- ✅ 오류 처리 포함
- ✅ 적절한 로깅 추가
- ✅ 입력 매개변수 검증
- ✅ 플러그인을 집중적이고 단일 목적으로 유지

---

## 챗봇에 MCP 통합하기

### 단계 1: MCP 연결 초기화

```javascript
// 예제: JavaScript/TypeScript 챗봇 클라이언트
class MCPClient {
    constructor(serverUrl) {
        this.serverUrl = serverUrl;
        this.tools = [];
    }
    
    async initialize() {
        // 초기화 요청 전송
        const response = await fetch(this.serverUrl, {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify({
                jsonrpc: '2.0',
                id: 1,
                method: 'initialize',
                params: {
                    protocolVersion: '2024-11-05',
                    capabilities: {},
                    clientInfo: {
                        name: 'my-chatbot',
                        version: '1.0.0'
                    }
                }
            })
        });
        
        return await response.json();
    }
    
    async listTools() {
        const response = await fetch(this.serverUrl, {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify({
                jsonrpc: '2.0',
                id: 2,
                method: 'tools/list',
                params: {}
            })
        });
        
        const data = await response.json();
        this.tools = data.result.tools;
        return this.tools;
    }
    
    async callTool(toolName, arguments) {
        const response = await fetch(this.serverUrl, {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify({
                jsonrpc: '2.0',
                id: Date.now(),
                method: 'tools/call',
                params: {
                    name: toolName,
                    arguments: arguments
                }
            })
        });
        
        const data = await response.json();
        return JSON.parse(data.result.content[0].text);
    }
}
```

### 단계 2: 대화에서 도구 사용

```javascript
// MCP 클라이언트 초기화
const mcp = new MCPClient('http://localhost:32769');
await mcp.initialize();
await mcp.listTools();

// 검색 도구 사용
const searchResult = await mcp.callTool('search', {
    query: 'Model Context Protocol',
    limit: 10
});

// 크롤 도구 사용
const crawlResult = await mcp.callTool('fetch_webpage', {
    urls: ['https://example.com'],
    limit: 1
});

// LLM 도구 사용
const llmResult = await mcp.callTool('runLLM', {
    messages: [
        {role: 'user', content: '요약해줘: ...'}
    ]
});
```

### 단계 3: AI 모델과 통합

```javascript
// 예제: MCP 도구를 AI 대화와 통합
async function handleUserMessage(userMessage, conversationHistory) {
    // 1. 대화 기록에 사용자 메시지 추가
    conversationHistory.push({
        role: 'user',
        content: userMessage
    });
    
    // 2. 사용 가능한 도구 목록 가져오기
    const tools = await mcp.listTools();
    
    // 3. 도구 설명과 함께 AI에 전송
    const aiResponse = await callAI({
        messages: conversationHistory,
        tools: tools,
        tool_choice: 'auto'
    });
    
    // 4. AI가 도구를 사용하려는 경우
    if (aiResponse.tool_calls) {
        for (const toolCall of aiResponse.tool_calls) {
            const toolResult = await mcp.callTool(
                toolCall.function.name,
                JSON.parse(toolCall.function.arguments)
            );
            
            // 대화에 도구 결과 추가
            conversationHistory.push({
                role: 'tool',
                name: toolCall.function.name,
                content: JSON.stringify(toolResult)
            });
        }
        
        // 도구 결과와 함께 최종 AI 응답 가져오기
        return await callAI({
            messages: conversationHistory
        });
    }
    
    return aiResponse;
}
```

---

## 구현 예제

### 완전한 통합 예제

이 예제는 `LBI` 챗봇이 MCP 서버와 통합되는 방식을 보여줍니다:

```javascript
// LBI 챗봇 MCP 통합
class LBIChatbot {
    constructor(config) {
        this.mcpServerUrl = config.mcpServerUrl || 'http://localhost:32769';
        this.mcpClient = null;
        this.availableTools = [];
    }
    
    async initialize() {
        // MCP 연결 초기화
        this.mcpClient = new MCPClient(this.mcpServerUrl);
        await this.mcpClient.initialize();
        
        // 사용 가능한 도구 발견
        this.availableTools = await this.mcpClient.listTools();
        console.log(`${this.availableTools.length}개의 MCP 도구 발견`);
    }
    
    async processMessage(userInput) {
        // 1. 도구가 필요한지 판단
        const needsTools = this.analyzeNeedsTools(userInput);
        
        if (!needsTools) {
            return await this.generateResponse(userInput);
        }
        
        // 2. AI를 사용하여 도구 사용 선택 및 계획
        const planResult = await this.mcpClient.callTool('tool_planner', {
            user_query: userInput,
            planner_llm_config: {
                url: this.aiProviderUrl,
                apiKey: this.aiApiKey,
                model: this.aiModel
            },
            max_steps: 5
        });
        
        if (!planResult.success) {
            return await this.generateResponse(userInput);
        }
        
        // 3. 계획 단계 실행
        const executionResults = [];
        for (const step of planResult.plan) {
            const result = await this.mcpClient.callTool(
                step.tool,
                step.arguments
            );
            executionResults.push({
                step: step.step,
                tool: step.tool,
                result: result
            });
        }
        
        // 4. 도구 결과와 함께 최종 응답 생성
        return await this.generateResponseWithContext(
            userInput,
            executionResults
        );
    }
    
    analyzeNeedsTools(input) {
        // 사용자 쿼리가 외부 도구를 필요로 하는지 확인
        const toolKeywords = [
            '검색', '찾아', '조회', '무엇', '누구',
            '가져', '얻어', '다운', '최신', '지금', '오늘'
        ];
        
        const lowerInput = input.toLowerCase();
        return toolKeywords.some(keyword => lowerInput.includes(keyword));
    }
    
    async generateResponseWithContext(input, toolResults) {
        // 도구 결과를 컨텍스트로 결합
        const context = toolResults.map(tr => 
            `도구: ${tr.tool}\n결과: ${JSON.stringify(tr.result, null, 2)}`
        ).join('\n\n');
        
        // 도구 컨텍스트와 함께 AI 응답 생성
        return await this.callAI({
            messages: [
                {
                    role: 'system',
                    content: '당신은 유용한 어시스턴트입니다. 제공된 도구 결과를 사용하여 정확하게 답변하세요.'
                },
                {
                    role: 'user',
                    content: `도구의 컨텍스트:\n${context}\n\n사용자 질문: ${input}`
                }
            ]
        });
    }
}
```

---

## 다른 챗봇으로 이식하기

### 다른 챗봇으로 이식 가능한가?

**네!** MCP 아키텍처는 챗봇에 구애받지 않도록 설계되었습니다. 이식 방법은 다음과 같습니다:

### 웹 기반 챗봇의 경우

1. **MCP 클라이언트 라이브러리 추가**
   - MCP 프로토콜용 HTTP 클라이언트 구현
   - POST 및 SSE 통신 방법 모두 지원
   - JSON-RPC 2.0 형식 처리

2. **런타임에 도구 발견**
   ```javascript
   // 챗봇 초기화 시
   const tools = await mcp.listTools();
   // 나중에 사용할 도구 저장
   ```

3. **도구 호출 통합**
   - AI 모델이 도구를 호출하려는 시점 감지
   - MCP를 통해 도구 실행
   - 결과를 AI에 다시 전달

### 데스크톱 챗봇(예: Electron)

```javascript
// 메인 프로세스에서
const { app } = require('electron');
const MCPClient = require('./mcp-client');

let mcpClient;

app.on('ready', async () => {
    mcpClient = new MCPClient('http://localhost:32769');
    await mcpClient.initialize();
    
    // 렌더러 프로세스에 노출
    ipcMain.handle('mcp-call-tool', async (event, toolName, args) => {
        return await mcpClient.callTool(toolName, args);
    });
});
```

### 모바일 앱(React Native)

```javascript
import axios from 'axios';

class MCPMobileClient {
    constructor(serverUrl) {
        this.serverUrl = serverUrl;
    }
    
    async callTool(toolName, arguments) {
        try {
            const response = await axios.post(this.serverUrl, {
                jsonrpc: '2.0',
                id: Date.now(),
                method: 'tools/call',
                params: { name: toolName, arguments }
            });
            
            return JSON.parse(response.data.result.content[0].text);
        } catch (error) {
            console.error('MCP 호출 실패:', error);
            return { success: false, error: error.message };
        }
    }
}
```

### 터미널/CLI 챗봇(Python)

```python
import requests
import json

class MCPTerminalClient:
    def __init__(self, server_url):
        self.server_url = server_url
        self.session = requests.Session()
    
    def initialize(self):
        response = self.session.post(self.server_url, json={
            'jsonrpc': '2.0',
            'id': 1,
            'method': 'initialize',
            'params': {
                'protocolVersion': '2024-11-05',
                'capabilities': {},
                'clientInfo': {'name': 'terminal-bot', 'version': '1.0'}
            }
        })
        return response.json()
    
    def call_tool(self, tool_name, arguments):
        response = self.session.post(self.server_url, json={
            'jsonrpc': '2.0',
            'id': 2,
            'method': 'tools/call',
            'params': {'name': tool_name, 'arguments': arguments}
        })
        
        data = response.json()
        return json.loads(data['result']['content'][0]['text'])

# 사용법
mcp = MCPTerminalClient('http://localhost:32769')
mcp.initialize()

# 검색 예제
result = mcp.call_tool('search', {'query': 'Python', 'limit': 5})
print(result)
```

### 모든 챗봇을 위한 통합 체크리스트

- ✅ JSON-RPC 2.0 프로토콜용 HTTP 클라이언트
- ✅ 시작 시 연결 초기화
- ✅ 동적으로 도구 발견
- ✅ 도구 스키마를 AI 모델 형식으로 변환
- ✅ AI가 요청하면 도구 실행
- ✅ 도구 오류를 우아하게 처리
- ✅ 도구 결과를 AI에 다시 전달
- ✅ 스트리밍 지원 (선택 사항, 긴 작업용)

---

## 모범 사례

### 1. 오류 처리

항상 오류를 우아하게 처리하세요:

```python
async def execute(self, arguments: Dict[str, Any]) -> Dict[str, Any]:
    try:
        # 도구 로직
        result = await self.perform_operation(arguments)
        return {"success": True, "data": result}
    except ValueError as e:
        return {"success": False, "error": f"잘못된 입력: {str(e)}"}
    except Exception as e:
        return {"success": False, "error": f"내부 오류: {str(e)}"}
```

### 2. 입력 검증

스키마에 따라 모든 입력을 검증하세요:

```python
def validate_arguments(self, arguments):
    query = arguments.get("query", "").strip()
    if not query:
        raise ValueError("쿼리 매개변수가 필요합니다")
    
    limit = arguments.get("limit", 10)
    if not isinstance(limit, int) or limit < 1 or limit > 100:
        raise ValueError("제한은 1에서 100 사이여야 합니다")
```

### 3. 로깅

포괄적인 로깅 추가:

```python
print(f"\n🔍 {self.name}")
print(f"   쿼리: {query}")
print(f"   매개변수: {params}")
print(f"   ✅ 성공: {len(results)}개 결과")
```

### 4. 성능

- I/O 작업에 async/await 사용
- 적절한 곳에 캐싱 구현
- 합리적인 타임아웃 설정
- 응답 크기 제한

### 5. 보안

- 모든 입력 검증
- 사용자 제공 데이터 살균
- 비밀에 환경 변수 사용
- 속도 제한 구현
- 프로덕션에서 HTTPS 사용

### 6. 문서화

각 도구를 명확하게 문서화하세요:

```python
@property
def description(self) -> str:
    return """
    SearXNG를 통한 웹 검색.
    
    매개변수:
    - query (필수): 검색 쿼리 문자열
    - limit (선택, 기본값=10): 결과 수 (1-50)
    - category (선택, 기본값='general'): 검색 카테고리
    
    반환값:
    {
        "success": bool,
        "results": [...],
        "results_count": int
    }
    """
```

### 7. 테스트

플러그인을 철저히 테스트하세요:

```python
# test_plugin.py
import pytest
from plugins.search_plugin import SearchPlugin

@pytest.mark.asyncio
async def test_search_basic():
    plugin = SearchPlugin()
    result = await plugin.execute({
        "query": "테스트 쿼리",
        "limit": 5
    })
    
    assert result["success"] == True
    assert "results" in result
    assert len(result["results"]) <= 5

@pytest.mark.asyncio
async def test_search_validation():
    plugin = SearchPlugin()
    result = await plugin.execute({"query": ""})
    
    assert result["success"] == False
    assert "error" in result
```

---

## 결론

MCP(Model Context Protocol)는 챗봇에 기능을 추가하는 강력하고 확장 가능한 방법을 제공합니다:

- **표준화됨**: JSON-RPC 2.0 프로토콜 사용
- **모듈식**: 플러그인 기반 아키텍처
- **동적**: 재시작 없이 도구 추가 가능
- **범용**: 모든 챗봇 플랫폼에 통합 가능
- **확장 가능**: 여러 도구 및 복잡한 워크플로 지원

`searxng-mcp-crawl` 서버는 자체 MCP 지원 애플리케이션의 템플릿으로 사용할 수 있는 완전한 구현을 보여줍니다.

더 많은 예제 및 참조 구현은 다음을 참조하세요:
- `server.py` - MCP 서버 구현
- `plugin_manager.py` - 플러그인 로딩 및 관리
- `plugins/` - 도구 구현 예제
- `LBI-0.35.0-pre17_개조.js` - 챗봇 통합 예제

---

## 추가 리소스

- [MCP 프로토콜 사양](https://spec.modelcontextprotocol.io/)
- [Anthropic MCP 문서](https://www.anthropic.com/news/model-context-protocol)
- [LobeChat MCP 통합](https://github.com/lobehub/lobe-chat)

---

*마지막 업데이트: 2024년 11월*

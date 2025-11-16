from plugin_base import MCPPlugin
from typing import Dict, Any, List, Optional
import httpx
import json
import asyncio
import re

class ToolPlannerPlugin(MCPPlugin):
    """
    Advanced Tool Planner with Intelligent Parameter Optimization
    
    Features:
    - Dynamic tool discovery
    - Intelligent parameter customization per step
    - Dedicated LLM configuration (separate from runLLM)
    - Context-aware planning
    - Token-optimized tool descriptions
    """
    
    def __init__(self):
        self.plugin_manager = None
    
    @property
    def name(self) -> str:
        return "tool_planner"
    
    @property
    def description(self) -> str:
        return "Create optimized execution plan. Params: user_query, planner_llm_config, max_steps=5."
    
    @property
    def input_schema(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "user_query": {
                    "type": "string"
                },
                "planner_llm_config": {
                    "type": "object",
                    "properties": {
                        "url": {"type": "string"},
                        "apiKey": {"type": "string"},
                        "model": {"type": "string"}
                    },
                    "required": ["url", "apiKey", "model"]
                },
                "max_steps": {
                    "type": "integer",
                    "default": 5,
                    "minimum": 1,
                    "maximum": 10
                },
                "complexity": {
                    "type": "string",
                    "enum": ["simple", "moderate", "detailed"],
                    "default": "moderate"
                }
            },
            "required": ["user_query", "planner_llm_config"]
        }
    
    @property
    def version(self) -> str:
        return "3.5.0"
    
    @property
    def author(self) -> str:
        return "damin25soka7"
    
    def set_plugin_manager(self, plugin_manager):
        """Inject plugin manager to access available tools"""
        self.plugin_manager = plugin_manager
    
    def get_available_tools(self) -> List[Dict[str, str]]:
        """Dynamically get all available tools from plugin manager"""
        if not self.plugin_manager:
            print("   ⚠️ Plugin manager not available")
            return []
        
        try:
            tools = self.plugin_manager.list_plugins()
            # Exclude self
            tools = [t for t in tools if t['name'] != 'tool_planner']
            return tools
        except Exception as e:
            print(f"   ⚠️ Error getting tools: {e}")
            return []
    
    async def call_planner_llm(self, messages: List[Dict], config: Dict) -> str:
        """Call dedicated planner LLM"""
        url = config.get('url', '').strip()
        api_key = config.get('apiKey', '').strip()
        model = config.get('model', '').strip()
        
        if not all([url, api_key, model]):
            raise ValueError("Planner LLM config incomplete (url, apiKey, model required)")
        
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {api_key}"
        }
        
        payload = {
            "model": model,
            "messages": messages,
            "temperature": 0.2,
            "max_tokens": 2000
        }
        
        print(f"   🤖 Calling Planner LLM: {model}")
        
        # Retry logic for planner
        for attempt in range(1, 4):
            try:
                async with httpx.AsyncClient(timeout=120.0) as client:
                    response = await client.post(url, headers=headers, json=payload)
                    
                    if response.status_code in [429, 403, 503]:
                        if attempt < 3:
                            wait_time = attempt * 3
                            print(f"   ⚠️ Rate limit (HTTP {response.status_code}), retrying in {wait_time}s...")
                            await asyncio.sleep(wait_time)
                            continue
                    
                    response.raise_for_status()
                    data = response.json()
                    
                    if 'choices' in data and len(data['choices']) > 0:
                        return data['choices'][0]['message']['content']
                    elif 'content' in data:
                        return data['content']
                    else:
                        raise ValueError("Unexpected LLM response format")
            
            except Exception as e:
                if attempt < 3:
                    print(f"   ⚠️ Attempt {attempt} failed: {str(e)[:100]}")
                    await asyncio.sleep(attempt * 2)
                    continue
                raise
        
        raise Exception("Failed to get planner LLM response after 3 attempts")
    
    def clean_json_response(self, response: str) -> str:
        """Clean and extract JSON from LLM response"""
        response_clean = response.strip()
        
        # 1. 마크다운 코드 블록 제거
        if response_clean.startswith('```'):
            lines = response_clean.split('\n')
            # json 또는 첫 줄 제거
            if lines[0].strip().lower() in ['```json', '```']:
                lines = lines[1:]
            # 마지막 ``` 제거
            if lines and lines[-1].strip() == '```':
                lines = lines[:-1]
            response_clean = '\n'.join(lines)
        
        # 2. 앞뒤 공백 제거
        response_clean = response_clean.strip()
        
        # 3. JSON 추출 (텍스트 안에 JSON이 포함된 경우)
        if not response_clean.startswith('{'):
            json_start = response_clean.find('{')
            if json_start != -1:
                response_clean = response_clean[json_start:]
        
        if not response_clean.endswith('}'):
            json_end = response_clean.rfind('}')
            if json_end != -1:
                response_clean = response_clean[:json_end + 1]
        
        # 4. 주석 제거 (JSON5 스타일)
        response_clean = re.sub(r'//.*?\n', '\n', response_clean)
        response_clean = re.sub(r'/\*.*?\*/', '', response_clean, flags=re.DOTALL)
        
        # 5. 후행 쉼표 제거 (JSON 표준 위반)
        response_clean = re.sub(r',(\s*[}\]])', r'\1', response_clean)
        
        return response_clean
    
    async def execute(self, arguments: Dict[str, Any]) -> Dict[str, Any]:
        """Create intelligent tool execution plan with optimized parameters"""
        
        user_query = arguments.get('user_query', '').strip()
        planner_llm_config = arguments.get('planner_llm_config', {})
        context = arguments.get('context', '')
        
        # Step constraints
        exact_steps = arguments.get('exact_steps')
        min_steps = arguments.get('min_steps', 1)
        max_steps = arguments.get('max_steps', 5)
        complexity = arguments.get('complexity', 'moderate')
        
        # Tool preferences
        preferred_tools = arguments.get('preferred_tools', [])
        avoid_tools = arguments.get('avoid_tools', [])
        
        # Validation
        if not user_query:
            return {'success': False, 'error': 'user_query is required'}
        
        if not planner_llm_config or not all(k in planner_llm_config for k in ['url', 'apiKey', 'model']):
            return {
                'success': False,
                'error': 'planner_llm_config (url, apiKey, model) is required'
            }
        
        # Step count logic
        if exact_steps:
            step_constraint = f"Use EXACTLY {exact_steps} steps, no more, no less."
            min_steps = exact_steps
            max_steps = exact_steps
        else:
            step_constraint = f"Use between {min_steps} and {max_steps} steps."
        
        print(f"\n{'='*70}")
        print(f"🧠 TOOL PLANNER v3.5 (Ultra-Minimal Schema)")
        print(f"Query: {user_query}")
        print(f"Step constraint: {step_constraint}")
        print(f"Complexity: {complexity}")
        print(f"Planner Model: {planner_llm_config.get('model', 'N/A')}")
        
        # Get available tools
        available_tools = self.get_available_tools()
        
        if not available_tools:
            return {'success': False, 'error': 'No tools available'}
        
        print(f"📦 Discovered {len(available_tools)} tools:")
        for tool in available_tools[:10]:
            print(f"   - {tool['name']}")
        
        if preferred_tools:
            print(f"✨ Preferred: {', '.join(preferred_tools)}")
        if avoid_tools:
            print(f"🚫 Avoid: {', '.join(avoid_tools)}")
        print(f"{'='*70}")
        
        # Filter tools
        filtered_tools = [
            tool for tool in available_tools 
            if tool['name'] not in avoid_tools
        ]
        
        # Build ULTRA-COMPACT tool descriptions
        tools_description = []
        for tool in filtered_tools:
            tool_name = tool['name']
            
            # 도구 이름만 (설명 최소화)
            tool_desc = f"- {tool_name}"
            tools_description.append(tool_desc)
        
        tools_text = "\n".join(tools_description)
        
        print(f"   📝 Tool descriptions: {len(tools_text)} chars (ultra-minimal)")
        
        # Complexity guidelines
        complexity_guide = {
            "simple": "Minimal steps, conservative parameters.",
            "moderate": "Balanced approach.",
            "detailed": "Comprehensive, generous parameters."
        }
        
        # Context addition
        context_text = f"\nContext: {context}" if context else ""
        
        # Build planning prompt (초경량)
        planning_prompt = f"""Create execution plan.

Query: {user_query}{context_text}

Tools: {tools_text}

Rules:
- {step_constraint}
- Complexity: {complexity}

search params: query, limit (10-30), category, time_range
fetch_webpage params: urls, limit (3-15), max_length (5000-10000), auto_chunk:true
runLLM params: messages only (NO url/apiKey/model)
get_current_datetime params: cities, format

Return JSON:
{{
  "main_query": "...",
  "plan": [
    {{"step": 1, "tool": "...", "arguments": {{}}, "purpose": "..."}}
  ],
  "total_steps": {exact_steps if exact_steps else "N"}
}}
"""
        
        try:
            response = await self.call_planner_llm([
                {
                    "role": "system",
                    "content": "You are a planner. Return valid JSON only."
                },
                {
                    "role": "user",
                    "content": planning_prompt
                }
            ], planner_llm_config)
            
            print(f"   ✅ Planner response received ({len(response)} chars)")
            
            # Clean JSON response
            response_clean = self.clean_json_response(response)
            
            print(f"   🔍 Cleaned JSON preview: {response_clean[:200]}...")
            
            try:
                plan_data = json.loads(response_clean)
            except json.JSONDecodeError as e:
                # Debug output
                print(f"   ❌ JSON parse failed at position {e.pos}")
                print(f"   📄 Context: ...{response_clean[max(0, e.pos-50):e.pos+50]}...")
                
                # Save for debugging
                try:
                    with open('planner_response_debug.json', 'w', encoding='utf-8') as f:
                        f.write(response_clean)
                    print(f"   💾 Saved to planner_response_debug.json")
                except:
                    pass
                
                return {
                    'success': False,
                    'error': f'JSON parse error: {str(e)}',
                    'raw_response_preview': response[:500]
                }
            
            # Validation
            if 'main_query' not in plan_data or 'plan' not in plan_data:
                return {
                    'success': False,
                    'error': 'Invalid plan: missing main_query or plan'
                }
            
            actual_steps = len(plan_data['plan'])
            
            # Validate step count
            if exact_steps and actual_steps != exact_steps:
                print(f"   ⚠️ Warning: {actual_steps} steps, expected {exact_steps}")
            
            # Validate tools
            available_tool_names = {t['name']: t for t in filtered_tools}
            invalid_tools = []
            
            for step in plan_data['plan']:
                tool_name = step.get('tool')
                if tool_name not in available_tool_names:
                    invalid_tools.append(tool_name)
            
            if invalid_tools:
                print(f"   ⚠️ Unavailable tools: {', '.join(invalid_tools)}")
            
            print(f"\n   📋 Optimized Plan:")
            print(f"   Main Query: {plan_data['main_query']}")
            print(f"   Total Steps: {actual_steps}")
            
            for step in plan_data['plan']:
                status = "✅" if step['tool'] in available_tool_names else "❌"
                args_summary = ", ".join([f"{k}={v}" for k, v in list(step.get('arguments', {}).items())[:3]])
                purpose = step.get('purpose', 'N/A')[:50]
                print(f"      {status} {step['step']}. {step['tool']}({args_summary}) - {purpose}")
            
            print(f"\n{'='*70}")
            print("✅ PLANNING COMPLETE")
            print(f"{'='*70}\n")
            
            return {
                'success': True,
                'main_query': plan_data['main_query'],
                'query_analysis': plan_data.get('query_analysis', {}),
                'plan': plan_data['plan'],
                'explanation': plan_data.get('explanation', ''),
                'total_steps': actual_steps,
                'constraints': {
                    'exact_steps': exact_steps,
                    'min_steps': min_steps,
                    'max_steps': max_steps,
                    'complexity': complexity
                },
                'original_query': user_query,
                'planner_model': planner_llm_config.get('model'),
                'tools_available': len(filtered_tools),
                'invalid_tools': invalid_tools if invalid_tools else None
            }
        
        except json.JSONDecodeError as e:
            print(f"   ❌ JSON parse error: {str(e)}")
            return {
                'success': False,
                'error': f'Failed to parse planner LLM response: {str(e)}',
                'raw_response_preview': response[:500] if 'response' in locals() else 'N/A'
            }
        
        except Exception as e:
            print(f"   ❌ Planning error: {str(e)}")
            return {
                'success': False,
                'error': str(e)
            }
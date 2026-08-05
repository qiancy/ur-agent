#!/usr/bin/env python3
"""Test script to diagnose chat interface 500 error."""
import sys
sys.path.insert(0, '/workspace/research/unires-agent')

# Patch StructuredTool._parse_input BEFORE importing agents
from langchain_core.tools import StructuredTool
import json

def patched_parse_input(self, tool_input):
    """Custom parse_input that handles JSON strings."""
    if isinstance(tool_input, str):
        try:
            parsed = json.loads(tool_input)
            if isinstance(parsed, dict):
                tool_input = parsed
            else:
                pass
        except json.JSONDecodeError:
            pass
    
    input_args = self.args_schema
    if isinstance(tool_input, str):
        if input_args is not None:
            key_ = next(iter(input_args.__fields__.keys()))
            input_args.validate({key_: tool_input})
        return tool_input
    else:
        if input_args is not None:
            result = input_args.parse_obj(tool_input)
            return {
                k: getattr(result, k)
                for k, v in result.dict().items()
                if k in tool_input
            }
    return tool_input

StructuredTool._parse_input = patched_parse_input

def test_imports():
    print("=" * 60)
    print("TEST 1: Importing modules")
    print("=" * 60)
    
    try:
        from src.agents.agent import create_uni_resource_agent, get_llm
        print("✓ src.agents.agent imported successfully")
    except Exception as e:
        print(f"✗ src.agents.agent import failed: {e}")
        return False
    
    try:
        from src.tools import ALL_TOOLS
        print(f"✓ src.tools imported successfully ({len(ALL_TOOLS)} tools)")
    except Exception as e:
        print(f"✗ src.tools import failed: {e}")
        return False
    
    return True

def test_agent_creation():
    print("\n" + "=" * 60)
    print("TEST 2: Creating agent")
    print("=" * 60)
    
    try:
        # Re-import to get fresh agent with patched tools
        from src.agents.agent import create_uni_resource_agent
        agent = create_uni_resource_agent()
        print("✓ Agent created successfully")
        return True
    except Exception as e:
        print(f"✗ Agent creation failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_llm_connection():
    print("\n" + "=" * 60)
    print("TEST 3: LLM connection")
    print("=" * 60)
    
    try:
        from src.agents.agent import get_llm
        llm = get_llm()
        print(f"✓ LLM initialized: {llm.model_name}")
        
        # Test simple call
        result = llm.invoke("hello")
        print(f"✓ LLM response: {result.content[:50]}...")
        return True
    except Exception as e:
        print(f"✗ LLM test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_full_chat():
    print("\n" + "=" * 60)
    print("TEST 4: Full chat test")
    print("=" * 60)
    
    try:
        # Re-import to get fresh agent with patched tools
        from src.agents.agent import create_uni_resource_agent
        from src.tools import ALL_TOOLS
        
        agent = create_uni_resource_agent()
        
        # Test query with AgentExecutor
        from langchain.agents import AgentExecutor
        agent_executor = AgentExecutor(
            agent=agent,
            tools=ALL_TOOLS,
            verbose=False,
            handle_parsing_errors=True,
            max_iterations=30
        )
        
        result = agent_executor.invoke({"input": "hello"})
        print(f"Response: {result.get('output', 'No output')[:200]}...")
        return True
    except Exception as e:
        print(f"✗ Full chat test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    print("\n" + "=" * 60)
    print("UNI-RESOURCE AGENT CHAT INTERFACE DIAGNOSIS")
    print("=" * 60)
    
    results = []
    results.append(("Imports", test_imports()))
    results.append(("Agent Creation", test_agent_creation()))
    results.append(("LLM Connection", test_llm_connection()))
    results.append(("Full Chat", test_full_chat()))
    
    print("\n" + "=" * 60)
    print("DIAGNOSIS REPORT")
    print("=" * 60)
    
    all_passed = True
    for name, passed in results:
        status = "PASS" if passed else "FAIL"
        print(f"{name}: {status}")
        if not passed:
            all_passed = False
    
    print("\n" + "=" * 60)
    if all_passed:
        print("RESULT: All tests passed. Chat interface should work.")
    else:
        print("RESULT: Some tests failed. See details above.")
    print("=" * 60)

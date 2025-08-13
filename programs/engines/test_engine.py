#!/usr/bin/env python3
"""
Test script for the ToolChatEngine to verify it works correctly.
"""
import sys
import os
from pathlib import Path
import asyncio

# Add src directory to Python path
src_path = Path(__file__).parent.parent.parent / "src"
if str(src_path) not in sys.path:
    sys.path.insert(0, str(src_path))

from llmgine.llm import SessionID
from tool_chat_engine import ToolChatEngine, ToolChatEngineCommand
from tools.test_tools import get_weather
from llmgine.bootstrap import ApplicationBootstrap, ApplicationConfig


async def test_engine():
    """Test the ToolChatEngine with a simple weather query."""
    print("Starting ToolChatEngine test...")
    
    # Initialize the bootstrap
    config = ApplicationConfig(enable_console_handler=False)
    bootstrap = ApplicationBootstrap(config)
    await bootstrap.bootstrap()
    
    # Create the engine
    engine = ToolChatEngine(session_id=SessionID("test"))
    
    # Register the weather tool
    await engine.register_tool(get_weather)
    print("Tool registered successfully")
    
    # Test a simple query
    command = ToolChatEngineCommand(prompt="What is the weather in Paris?")
    result = await engine.handle_command(command)
    
    print(f"\nTest Result:")
    print(f"Success: {result.success}")
    print(f"Response: {result.result}")
    print(f"Error: {result.error}")
    
    return result.success


async def main():
    """Main test function."""
    try:
        success = await test_engine()
        if success:
            print("\n✅ ToolChatEngine test passed!")
            return 0
        else:
            print("\n❌ ToolChatEngine test failed!")
            return 1
    except Exception as e:
        print(f"\n❌ Test failed with exception: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)

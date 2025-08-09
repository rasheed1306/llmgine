import asyncio
import json
import uuid
from dataclasses import dataclass
from typing import Any

from litellm import acompletion

from llmgine.bus.bus import MessageBus
from llmgine.llm import AsyncOrSyncToolFunction, SessionID
from llmgine.llm.context.memory import SimpleChatHistory
from llmgine.llm.tools import ToolCall
from llmgine.llm.tools.tool_manager import ToolManager
from llmgine.messages.commands import Command, CommandResult
from llmgine.messages.events import Event
from llmgine.ui.cli.cli import EngineCLI
from llmgine.ui.cli.components import EngineResultComponent


@dataclass
class ToolChatEngineCommand(Command):
    """Command for the Tool Chat Engine."""

    prompt: str = ""


@dataclass
class ToolChatEngineStatusEvent(Event):
    """Status event for the Tool Chat Engine."""

    status: str = ""


def get_weather(city: str) -> str:
    """Get the current weather for a given city."""
    # Mock implementation
    return f"The weather in {city} is sunny and 72°F"


def calculate(expression: str) -> str:
    """Calculate a mathematical expression."""
    try:
        result = eval(expression)
        return f"The result of {expression} is {result}"
    except Exception as e:
        return f"Error calculating {expression}: {str(e)}"


async def search_web(query: str) -> str:
    """Search the web for information."""
    # Mock implementation
    await asyncio.sleep(1)  # Simulate network delay
    return f"Search results for '{query}': [Mock results - This would contain actual search results]"


def play_music(song: str, artist: str = "") -> str:
    """Play a song."""
    if artist:
        return f"Now playing '{song}' by {artist}"
    return f"Now playing '{song}'"


class ToolChatEngine:
    """An engine that can chat and use tools."""

    def __init__(self, model: str = "gpt-4o-mini", session_id: str = None):
        self.session_id = SessionID(session_id or str(uuid.uuid4()))
        self.bus = MessageBus()
        self.model = model

        # Initialize chat history
        self.chat_history = SimpleChatHistory()
        self.chat_history.set_system_prompt(
            "You are a helpful assistant with access to various tools. "
            "Use the tools when appropriate to help answer user questions."
        )

        # Initialize tool manager
        self.tool_manager = ToolManager(self.chat_history)

        # Register tools
        self._register_tools()

    def _register_tools(self):
        """Register all available tools."""
        self.tool_manager.register_tool(get_weather)
        self.tool_manager.register_tool(calculate)
        self.tool_manager.register_tool(search_web)
        self.tool_manager.register_tool(play_music)

    async def handle_command(self, command: ToolChatEngineCommand) -> CommandResult:
        """Handle a chat command."""
        try:
            # Publish initial status
            await self.bus.publish(
                ToolChatEngineStatusEvent(status="processing", session_id=self.session_id)
            )

            # 1. Add user message to chat history
            self.chat_history.add_user_message(command.prompt)

            # 2. Get current context and tools
            current_context = self.tool_manager.chat_history_to_messages()
            tools = self.tool_manager.parse_tools_to_list()

            # 3. Call the LLM
            await self.bus.publish(
                ToolChatEngineStatusEvent(
                    status="calling LLM", session_id=self.session_id
                )
            )

            response = await acompletion(
                model=self.model, messages=current_context, tools=tools if tools else None
            )

            # 4. Extract the message from response
            if not response.choices:
                return CommandResult(success=False, error="No response from LLM")

            message = response.choices[0].message

            # 5. Check for tool calls
            if hasattr(message, "tool_calls") and message.tool_calls:
                await self.bus.publish(
                    ToolChatEngineStatusEvent(
                        status="executing tools", session_id=self.session_id
                    )
                )

                # Convert litellm tool calls to our ToolCall format
                tool_calls = [
                    ToolCall(
                        id=tc.id, name=tc.function.name, arguments=tc.function.arguments
                    )
                    for tc in message.tool_calls
                ]

                # Execute tools
                tool_results = await self.tool_manager.execute_tool_calls(tool_calls)

                # Add assistant message with tool calls
                self.chat_history.add_assistant_message(
                    content=message.content or "", tool_calls=tool_calls
                )

                # Add tool results
                for tool_call, result in zip(tool_calls, tool_results):
                    self.chat_history.add_tool_message(
                        tool_call_id=tool_call.id, content=str(result)
                    )

                # Get final response after tool execution
                await self.bus.publish(
                    ToolChatEngineStatusEvent(
                        status="getting final response", session_id=self.session_id
                    )
                )

                final_context = self.tool_manager.chat_history_to_messages()
                final_response = await acompletion(
                    model=self.model, messages=final_context
                )

                if final_response.choices and final_response.choices[0].message.content:
                    final_content = final_response.choices[0].message.content
                    self.chat_history.add_assistant_message(final_content)

                    await self.bus.publish(
                        ToolChatEngineStatusEvent(
                            status="finished", session_id=self.session_id
                        )
                    )
                    return CommandResult(success=True, result=final_content)
            else:
                # No tool calls, just return the response
                content = message.content or ""
                self.chat_history.add_assistant_message(content)

                await self.bus.publish(
                    ToolChatEngineStatusEvent(
                        status="finished", session_id=self.session_id
                    )
                )
                return CommandResult(success=True, result=content)

        except Exception as e:
            await self.bus.publish(
                ToolChatEngineStatusEvent(status="finished", session_id=self.session_id)
            )
            return CommandResult(success=False, error=str(e))


async def main():
    """Main function to run the Tool Chat Engine."""
    from llmgine.bootstrap import ApplicationBootstrap, ApplicationConfig

    config = ApplicationConfig(enable_console_handler=False)
    bootstrap = ApplicationBootstrap(config)
    await bootstrap.bootstrap()

    # Create engine with GPT-4O Mini
    engine = ToolChatEngine(model="gpt-4o-mini")

    # Set up CLI
    cli = EngineCLI(engine.session_id)
    cli.register_engine(engine)
    cli.register_engine_command(ToolChatEngineCommand, engine.handle_command)
    cli.register_engine_result_component(EngineResultComponent)
    cli.register_loading_event(ToolChatEngineStatusEvent)

    # Run the CLI
    await cli.main()


if __name__ == "__main__":
    asyncio.run(main())

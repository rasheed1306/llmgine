"""
Simplified voice processing engine using litellm directly.
"""

import json
import uuid
from dataclasses import dataclass
from typing import Optional, List, Dict, Any

from llmgine.bus.bus import MessageBus
from llmgine.llm import AsyncOrSyncToolFunction, SessionID
from llmgine.llm.context.memory import SimpleChatHistory
from llmgine.llm.engine.engine import Engine
from litellm import acompletion
from llmgine.llm.tools import ToolCall
from llmgine.llm.tools.tool_manager import ToolManager
from llmgine.messages.commands import Command, CommandResult
from llmgine.messages.events import Event


SYSTEM_PROMPT = (
    "You are a voice processing engine. You are provided with the number of speakers inside the conversation, "
    "and a snippet of what each speaker said in the conversation. "
    "The number of speakers present in the snippet will be greater than the actual number of speakers in the conversation. "
    "Your task is to decide which speakers in the snippet should be merged into a single speaker, based on the context, speaking style, "
    "and the content of what they said. Make sure the number of speakers after merge is the same as the actual number of speakers in the conversation. "
    "If you think speaker_1 and speaker_2 are actually one person, speaker_3 and speaker_4 are one person: "
    'example function call: merge_speakers("speaker_1,speaker_2") ; merge_speakers("speaker_3,speaker_4")'
)


@dataclass
class VoiceProcessingEngineCommand(Command):
    prompt: str = ""
    speakers_data: Optional[Dict[str, Any]] = None


@dataclass
class VoiceProcessingEngineStatusEvent(Event):
    status: str = ""


def merge_speakers(speakers: str) -> str:
    """Merge multiple speakers into one."""
    speaker_list = speakers.split(",")
    return f"Merged speakers: {', '.join(speaker_list)}"


class VoiceProcessingEngine(Engine):
    """A simplified voice processing engine using litellm directly."""
    
    def __init__(
        self,
        model: str = "gpt-4o-mini",
        system_prompt: str = SYSTEM_PROMPT,
        session_id: Optional[SessionID] = None,
    ):
        self.session_id = session_id or SessionID(str(uuid.uuid4()))
        self.bus = MessageBus()
        self.model = model
        self.system_prompt = system_prompt
        
        # Initialize chat history
        self.chat_history = SimpleChatHistory()
        
        # Initialize tool manager
        self.tool_manager = ToolManager(self.chat_history)
        
        # Register tools
        self.tool_manager.register_tool(merge_speakers)
    
    async def handle_command(self, command: VoiceProcessingEngineCommand) -> CommandResult:
        """Handle a voice processing command."""
        try:
            # Add system prompt and user message
            messages = [
                {"role": "system", "content": self.system_prompt},
                {"role": "user", "content": command.prompt}
            ]
            
            if command.speakers_data:
                messages.append({
                    "role": "user",
                    "content": f"Speaker data: {json.dumps(command.speakers_data)}"
                })
            
            # Get tools
            tools = self.tool_manager.parse_tools_to_list()
            
            # Publish status
            await self.bus.publish(
                VoiceProcessingEngineStatusEvent(
                    status="calling LLM", session_id=self.session_id
                )
            )
            
            # Generate response
            response = await acompletion(
                model=self.model,
                messages=messages,
                tools=tools if tools else None,
                tool_choice="auto"
            )
            
            # Extract message
            if not response.choices:
                return CommandResult(success=False, error="No response from LLM")
            
            message = response.choices[0].message
            
            # Check for tool calls
            if hasattr(message, 'tool_calls') and message.tool_calls:
                await self.bus.publish(
                    VoiceProcessingEngineStatusEvent(
                        status="executing tools", session_id=self.session_id
                    )
                )
                
                # Convert and execute tool calls
                tool_calls = [
                    ToolCall(
                        id=tc.id,
                        name=tc.function.name,
                        arguments=tc.function.arguments
                    )
                    for tc in message.tool_calls
                ]
                
                tool_results = await self.tool_manager.execute_tool_calls(tool_calls)
                
                # Format results
                result_text = "\n".join([
                    f"Tool: {tc.name}, Result: {result}"
                    for tc, result in zip(tool_calls, tool_results)
                ])
                
                await self.bus.publish(
                    VoiceProcessingEngineStatusEvent(
                        status="completed", session_id=self.session_id
                    )
                )
                
                return CommandResult(success=True, result=result_text)
            else:
                # No tool calls
                content = message.content or ""
                
                await self.bus.publish(
                    VoiceProcessingEngineStatusEvent(
                        status="completed", session_id=self.session_id
                    )
                )
                
                return CommandResult(success=True, result=content)
                
        except Exception as e:
            await self.bus.publish(
                VoiceProcessingEngineStatusEvent(
                    status=f"error: {str(e)}", session_id=self.session_id
                )
            )
            return CommandResult(success=False, error=str(e))


async def main():
    """Example usage of the voice processing engine."""
    from llmgine.bootstrap import ApplicationBootstrap, ApplicationConfig
    
    config = ApplicationConfig(enable_console_handler=False)
    bootstrap = ApplicationBootstrap(config)
    await bootstrap.bootstrap()
    
    # Create engine
    engine = VoiceProcessingEngine(model="gpt-4o-mini")
    
    # Example command
    command = VoiceProcessingEngineCommand(
        prompt="There are 2 actual speakers. Analyze the following transcript.",
        speakers_data={
            "speaker_1": "Hello, how are you?",
            "speaker_2": "I'm doing well, thanks!",
            "speaker_3": "Hi there, how's it going?",
            "speaker_4": "Pretty good, thank you!"
        }
    )
    
    result = await engine.handle_command(command)
    print(f"Result: {result}")


if __name__ == "__main__":
    import asyncio
    asyncio.run(main())
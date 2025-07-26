"""
This engine's job is to receive facts and decides whether to
create, update, or delete a fact.

To create or update a fact, construct the content as follows:
<CREATE_FACT><fact>

To delete a fact, construct the content as follows:
<DELETE_FACT><fact>
"""

import json
import uuid
from dataclasses import dataclass
from typing import Optional

from openai.types.chat.chat_completion_message import ChatCompletionMessage

from llmgine.bus.bus import MessageBus
from llmgine.llm import AsyncOrSyncToolFunction, SessionID
from llmgine.llm.context.memory import SimpleChatHistory
from llmgine.llm.engine.engine import Engine
from llmgine.llm.models.model import Model
from llmgine.llm.models.openai_models import Gpt41Mini, OpenAIResponse
from llmgine.llm.providers.providers import Providers
from llmgine.llm.tools import ToolCall
from llmgine.llm.tools.tool_manager import ToolManager
from llmgine.messages.commands import Command, CommandResult
from llmgine.messages.events import Event
from llmgine.ui.cli.voice_processing_engine_cli import (
    SpecificComponent,
    SpecificComponentEvent,
    SpecificPrompt,
    SpecificPromptCommand,
)
from programs.stt import merge_speakers, merge_speakers_engine, process_audio

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


@dataclass
class VoiceProcessingEngineStatusEvent(Event):
    status: str = ""


@dataclass
class VoiceProcessingEngineToolResultEvent(Event):
    tool_name: str = ""
    result: str = ""


# ------------------------------------ENGINE-------------------------------------------


class VoiceProcessingEngine(Engine):
    def __init__(
        self,
        model: Model,  # TODO This name and class could be more descriptive
        system_prompt: Optional[str] = None,
        session_id: SessionID = SessionID("test"),
    ):
        self.model: Model = model
        self.system_prompt: Optional[str] = system_prompt
        self.session_id: SessionID = SessionID(session_id)
        self.message_bus: MessageBus = MessageBus()
        self.engine_id: str = str(uuid.uuid4())

        # Create tightly coupled components - pass the simple engine
        self.context_manager = SimpleChatHistory(
            engine_id=self.engine_id, session_id=self.session_id
        )
        self.llm_manager = Gpt41Mini(Providers.OPENAI)
        self.tool_manager = ToolManager(
            engine_id=self.engine_id, session_id=self.session_id, llm_model_name="openai"
        )

    async def handle_command(
        self, command: VoiceProcessingEngineCommand
    ) -> CommandResult:
        """Handle a prompt command following OpenAI tool usage pattern.

        Args:
            command: The prompt command to handle

        Returns:
            CommandResult: The result of the command execution
        """
        try:
            # Process the audio file and get the snippet
            audio_file, number_of_speakers = command.prompt.split("&")
            snippet, audio_file_path = process_audio(audio_file, number_of_speakers)
            self.audio_file_path = audio_file_path

            if len(snippet) == int(number_of_speakers):
                return CommandResult(success=True, result="No merge is required.")

            # Prompt the LLM with the actual number of speakers and the snippet
            prompt = (
                "Actual Number of speakers: "
                + number_of_speakers
                + ".\nHere is the snippet of what each speaker said in the conversation: "
                + str(snippet)
            )
            result = await self.execute(prompt=prompt)

            return CommandResult(success=True, result=result)
        except Exception as e:
            return CommandResult(success=False, error=str(e))

    async def execute(self, prompt: str) -> str:
        """This function executes the engine.

        Args:
            prompt: The prompt to execute
        """

        self.context_manager.store_string(prompt, "user")

        while True:
            # Retrieve the current context
            current_context = await self.context_manager.retrieve()
            # Get the tools
            tools = await self.tool_manager.get_tools()
            # Notify status
            await self.message_bus.publish(
                VoiceProcessingEngineStatusEvent(
                    status="calling LLM", session_id=self.session_id
                )
            )
            # Generate the response
            response: OpenAIResponse = await self.llm_manager.generate(
                messages=current_context, tools=tools, tool_choice="auto"
            )
            assert isinstance(response, OpenAIResponse), (
                "response is not an OpenAIResponse"
            )

            # Get the response message
            response_message: ChatCompletionMessage = response.raw.choices[0].message
            assert isinstance(response_message, ChatCompletionMessage), (
                "response_message is not a ChatCompletionMessage"
            )

            # Store the response message
            await self.context_manager.store_assistant_message(response_message)
            # If there are no tool calls, break the loop and return the content
            if not response_message.tool_calls:
                final_content = response_message.content or ""
                # Notify status complete
                await self.message_bus.publish(
                    VoiceProcessingEngineStatusEvent(
                        status="finished", session_id=self.session_id
                    )
                )
                return final_content

            # Else, process tool calls
            for tool_call in response_message.tool_calls:
                tool_call_obj = ToolCall(
                    id=tool_call.id,
                    name=tool_call.function.name,
                    arguments=tool_call.function.arguments,
                )
                try:
                    # Execute the tool
                    await self.message_bus.publish(
                        VoiceProcessingEngineStatusEvent(
                            status="executing tool", session_id=self.session_id
                        )
                    )

                    # Insert audio file path here manually
                    if tool_call.function.name == "merge_speakers":
                        args = json.loads(tool_call.function.arguments)
                        args["audio_file"] = self.audio_file_path
                        tool_call_obj.arguments = json.dumps(args)
                        tool_call_obj.name = "merge_speakers_engine"

                    result = await self.tool_manager.execute_tool_call(tool_call_obj)

                    # Convert result to string if needed for history
                    if isinstance(result, dict):
                        result_str = json.dumps(result)
                    else:
                        result_str = str(result)
                    # Store tool execution result in history
                    self.context_manager.store_tool_call_result(
                        tool_call_id=tool_call_obj.id,
                        name=tool_call_obj.name,
                        content=result_str,
                    )
                    # Publish tool execution event
                    await self.message_bus.publish(
                        VoiceProcessingEngineToolResultEvent(
                            tool_name=tool_call_obj.name,
                            result=result_str,
                            session_id=self.session_id,
                        )
                    )

                except Exception as e:
                    error_msg = f"Error executing tool {tool_call_obj.name}: {e!s}"
                    print(error_msg)  # Debug print
                    # Store error result in history
                    self.context_manager.store_tool_call_result(
                        tool_call_id=tool_call_obj.id,
                        name=tool_call_obj.name,
                        content=error_msg,
                    )

    async def register_tool(self, function: AsyncOrSyncToolFunction):
        """Register a function as a tool.

        Args:
            function: The function to register as a tool
        """
        await self.tool_manager.register_tool(function)


async def main():
    from llmgine.bootstrap import ApplicationBootstrap, ApplicationConfig
    from llmgine.llm.models.openai_models import Gpt41Mini
    from llmgine.llm.providers.providers import Providers
    from llmgine.ui.cli.components import EngineResultComponent, ToolComponent
    from llmgine.ui.cli.voice_processing_engine_cli import VoiceProcessingEngineCLI

    config = ApplicationConfig(enable_console_handler=False)
    bootstrap = ApplicationBootstrap(config)
    await bootstrap.bootstrap()

    # Initialize the engine
    engine = VoiceProcessingEngine(
        model=Gpt41Mini(Providers.OPENAI),
        system_prompt=SYSTEM_PROMPT,
        session_id=SessionID("test"),
    )

    # Register cli components
    cli = VoiceProcessingEngineCLI("voice processing engine")
    cli.register_engine(engine)
    cli.register_engine_command(VoiceProcessingEngineCommand, engine.handle_command)
    cli.register_engine_result_component(EngineResultComponent)
    cli.register_loading_event(VoiceProcessingEngineStatusEvent)
    cli.register_component_event(VoiceProcessingEngineToolResultEvent, ToolComponent)
    cli.register_prompt_command(SpecificPromptCommand, SpecificPrompt)
    cli.register_component_event(SpecificComponentEvent, SpecificComponent)

    # Register tools
    await engine.register_tool(merge_speakers)
    await engine.register_tool(merge_speakers_engine)

    await cli.main()


if __name__ == "__main__":
    import asyncio

    asyncio.run(main())

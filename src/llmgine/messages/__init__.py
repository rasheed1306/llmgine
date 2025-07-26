"""Message types for the LLMgine system."""

from llmgine.messages.approvals import ApprovalCommand, ApprovalResult
from llmgine.messages.commands import Command, CommandResult
from llmgine.messages.events import Event
from llmgine.messages.scheduled_events import (
    EVENT_CLASSES,
    ScheduledEvent,
    register_scheduled_event_class,
)

__all__ = [
    "EVENT_CLASSES",
    "ApprovalCommand",
    "ApprovalResult",
    "Command",
    "CommandResult",
    "Event",
    "ScheduledEvent",
    "register_scheduled_event_class",
]

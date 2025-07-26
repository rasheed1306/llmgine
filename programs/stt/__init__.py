"""Audio to text tools.

This module provides tools that can be called by language models.
"""

from programs.stt.functions import merge_speakers, merge_speakers_engine, process_audio

__all__ = [
    "merge_speakers",
    "merge_speakers_engine",
    "process_audio",
]

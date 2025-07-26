import datetime
import json
import os
from collections import defaultdict as dd
from typing import Any, Dict, List, Optional, Set, Tuple

import dotenv
import requests

dotenv.load_dotenv()

filler_words = {
    "",
    "huh",
    "well",
    "um",
    "hm",
    "hmm",
    "(cough)",
    "(coughing)",
    "(laughing)",
    "that's",
    "oh",
    "mm-mm",
    "(whispering)",
    "(laughs)",
    "mm-hmm",
    "sorry",
    "uh-huh",
    "(coughs)",
    "yeah",
    "so",
}


def post(
    url: str,
    data: Optional[Dict[str, Any]] = None,
    headers: Optional[Dict[str, str]] = None,
    files: Optional[Dict[str, Any]] = None,
) -> Optional[requests.Response]:
    """
    Send a POST request to the specified URL

    Args:
        url (str): The URL to send the request to
        data (dict, optional): The data to send in the request body
        headers (dict, optional): The headers to include in the request
        files (dict, optional): Files to upload in the request

    Returns:
        requests.Response: The response from the server
    """
    try:
        response = requests.post(url, data=data, headers=headers, files=files)
        response.raise_for_status()  # Raises an HTTPError for bad responses (4xx, 5xx)
        return response
    except requests.exceptions.RequestException as e:
        print(f"An error occurred: {e}")
        return None


# Transcribe
def transcribe(audio_file: str, num_speakers: int) -> Dict[str, Any]:
    ELEVENLABS_API_KEY = os.getenv("ELEVENLABS_API_KEY")
    if not ELEVENLABS_API_KEY:
        raise ValueError("ELEVENLABS_API_KEY not found in environment variables")

    MODEL_ID = "scribe_v1"

    # Open the file in binary mode
    with open(audio_file, "rb") as f:
        files = {"file": ("audio.m4a", f, "audio/mp4")}
        data = {
            "model_id": MODEL_ID,
            "num_speakers": num_speakers,
            "diarize": True,
        }

        res = post(
            url="https://api.elevenlabs.io/v1/speech-to-text",
            data=data,
            headers={"xi-api-key": ELEVENLABS_API_KEY},
            files=files,
        )

    if res is None:
        raise Exception("Failed to get response from ElevenLabs API")
    return res.json()


def process_transcription(result: Dict[str, Any]) -> List[Dict[str, Any]]:
    result_words: List[Dict[str, Any]] = result["words"]

    conversation: List[Dict[str, Any]] = []

    current_speaker = None
    current_sentence = ""
    for word_dict in result_words:
        word = word_dict["text"]
        speaker = word_dict["speaker_id"]

        if speaker != current_speaker:
            if current_speaker is not None:
                conversation.append({
                    "speaker": current_speaker,
                    "sentence": current_sentence,
                })

            current_speaker = speaker
            current_sentence = word
        else:
            current_sentence += word

    # Add the last sentence to the conversation
    if current_speaker is not None:
        conversation.append({"speaker": current_speaker, "sentence": current_sentence})

    return conversation


def find_filler_words(file_path: str) -> Set[str]:
    with open(file_path, "r") as f:
        conversation = json.load(f)

    filler_words: Set[str] = set()
    for sentence in conversation:
        words = sentence["sentence"].split(" ")
        if len(words) <= 2:
            filler_words.update(words)

    return filler_words


def cleanup_conversation(conversation: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    for sentence in conversation:
        current_sentence = sentence["sentence"]
        if all(
            word.lower().strip(".,!?:;-") in filler_words
            for word in current_sentence.split(" ")
        ):
            conversation.remove(sentence)

    i, j = 0, 0
    while i <= len(conversation) - 1:
        while (
            j < len(conversation) - 1
            and conversation[j]["speaker"] == conversation[j + 1]["speaker"]
        ):
            conversation[j]["sentence"] = (
                conversation[j]["sentence"] + " " + conversation[j + 1]["sentence"]
            )
            conversation.pop(j + 1)
        j += 1
        i += 1

    return conversation


def get_conversation_snippet(conversation: List[Dict[str, Any]]) -> Dict[str, List[str]]:
    """
    Get a snippet of the conversation for each speaker.
    For LLM reference.
    """

    # key: speaker, value: list of sentences the speaker has spoken
    snippet: Dict[str, List[str]] = dd(list)
    for sentence in conversation:
        # Ignore sentences that are too short
        if len(sentence["sentence"]) < 10:
            continue

        if len(snippet[sentence["speaker"]]) < 20:
            snippet[sentence["speaker"]].append(sentence["sentence"])

    return snippet


def build_file_name(num: int, audio_file: str, step: str, time: bool = True) -> str:
    if time:
        return (
            "/"
            + str(num)
            + "_"
            + audio_file.split(".")[0]
            + "_"
            + step
            + "_"
            + datetime.datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
            + ".json"
        )
    else:
        return "/" + str(num) + "_" + audio_file.split(".")[0] + "_" + step + ".json"


def process_audio(audio_file: str, num_speakers: str) -> Tuple[Dict[str, List[str]], str]:
    """
    Process the audio file and return the conversation.

    Args:
        audio_file: The path to the audio file
        num_speakers: The number of speakers in the audio file

    Returns:
        Tuple[str, str]: The conversation and the path to the audio file
    """

    if not num_speakers.isdigit():
        return {}, "num_speakers must be an integer"

    num_speakers_int = int(num_speakers)

    # 1. Get the directory where the script is located
    script_dir = os.path.dirname(os.path.abspath(__file__))
    # Construct the path to the audio file
    audio_file_path = os.path.join(script_dir, "audio", audio_file)
    transcribed_file_dir = os.path.join(script_dir, "transcribed_audio")

    # Create a new directory inside the transcribed_audio directory
    new_dir = os.path.join(
        transcribed_file_dir,
        audio_file.split(".")[0]
        + "_"
        + datetime.datetime.now().strftime("%Y-%m-%d_%H-%M-%S"),
    )
    os.makedirs(new_dir, exist_ok=True)

    # Check if the file exists
    if not os.path.exists(audio_file_path):
        return (
            {},
            f"Audio file not found at: {audio_file_path}. Make sure the file is in the audio folder.",
        )

    # ----------------------------------------
    # 2. Get the transcription and write it to a file
    # ----------------------------------------
    # Check if the transcription file exists
    if os.path.exists(
        transcribed_file_dir + "/" + audio_file.split(".")[0] + "_raw_transcript.json"
    ):
        with open(
            transcribed_file_dir
            + "/"
            + audio_file.split(".")[0]
            + "_raw_transcript.json",
            "r",
        ) as f:
            result = json.load(f)
    else:
        return {}, "Transcription file not found"
        result: Dict[str, Any] = transcribe(audio_file_path, num_speakers_int)

    with open(new_dir + build_file_name(1, audio_file, "raw_transcript"), "w") as f:
        json.dump(result, f, indent=2)

    # ----------------------------------------
    # 3. Process the transcription into a conversational format
    # ----------------------------------------
    conversation: List[Dict[str, Any]] = process_transcription(result)

    with open(new_dir + build_file_name(2, audio_file, "raw_conversation"), "w") as f:
        json.dump(conversation, f, indent=2)

    # ----------------------------------------
    # 4. Cleanup the conversation (remove filler words, merge sentences from the same speaker)
    # ----------------------------------------
    cleaned_conversation = cleanup_conversation(conversation)

    # To be returned later
    audio_file_path = new_dir + build_file_name(3, audio_file, "parsed_conversation")
    with open(audio_file_path, "w") as f:
        json.dump(cleaned_conversation, f, indent=2)

    # ----------------------------------------
    # 5. Get a snippet of the conversation for each speaker
    # ----------------------------------------
    snippet = get_conversation_snippet(cleaned_conversation)
    with open(new_dir + build_file_name(4, audio_file, "speaker_snippet"), "w") as f:
        json.dump(snippet, f, indent=2)

    return snippet, audio_file_path


def merge_speakers(speakers_to_merge: str) -> str:
    """
    Merge two speakers in the conversation. They may be the same speaker.

    Args:
        speakers_to_merge: A list of the ids of the speakers to merge, separated by commas.

    Returns:
        str: Result of the merge
    """

    return ""


def merge_speakers_engine(audio_file: str, speakers_to_merge: str) -> str:
    """
    Merge two speakers in the conversation. They may be the same speaker.
    Do not call this function directly.

    Args:
        audio_file: The path to the audio file (hidden from the llm)
        speakers_to_merge: A list of the ids of the speakers to merge, separated by commas.

    Returns:
        str: Result of the merge
    """
    speakers_to_merge_list = speakers_to_merge.split(",")

    if len(speakers_to_merge_list) == 1:
        return "No merge is required for " + str(speakers_to_merge_list[0]) + "\n"

    # Load the conversation
    script_dir = os.path.dirname(os.path.abspath(__file__))
    # Construct the path to the audio file
    audio_file_path = os.path.join(script_dir, "transcribed_audio", audio_file)
    with open(audio_file_path, "r") as f:
        conversation = json.load(f)

    # Create a dictionary to store the merged speakers
    merged_speakers: Dict[str, str] = {}
    for speaker in speakers_to_merge_list:
        merged_speakers[speaker] = speakers_to_merge_list[0]

    for message in conversation:
        if message["speaker"] in merged_speakers:
            message["speaker"] = merged_speakers[message["speaker"]]

    # Write the merged conversation to a new file
    new_file_path = audio_file_path.split(".")[0] + "_merged.json"
    with open(new_file_path, "w") as f:
        json.dump(conversation, f, indent=2)

    return (
        "Merged: "
        + str(speakers_to_merge_list[1:])
        + " into "
        + str(speakers_to_merge_list[0])
        + "\n"
    )


# print(merge_speakers_engine("KFC_2025-05-18_11-49-18/3_KFC_parsed_conversation_2025-05-18_11-49-18.json", 'speaker_1,speaker_2'))
# print(process_audio("KFC.m4a", "2"))

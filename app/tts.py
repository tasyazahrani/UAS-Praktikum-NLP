import os
import uuid
import subprocess

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

COQUI_DIR = os.path.join(BASE_DIR, "coqui_utils")
COQUI_MODEL_PATH = os.path.join(COQUI_DIR, "checkpoint_1260000-inference.pth")
COQUI_CONFIG_PATH = os.path.join(COQUI_DIR, "config.json")
COQUI_SPEAKERS_PATH = os.path.join(COQUI_DIR, "speakers.pth")
COQUI_SPEAKER = "wibowo"

# ✅ Folder khusus output TTS — terpisah dari corpus
AUDIO_OUTPUT_DIR = os.path.join(BASE_DIR, "data", "corpus", "tts_output")


def transcribe_text_to_speech(text: str) -> str:
    path = _tts_with_coqui(text)
    return path


def _tts_with_coqui(text: str) -> str:
    os.makedirs(AUDIO_OUTPUT_DIR, exist_ok=True)

    output_path = os.path.join(AUDIO_OUTPUT_DIR, f"tts_{uuid.uuid4().hex[:8]}.wav")

    cmd = [
        "tts",
        "--text", text,
        "--model_path", COQUI_MODEL_PATH,
        "--config_path", COQUI_CONFIG_PATH,
        "--speakers_file", COQUI_SPEAKERS_PATH,
        "--speaker_idx", COQUI_SPEAKER,
        "--out_path", output_path
    ]

    try:
        subprocess.run(
            cmd,
            check=True,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL
        )
    except subprocess.CalledProcessError as e:
        print(f"[ERROR] TTS subprocess failed: {e}")
        return "[ERROR] Failed to synthesize speech"

    return output_path
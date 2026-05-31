import os
import uuid
import shutil
import tempfile
import subprocess

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

WHISPER_DIR = os.path.join(BASE_DIR, "whisper.cpp")
WHISPER_BINARY = os.path.join(WHISPER_DIR, "build", "bin", "whisper-cli.exe")
WHISPER_MODEL_PATH = os.path.join(WHISPER_DIR, "models", "ggml-small.bin")

def transcribe_speech_to_text(file_bytes: bytes, file_ext: str = ".wav") -> str:
    tmpdir = tempfile.mkdtemp()
    try:
        audio_path = os.path.join(tmpdir, f"{uuid.uuid4()}{file_ext}")
        output_base = os.path.join(tmpdir, "transcription")
        result_path = output_base + ".txt"

        with open(audio_path, "wb") as f:
            f.write(file_bytes)

        cmd = [
            WHISPER_BINARY,
            "-m", WHISPER_MODEL_PATH,
            "-f", audio_path,
            "-l", "auto",    # auto-detect bahasa (Indonesia, Inggris, Arab)
            "-otxt",
            "-of", output_base
        ]

        try:
            subprocess.run(
                cmd,
                check=True,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL
            )
        except subprocess.CalledProcessError as e:
            return f"[ERROR] Whisper failed: {e}"

        try:
            with open(result_path, "r", encoding="utf-8") as result_file:
                return result_file.read().strip()
        except FileNotFoundError:
            parent_result = os.path.join(os.path.dirname(tmpdir), "transcription.txt")
            if os.path.exists(parent_result):
                with open(parent_result, "r", encoding="utf-8") as f:
                    return f.read().strip()
            return "[ERROR] Transcription file not found"
    finally:
        shutil.rmtree(tmpdir, ignore_errors=True)
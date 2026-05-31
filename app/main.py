import os
from fastapi import FastAPI, UploadFile, File
from fastapi.responses import FileResponse

from app.stt import transcribe_speech_to_text
from app.llm import generate_response
from app.tts import transcribe_text_to_speech

app = FastAPI()

@app.post("/voice-chat")
async def voice_chat(file: UploadFile = File(...)):
    file_bytes = await file.read()
    file_ext = os.path.splitext(file.filename)[-1] or ".wav"

    transcribed_text = transcribe_speech_to_text(file_bytes, file_ext)
    print(f"[STT] Transkripsi: {transcribed_text}")

    response_text = generate_response(transcribed_text)
    print(f"[LLM] Respons: {response_text}")

    audio_path = transcribe_text_to_speech(response_text)
    print(f"[TTS] Audio: {audio_path}")

    return FileResponse(
        path=audio_path,
        media_type="audio/wav",
        filename="response.wav"
    )

@app.get("/")
def root():
    return {"status": "Voice Chatbot API is running!"}
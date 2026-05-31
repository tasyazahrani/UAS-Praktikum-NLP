import os
import tempfile
import requests
import gradio as gr
import scipy.io.wavfile
import numpy as np

BACKEND_URL = "http://localhost:8000/voice-chat"

def voice_chat(audio_mic, audio_upload):
    # Prioritaskan upload, kalau tidak ada pakai mikrofon
    audio = audio_upload if audio_upload is not None else audio_mic

    if audio is None:
        return None, "❌ Tidak ada audio yang direkam atau diupload."

    sr, audio_data = audio

    # Pastikan format audio benar
    if audio_data.dtype != np.int16:
        audio_data = (audio_data * 32767).astype(np.int16)

    # Simpan sebagai .wav sementara
    with tempfile.NamedTemporaryFile(delete=False, suffix=".wav") as tmpfile:
        scipy.io.wavfile.write(tmpfile.name, sr, audio_data)
        audio_path = tmpfile.name

    try:
        # Kirim ke backend FastAPI
        with open(audio_path, "rb") as f:
            files = {"file": ("voice.wav", f, "audio/wav")}
            response = requests.post(BACKEND_URL, files=files, timeout=300)

        if response.status_code == 200:
            output_audio_path = os.path.join(tempfile.gettempdir(), "tts_output.wav")
            with open(output_audio_path, "wb") as f:
                f.write(response.content)
            return output_audio_path, "✅ Respons berhasil diterima!"
        else:
            return None, f"❌ Error dari server: {response.status_code} - {response.text}"

    except requests.exceptions.ConnectionError:
        return None, "❌ Backend tidak berjalan! Jalankan uvicorn dulu."
    except requests.exceptions.Timeout:
        return None, "❌ Timeout! Server terlalu lama merespons."
    except Exception as e:
        return None, f"❌ Error: {str(e)}"
    finally:
        if os.path.exists(audio_path):
            os.remove(audio_path)

# UI Gradio
with gr.Blocks(title="Voice Chatbot NLP") as demo:
    gr.Markdown("# 🎙️ Voice Chatbot — Code-Switching ID/EN/AR")
    gr.Markdown("Rekam atau upload audio dalam **Bahasa Indonesia, English, atau Arabic** dan dapatkan balasan suara dari asisten AI.")

    with gr.Row():
        with gr.Column():
            gr.Markdown("### 🎤 Rekam Suara")
            audio_mic = gr.Audio(
                sources="microphone",
                type="numpy",
                label="Rekam dari Mikrofon"
            )

            gr.Markdown("### 📁 Upload Audio")
            audio_upload = gr.Audio(
                sources="upload",
                type="numpy",
                label="Upload File Audio (.wav, .mp3)"
            )

            submit_btn = gr.Button("🔁 Kirim ke Asisten", variant="primary")

        with gr.Column():
            audio_output = gr.Audio(
                type="filepath",
                label="🔊 Balasan dari Asisten"
            )
            status_text = gr.Textbox(
                label="📋 Status",
                interactive=False
            )

    submit_btn.click(
        fn=voice_chat,
        inputs=[audio_mic, audio_upload],
        outputs=[audio_output, status_text]
    )

    gr.Markdown("---")
    gr.Markdown("💡 **Tips:** Pastikan backend sudah berjalan di `http://localhost:8000` sebelum menggunakan aplikasi ini.")

demo.launch(share=False)
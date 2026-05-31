# 🎙️ Voice Chatbot — Code-Switching Speech-to-Speech System

Sistem chatbot berbasis suara yang mendukung **code-switching** antara Bahasa Indonesia, English, dan Arabic. Dibangun sebagai proyek UAS Praktikum Natural Language Processing (NLP) 2025/2026 — Universitas Syiah Kuala.

## 📋 Deskripsi

Sistem ini membangun pipeline **Speech-to-Speech end-to-end** yang:
1. Menerima input suara dari pengguna
2. Mentranskripsi suara ke teks menggunakan **Whisper**
3. Menghasilkan respons menggunakan **Google Gemini API**
4. Mengubah respons teks kembali menjadi suara menggunakan **Coqui TTS**

## 🏗️ Arsitektur Pipeline

```
Audio Input → [STT: Whisper] → Teks → [LLM: Gemini] → Respons → [TTS: Coqui] → Audio Output
```

## 🛠️ Teknologi yang Digunakan

| Komponen | Teknologi |
|----------|-----------|
| Speech-to-Text (STT) | Whisper.cpp (ggml-small) |
| Large Language Model | Google Gemini API |
| Text-to-Speech (TTS) | Coqui TTS + Indonesian-TTS VITS |
| Backend | FastAPI |
| Frontend | Gradio |

## 📁 Struktur Proyek

```
UAS-PRAKTIKUM-PEMROSESAN-BAHASA-ALAMI/
├── app/
│   ├── __pycache__/
│   ├── coqui_utils/         # Model TTS (tidak di-push ke GitHub)
│   │   ├── checkpoint_1260000-inference.pth
│   │   ├── config.json
│   │   └── speakers.pth
│   ├── data/               # Hasil TTS
│   │   ├── corpus
│   │   └── tts_output
│   ├── whisper.cpp/         # Whisper binary & model (tidak di-push)
│   ├── chat_history.json
│   ├── llm.py               # LLM dengan Gemini API
│   ├── main.py              # FastAPI endpoint utama
│   ├── stt.py               # Speech-to-Text dengan Whisper
│   └── tts.py               # Text-to-Speech dengan Coqui
├── data/                    # Corpus audio
│   ├── corpus
│   └── audio
├── env/                     # Virtual environment (tidak di-push)
├── gradio_app/
│   └── app.py               # Frontend Gradio
├── log/                     # Log hasil pipeline
├── .env                     # API Key (tidak di-push)
├── .gitignore
├── analisis_hasil.py        # Analisis hasil pipeline
├── analisis_pipline.py      # Pipeline analisis seluruh corpus
├── evaluasi_wer_cer.py      # Evaluasi WER & CER
├── README.md
└── requirements.txt
```

## ⚙️ Cara Setup

### 1. Clone Repository

```bash
git clone https://github.com/tasyazahrani/UAS-Praktikum-NLP.git
cd UAS-Praktikum-NLP
```

### 2. Buat Virtual Environment

```bash
python -m venv env

# Windows
env\Scripts\activate

# Linux/macOS
source env/bin/activate
```

### 3. Install Dependensi

```bash
pip install -r requirements.txt
pip install -U google-genai
pip install coqui-tts
pip install torch torchaudio --index-url https://download.pytorch.org/whl/cpu
```

### 4. Setup Whisper.cpp

```bash
cd app
git clone https://github.com/ggml-org/whisper.cpp.git
cd whisper.cpp

# Build (Windows dengan MinGW)
cmake -B build -G "MinGW Makefiles" -DCMAKE_BUILD_TYPE=Release
cmake --build build --config Release

# Download model (gunakan Git Bash)
bash models/download-ggml-model.sh small
```

### 5. Download Model Coqui TTS

Download 3 file berikut dari [Indonesian-TTS v1.2](https://github.com/Wikidepia/indonesian-tts/releases/tag/v1.2):
- `checkpoint_1260000-inference.pth`
- `config.json`
- `speakers.pth`

Taruh di folder `app/coqui_utils/`

### 6. Setup API Key Gemini

Buat API key di [Google AI Studio](https://aistudio.google.com/apikey), lalu buat file `.env` di root project:

```
GEMINI_API_KEY=your_api_key_here
GEMINI_API_KEY_2=your_second_api_key
GEMINI_API_KEY_3=your_third_api_key
```

> Lihat `.env.example` untuk format lengkapnya.

## 🚀 Cara Menjalankan

### Backend

```bash
python -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

### Frontend (Gradio)

```bash
cd gradio_app
python app.py
```

Buka browser: **http://127.0.0.1:7860**

### Pipeline Analisis Corpus

```bash
python analisis_pipline.py
```

> Pipeline mendukung **resume mode** — kalau berhenti di tengah, jalankan lagi dan otomatis lanjut dari audio yang belum diproses.

## 🎯 Fitur Sistem

- ✅ **Code-switching** — mendukung mix bahasa Indonesia, English, Arab
- ✅ **Auto language detection** — Whisper otomatis deteksi bahasa
- ✅ **Resume mode** — pipeline tidak mengulang audio yang sudah diproses
- ✅ **Auto retry** — otomatis retry kalau kena rate limit atau server busy
- ✅ **Multi API key** — rotasi key untuk menghindari quota limit
- ✅ **Upload audio** — bisa upload file atau rekam langsung di Gradio

## 📊 Evaluasi

| Metrik | Keterangan |
|--------|------------|
| WER/CER | Word/Character Error Rate untuk STT |
| LLM Quality | Kualitas respons berdasarkan penilaian manual |
| TTS Naturalness | Penilaian subjektif kualitas suara |
| Latency | Waktu total end-to-end pipeline |

Hasil lengkap tersimpan di `log/hasil_pipeline.json`

## ⚠️ Catatan Penting

- File model (`*.bin`, `*.pth`) tidak disertakan di repo karena ukurannya besar — download manual sesuai panduan di atas
- Jangan commit file `.env` ke GitHub
- Gunakan Python **3.10** untuk kompatibilitas terbaik
- TTS membutuhkan waktu ~1-2 menit per audio karena berjalan di CPU

## 👨‍💻 Informasi

**Mata Kuliah:** Praktikum Natural Language Processing 2025/2026  
**Program Studi:** Informatika  
**Universitas:** Universitas Syiah Kuala
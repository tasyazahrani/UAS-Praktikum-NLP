import os
import sys
import json
import time
import re

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.stt import transcribe_speech_to_text
from app.llm import generate_response
from app.tts import transcribe_text_to_speech

AUDIO_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data", "corpus", "audio")
LOG_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "log")
os.makedirs(LOG_DIR, exist_ok=True)
LOG_FILE = os.path.join(LOG_DIR, "hasil_pipeline.json")

# Delay antar request untuk mencegah rate limit
DELAY_BETWEEN_REQUESTS = 8

def load_existing_results():
    """Load hasil yang sudah ada agar bisa resume kalau berhenti"""
    if os.path.exists(LOG_FILE):
        with open(LOG_FILE, "r", encoding="utf-8") as f:
            try:
                return json.load(f)
            except:
                return []
    return []

def is_berhasil(r):
    """Cek apakah satu entry pipeline berhasil penuh"""
    return (
        r.get("llm") and not str(r.get("llm", "")).startswith("[ERROR]") and
        r.get("tts") and not str(r.get("tts", "")).startswith("[SKIP]") and
        not r.get("error")
    )

def get_processed_files(results):
    """Hanya skip yang BERHASIL — yang error akan diproses ulang"""
    return {r["file"] for r in results if is_berhasil(r)}

def process_audio(audio_path: str) -> dict:
    filename = os.path.basename(audio_path)
    print(f"\n{'='*50}")
    print(f"[PROSES] {filename}")
    result = {
        "file": filename,
        "stt": None,
        "llm": None,
        "tts": None,
        "latency_stt": None,
        "latency_llm": None,
        "latency_tts": None,
        "error": None
    }

    try:
        with open(audio_path, "rb") as f:
            file_bytes = f.read()

        # STT
        print(f"  [STT] Transkripsi...")
        t0 = time.time()
        transcription = transcribe_speech_to_text(file_bytes, ".wav")
        result["latency_stt"] = round(time.time() - t0, 2)
        result["stt"] = transcription
        print(f"  [STT] Hasil: {transcription}")
        print(f"  [STT] Waktu: {result['latency_stt']}s")

        # Jeda mencegah rate limit
        time.sleep(DELAY_BETWEEN_REQUESTS)

        # LLM dengan auto retry
        print(f"  [LLM] Generate respons...")
        t1 = time.time()
        response = generate_response_with_retry(transcription)
        result["latency_llm"] = round(time.time() - t1, 2)
        result["llm"] = response
        print(f"  [LLM] Respons: {response}")
        print(f"  [LLM] Waktu: {result['latency_llm']}s")

        # Skip TTS kalau LLM error
        if response.startswith("[ERROR]"):
            print(f"  [TTS] Skip karena LLM error!")
            result["tts"] = "[SKIP] LLM error"
            result["latency_tts"] = 0
            return result

        # TTS
        print(f"  [TTS] Sintesis suara...")
        t2 = time.time()
        audio_out = transcribe_text_to_speech(response)
        result["latency_tts"] = round(time.time() - t2, 2)
        result["tts"] = audio_out
        print(f"  [TTS] Output: {audio_out}")
        print(f"  [TTS] Waktu: {result['latency_tts']}s")

    except Exception as e:
        result["error"] = str(e)
        print(f"  [ERROR] {e}")

    return result

def generate_response_with_retry(prompt: str, max_retries: int = 5) -> str:
    """Generate respons dengan auto retry kalau kena rate limit"""
    for attempt in range(max_retries):
        response = generate_response(prompt)

        if not response.startswith("[ERROR]"):
            return response

        if "429" in response:
            match = re.search(r'retry in (\d+)', response)
            wait_time = int(match.group(1)) + 10 if match else 60
            print(f"  [LLM] Rate limit! Tunggu {wait_time}s... (attempt {attempt+1}/{max_retries})")
            time.sleep(wait_time)
        else:
            return response

    return "[ERROR] Max retries exceeded"

def main():
    audio_files = sorted([
        os.path.join(AUDIO_DIR, f)
        for f in os.listdir(AUDIO_DIR)
        if f.endswith(".wav")
    ])

    print(f"Total audio ditemukan: {len(audio_files)}")

    # Load hasil yang sudah ada (resume mode)
    all_results = load_existing_results()

    # ✅ FIX: Hapus entry yang error dari results supaya diproses ulang
    results = [r for r in all_results if is_berhasil(r)]
    error_count = len(all_results) - len(results)

    if error_count > 0:
        print(f"⚠️  {error_count} entry error ditemukan — akan diproses ulang")

    # Hanya skip yang berhasil
    processed_files = get_processed_files(results)

    # Filter audio yang belum diproses / yang error
    remaining = [f for f in audio_files if os.path.basename(f) not in processed_files]
    print(f"Sudah berhasil sebelumnya: {len(processed_files)}")
    print(f"Sisa yang akan diproses  : {len(remaining)}")

    for i, audio_path in enumerate(remaining):
        result = process_audio(audio_path)
        results.append(result)

        # Simpan log setiap selesai 1 file
        with open(LOG_FILE, "w", encoding="utf-8") as f:
            json.dump(results, f, ensure_ascii=False, indent=2)

        print(f"  [PROGRESS] {len(processed_files) + i + 1}/{len(audio_files)} selesai")

    print(f"\n{'='*50}")
    print(f"Pipeline selesai! Total diproses: {len(results)} audio")
    print(f"Log tersimpan di: {LOG_FILE}")

    # Ringkasan akhir
    sukses = sum(1 for r in results if is_berhasil(r))
    gagal = len(results) - sukses
    print(f"\n=== RINGKASAN ===")
    print(f"✅ Berhasil: {sukses}")
    print(f"❌ Gagal/Error: {gagal}")
    print(f"📊 Total: {len(results)}")
    print()
    for r in results:
        status = "✅" if is_berhasil(r) else "❌"
        print(f"{status} {r['file']}")
        if r['stt']:
            print(f"   STT: {r['stt'][:60]}...")
        if r['llm']:
            print(f"   LLM: {r['llm'][:60]}...")
        print(f"   Latency: STT={r['latency_stt']}s | LLM={r['latency_llm']}s | TTS={r['latency_tts']}s")

if __name__ == "__main__":
    main()
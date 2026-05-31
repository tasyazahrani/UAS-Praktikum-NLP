import json
import os
from collections import defaultdict

LOG_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "log", "hasil_pipeline.json")

def main():
    if not os.path.exists(LOG_FILE):
        print(f"[ERROR] File log tidak ditemukan: {LOG_FILE}")
        return

    with open(LOG_FILE, "r", encoding="utf-8") as f:
        results = json.load(f)

    total = len(results)

    # ── Hitung status ──────────────────────────────────────────
    stt_berhasil  = sum(1 for r in results if r.get("stt") and not str(r.get("stt","")).startswith("[ERROR]"))
    llm_berhasil  = sum(1 for r in results if r.get("llm") and not str(r.get("llm","")).startswith("[ERROR]"))
    tts_berhasil  = sum(1 for r in results if r.get("tts") and not str(r.get("tts","")).startswith(("[ERROR]", "[SKIP]")))
    pipeline_full = sum(1 for r in results if
                        r.get("stt") and not str(r.get("stt","")).startswith("[ERROR]") and
                        r.get("llm") and not str(r.get("llm","")).startswith("[ERROR]") and
                        r.get("tts") and not str(r.get("tts","")).startswith(("[ERROR]", "[SKIP]")))

    # ── Latency ───────────────────────────────────────────────
    lat_stt = [r["latency_stt"] for r in results if r.get("latency_stt")]
    lat_llm = [r["latency_llm"] for r in results if r.get("latency_llm")]
    lat_tts = [r["latency_tts"] for r in results if r.get("latency_tts") and r.get("latency_tts", 0) > 0]

    def avg(lst): return sum(lst) / len(lst) if lst else 0
    def mn(lst):  return min(lst) if lst else 0
    def mx(lst):  return max(lst) if lst else 0

    # ── Error breakdown ────────────────────────────────────────
    llm_errors = defaultdict(int)
    for r in results:
        llm = r.get("llm", "") or ""
        if llm.startswith("[ERROR]"):
            if "429" in llm:
                llm_errors["Rate Limit (429)"] += 1
            elif "403" in llm:
                llm_errors["Permission Denied (403)"] += 1
            elif "400" in llm:
                llm_errors["Invalid Argument (400)"] += 1
            else:
                llm_errors["Error lain"] += 1

    # ── Print laporan ──────────────────────────────────────────
    print("=" * 60)
    print("ANALISIS HASIL PIPELINE")
    print("=" * 60)

    print(f"\n📊 RINGKASAN TOTAL")
    print(f"   Total audio diproses : {total}")
    print(f"   Pipeline lengkap     : {pipeline_full} ({pipeline_full/total*100:.1f}%)")

    print(f"\n🎙️  STT")
    print(f"   Berhasil : {stt_berhasil}/{total} ({stt_berhasil/total*100:.1f}%)")
    print(f"   Gagal    : {total - stt_berhasil}/{total}")
    print(f"   Latency  → avg: {avg(lat_stt):.2f}s | min: {mn(lat_stt):.2f}s | max: {mx(lat_stt):.2f}s")

    print(f"\n🤖 LLM")
    print(f"   Berhasil : {llm_berhasil}/{total} ({llm_berhasil/total*100:.1f}%)")
    print(f"   Gagal    : {total - llm_berhasil}/{total}")
    print(f"   Latency  → avg: {avg(lat_llm):.2f}s | min: {mn(lat_llm):.2f}s | max: {mx(lat_llm):.2f}s")
    if llm_errors:
        print(f"   Error breakdown:")
        for k, v in llm_errors.items():
            print(f"     - {k}: {v} kasus")

    print(f"\n🔊 TTS")
    print(f"   Berhasil : {tts_berhasil}/{total} ({tts_berhasil/total*100:.1f}%)")
    print(f"   Skip     : {sum(1 for r in results if str(r.get('tts','')).startswith('[SKIP]'))}")
    print(f"   Latency  → avg: {avg(lat_tts):.2f}s | min: {mn(lat_tts):.2f}s | max: {mx(lat_tts):.2f}s")

    total_lat = [
        (r.get("latency_stt") or 0) + (r.get("latency_llm") or 0) + (r.get("latency_tts") or 0)
        for r in results
        if r.get("latency_stt") and r.get("latency_llm") and r.get("latency_tts")
    ]
    print(f"\n⏱️  END-TO-END LATENCY")
    print(f"   avg: {avg(total_lat):.2f}s | min: {mn(total_lat):.2f}s | max: {mx(total_lat):.2f}s")

    print(f"\n❌ FILE YANG GAGAL")
    gagal = [r for r in results if r.get("error") or str(r.get("llm","")).startswith("[ERROR]")]
    if gagal:
        for r in gagal:
            print(f"   - {r['file']} → {r.get('error') or r.get('llm','')[:60]}")
    else:
        print("   Tidak ada file yang gagal total ✅")

    print("\n" + "=" * 60)

    # Simpan ringkasan ke file
    output_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "log", "ringkasan_analisis.txt")
    with open(output_path, "w", encoding="utf-8") as f:
        f.write(f"Total audio      : {total}\n")
        f.write(f"Pipeline lengkap : {pipeline_full} ({pipeline_full/total*100:.1f}%)\n")
        f.write(f"STT berhasil     : {stt_berhasil} ({stt_berhasil/total*100:.1f}%)\n")
        f.write(f"LLM berhasil     : {llm_berhasil} ({llm_berhasil/total*100:.1f}%)\n")
        f.write(f"TTS berhasil     : {tts_berhasil} ({tts_berhasil/total*100:.1f}%)\n")
        f.write(f"Latency STT avg  : {avg(lat_stt):.2f}s\n")
        f.write(f"Latency LLM avg  : {avg(lat_llm):.2f}s\n")
        f.write(f"Latency TTS avg  : {avg(lat_tts):.2f}s\n")
        f.write(f"Latency E2E avg  : {avg(total_lat):.2f}s\n")

    print(f"Ringkasan disimpan ke: {output_path}")

if __name__ == "__main__":
    main()
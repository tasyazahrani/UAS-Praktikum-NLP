import os
import time
import re
from google import genai
from google.genai import types
from pydantic import TypeAdapter
from dotenv import load_dotenv

load_dotenv()

# Daftarkan semua API key di sini
API_KEYS = [
    os.getenv("GEMINI_API_KEY"),
    os.getenv("GEMINI_API_KEY_2"),
    os.getenv("GEMINI_API_KEY_3"),
]
# Filter key yang None
API_KEYS = [k for k in API_KEYS if k]

MODEL = "gemini-2.5-flash"

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
CHAT_HISTORY_FILE = os.path.join(BASE_DIR, "chat_history.json")

system_instruction = """
You are a responsive, intelligent multilingual virtual assistant that handles code-switching between Indonesian (Bahasa Indonesia), English, and Arabic.

Your task is to respond naturally to user input that may contain a mix of these three languages.

Your responses must follow these rules:
1. Detect the dominant language or language mix in the user's message.
2. Respond in the SAME language mix as the user (preserve code-switching).
3. If the user speaks pure Indonesian → respond in Indonesian.
4. If the user speaks pure English → respond in English.
5. If the user speaks pure Arabic → respond in Arabic.
6. If the user mixes languages → respond with the same mix.
7. Keep answers short and to the point (maximum 2-3 sentences).
8. Be polite and natural in all three languages.
9. If the transcription result is unclear like "(Speaking in foreign language)", ask the user politely to repeat in Indonesian, English, or Arabic.

Examples:
User: Aku mau pergi ke market, can you recommend the best one?
Assistant: Sure! Pasar terbaik di sini adalah Pasar Baru, it has a wide variety of goods dengan harga terjangkau.

User: Tolong jelaskan apa itu machine learning.
Assistant: Machine learning adalah cabang dari kecerdasan buatan yang memungkinkan komputer belajar dari data tanpa diprogram secara eksplisit.

User: Explain step by step how to book a flight online.
Assistant: First, open a flight booking website or app, then enter your departure city, destination, date, and number of passengers. Choose your preferred flight, fill in your personal details, and complete the payment.

User: (Speaking in foreign language)
Assistant: Maaf, saya tidak dapat mengenali bahasa Anda. Silakan ulangi dalam Bahasa Indonesia, English, atau العربية.
"""

history_adapter = TypeAdapter(list[types.Content])
current_key_index = 0

def get_client():
    return genai.Client(api_key=API_KEYS[current_key_index])

def get_chat_config():
    return types.GenerateContentConfig(system_instruction=system_instruction)

def export_chat_history(chat) -> str:
    return history_adapter.dump_json(chat.get_history()).decode("utf-8")

def save_chat_history(chat):
    json_history = export_chat_history(chat)
    with open(CHAT_HISTORY_FILE, "w", encoding="utf-8") as f:
        f.write(json_history)

def load_chat_history(client, chat_config):
    if not os.path.exists(CHAT_HISTORY_FILE):
        return client.chats.create(model=MODEL, config=chat_config)
    if os.path.getsize(CHAT_HISTORY_FILE) == 0:
        return client.chats.create(model=MODEL, config=chat_config)
    with open(CHAT_HISTORY_FILE, "r", encoding="utf-8") as f:
        json_str = f.read().strip()
    if not json_str:
        return client.chats.create(model=MODEL, config=chat_config)
    try:
        history = history_adapter.validate_json(json_str)
        return client.chats.create(model=MODEL, config=chat_config, history=history)
    except Exception as e:
        print(f"[ERROR] Gagal load history chat: {e}")
        return client.chats.create(model=MODEL, config=chat_config)

def generate_response(prompt: str) -> str:
    global current_key_index

    for attempt in range(len(API_KEYS) * 3):
        try:
            client = get_client()
            chat_config = get_chat_config()
            chat = load_chat_history(client, chat_config)

            response = chat.send_message(prompt)
            save_chat_history(chat)
            print(f"  [LLM] Menggunakan key index: {current_key_index}")
            return response.text.strip()

        except Exception as e:
            error_str = str(e)
            if "429" in error_str:
                # Coba rotate ke key berikutnya
                next_index = (current_key_index + 1) % len(API_KEYS)
                if next_index != current_key_index:
                    print(f"  [LLM] Key {current_key_index} limit! Rotate ke key {next_index}...")
                    current_key_index = next_index
                    time.sleep(2)
                else:
                    # Semua key sudah dicoba, tunggu dulu
                    match = re.search(r'retry in (\d+)', error_str)
                    wait_time = int(match.group(1)) + 5 if match else 30
                    print(f"  [LLM] Semua key limit! Tunggu {wait_time}s...")
                    time.sleep(wait_time)
            else:
                return f"[ERROR] {error_str}"

    return "[ERROR] Semua API key habis quota"
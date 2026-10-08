import requests
import json

TOKEN = "ВАШ_ТОКЕН_MAX"
URL = "https://platform-api.max.ru/messages"
HEADERS = {"Authorization": TOKEN, "Content-Type": "application/json"}
USER_ID = 5194550

tests = [
    ("1. Только text", {"user_id": USER_ID, "text": "Test minimal"}),
    
    ("2. text + format (в body)", {"user_id": USER_ID, "body": {"text": "Test", "format": "plain"}}),
    
    ("3. text + format (top)", {"user_id": USER_ID, "text": "Test", "format": "plain"}),
    
    ("4. text + attachments (без format)", {
        "user_id": USER_ID,
        "text": "Test with btn",
        "attachments": [{
            "type": "inline_keyboard",
            "payload": {
                "buttons": [[{"type": "callback", "text": "OK", "payload": "ok"}]]
            }
        }]
    }),
    
    ("5. peer_id + text (минимум)", {"peer_id": USER_ID, "text": "Test peer"}),
]

print("🔍 Тестирование структуры body...\n")
for name, payload in tests:
    try:
        r = requests.post(URL, headers=HEADERS, json=payload, timeout=10)
        status = "✅ 200" if r.status_code == 200 and not r.text.startswith('{"code"') else f"❌ {r.status_code}"
        print(f"[{status}] {name}")
        print(f"     📤 {json.dumps(payload, ensure_ascii=False)[:120]}...")
        print(f"     📥 {r.text[:100]}\n")
        
        # Если успех — останавливаемся
        if r.status_code == 200 and not r.text.startswith('{"code"'):
            print("🎉 Нашли рабочую структуру! Используйте её в боте.")
            break
    except Exception as e:
        print(f"[💥 ERR] {name} | {e}\n")
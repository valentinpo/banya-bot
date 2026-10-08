import requests
import json

TOKEN = "ВАШ_ТОКЕН_MAX"
BASE = "https://platform-api.max.ru"

SENDER_ID = 5194550  # Из вашего лога: sender.user_id
CHAT_ID = 253857436  # Из вашего лога: recipient.chat_id

def test(payload, label):
    print(f"\n{'='*40}\n🧪 {label}")
    print(f"📤 {json.dumps(payload, ensure_ascii=False, indent=2)}")
    try:
        r = requests.post(f"{BASE}/messages", headers={"Authorization": TOKEN, "Content-Type": "application/json"}, json=payload, timeout=10)
        print(f"📥 HTTP {r.status_code}: {r.text}")
        if r.status_code == 200 and ("ok" in r.text.lower() or "success" in r.text.lower() or not r.text.startswith("{")):
            print("✅ СООБЩЕНИЕ ДОШЛО! Проверьте чат в MAX.")
    except Exception as e:
        print(f"❌ Сеть: {e}")

# 1. user_id (число)
test({"user_id": SENDER_ID, "body": {"text": "Тест 1: user_id int", "format": "plain"}}, "user_id (int)")

# 2. user_id (строка)
test({"user_id": str(SENDER_ID), "body": {"text": "Тест 2: user_id str", "format": "plain"}}, "user_id (str)")

# 3. peer_id (число)
test({"peer_id": SENDER_ID, "body": {"text": "Тест 3: peer_id int", "format": "plain"}}, "peer_id (int)")

# 4. peer_id (строка)
test({"peer_id": str(SENDER_ID), "body": {"text": "Тест 4: peer_id str", "format": "plain"}}, "peer_id (str)")

# 5. chat_id (строка)
test({"chat_id": str(CHAT_ID), "body": {"text": "Тест 5: chat_id str", "format": "plain"}}, "chat_id (str)")
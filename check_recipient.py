import requests
import json

TOKEN = "ВАШ_ТОКЕН_MAX"
BASE = "https://platform-api.max.ru"
SENDER_ID = 5194550  # Тот, кто написал /start
CHAT_ID   = 253857436

def test(name, payload):
    print(f"\n🔹 {name}")
    print(f"   📤 {json.dumps(payload, ensure_ascii=False)}")
    try:
        r = requests.post(f"{BASE}/messages", headers={"Authorization": TOKEN, "Content-Type": "application/json"}, json=payload, timeout=10)
        print(f"   ⬅️ HTTP {r.status_code}")
        print(f"   📄 {r.text[:200]}")
        if r.status_code == 200 and not r.text.strip().startswith('{"code"'):
            print("   ✅ УСПЕХ! Сообщение должно появиться в MAX.")
    except Exception as e:
        print(f"   ❌ Сеть: {e}")

# 1. peer_id (строка) + плоский текст
test("1. peer_id=str + text", {"peer_id": str(SENDER_ID), "text": "Test 1"})

# 2. user_id (строка) + body
test("2. user_id=str + body", {"user_id": str(SENDER_ID), "body": {"text": "Test 2", "format": "plain"}})

# 3. recipient.user_id (строка)
test("3. recipient.user_id=str", {"recipient": {"user_id": str(SENDER_ID)}, "body": {"text": "Test 3"}})

# 4. chat_id (строка) + body
test("4. chat_id=str + body", {"chat_id": str(CHAT_ID), "body": {"text": "Test 4"}})

# 5. to.user_id (вложенный объект)
test("5. to.user_id", {"to": {"user_id": SENDER_ID}, "body": {"text": "Test 5"}})
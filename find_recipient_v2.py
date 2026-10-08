import requests, json

TOKEN = "ВАШ_ТОКЕН_MAX"
URL = "https://platform-api.max.ru/messages"
HEADERS = {"Authorization": TOKEN, "Content-Type": "application/json"}
BODY = {"body": {"text": "Ping", "format": "plain"}}

USER = 5194550
CHAT = 253857436

tests = [
    ("peer_id (int)",       {"peer_id": USER, **BODY}),
    ("peer_id (str)",       {"peer_id": str(USER), **BODY}),
    ("peer_id (u-prefix)",  {"peer_id": f"u{USER}", **BODY}),
    ("chat_id (c-prefix)",  {"chat_id": f"c{CHAT}", **BODY}),
    ("target_id",           {"target_id": USER, **BODY}),
    ("recipient_id",        {"recipient_id": USER, **BODY}),
]

for name, payload in tests:
    try:
        r = requests.post(URL, headers=HEADERS, json=payload, timeout=10)
        status = "✅ 200" if r.status_code == 200 and not r.text.startswith('{"code"') else f"❌ {r.status_code}"
        print(f"[{status}] {name:20} | Ответ: {r.text[:80]}")
    except Exception as e:
        print(f"[❌ ERR] {name:20} | {e}")
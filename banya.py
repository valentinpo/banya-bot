import requests, time, logging, sys, os
from dotenv import load_dotenv

load_dotenv()
TOKEN = os.getenv("TOKEN", "ВАШ_ТОКЕН_MAX")
API = "https://platform-api.max.ru"
HEADERS = {"Authorization": TOKEN, "Content-Type": "application/json"}

logging.basicConfig(level=logging.INFO, format='%(asctime)s [%(levelname)s] %(message)s', handlers=[logging.StreamHandler(sys.stdout)])
log = logging.getLogger(__name__)

marker = None

# 🔥 КЛАВИАТУРА — ВОТ ОНА, КНОПКИ!
KB = {
    "inline_keyboard": [
        [{"text": "🏠 Визитка", "callback_data": "vizitka"}, {"text": "💰 Прайс", "callback_data": "price"}],
        [{"text": "❓ FAQ", "callback_data": "faq"}, {"text": "📝 Забронировать", "callback_data": "book"}]
    ]
}

def send(uid, txt, keyboard=None):
    """✅ Отправка: если keyboard передан — он попадёт в API"""
    url = f"{API}/messages?user_id={uid}"
    payload = {"text": txt, "format": "markdown"}
    if keyboard:  # ← КЛЮЧЕВОЙ МОМЕНТ: добавляем клавиатуру в payload
        payload["keyboard"] = keyboard
    try:
        r = requests.post(url, headers=HEADERS, json=payload, timeout=5)
        return r.status_code == 200
    except Exception as e:
        log.error(f"Send error: {e}")
        return False

def get_updates():
    global marker
    try:
        params = {"timeout": 30}
        if marker: params["marker"] = marker
        r = requests.get(f"{API}/updates", headers=HEADERS, params=params, timeout=35)
        if r.status_code == 200:
            d = r.json()
            marker = d.get("marker")
            return d.get("updates", [])
    except:
        time.sleep(2)
    return []

def handle(u):
    t = u.get("update_type")
    
    # 1. Старт бота
    if t == "bot_started":
        uid = u.get("user", {}).get("user_id")
        nm = u.get("user", {}).get("name", "Гость")
        if uid:
            # ✅ ОТПРАВЛЯЕМ С КЛАВИАТУРОЙ!
            send(uid, f"👋 Привет, {nm}! Я бот бани 🛁\nНажми кнопку:", KB)
    
    # 2. Нажатие кнопки 🔥
    elif t == "callback_query":
        cb = u.get("callback_query", {})
        uid = cb.get("from", {}).get("user_id") or cb.get("user_id")
        data = cb.get("data")
        log.info(f"🖱️ Кнопка: {data} от {uid}")
        
        if uid and data:  # ✅ Проверка, чтобы не падало
            if data == "vizitka":
                send(uid, "📍 Адрес: ул. Банная, 1\n📞 +7 (999) 123-45-67", KB)
            elif data == "price":
                send(uid, "⏱️ 1 час: 1500 ₽\n🎁 3 часа: 4000 ₽\n🔥 Мангал: 500 ₽", KB)
            elif data == "faq":
                send(uid, "❓ FAQ:\n• Парковка — да\n• Дети — да\n• Своё — еда да, алкоголь нет", KB)
            elif data == "book":
                send(uid, "📅 Напишите дату и время — админ свяжется!", KB)
    
    # 3. Текст
    elif t == "message_created":
        m = u.get("message", {})
        uid = m.get("sender", {}).get("user_id")
        txt = m.get("body", {}).get("text", "").strip().lower()
        if uid and txt in ["/start", "привет", "меню"]:
            send(uid, "👋 Главное меню:", KB)  # ✅ С кнопками!

def main():
    log.info("🤖 Запуск бота Бани (кнопки включены!)")
    while True:
        try:
            for upd in get_updates():
                handle(upd)
            time.sleep(1)
        except KeyboardInterrupt:
            log.info("🛑 Стоп")
            break
        except Exception as e:
            log.error(f"Err: {e}")
            time.sleep(3)

if __name__ == "__main__":  # ✅ Правильная проверка!
    main()
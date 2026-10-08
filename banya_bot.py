import requests
import time
import logging
import sys

# === 1. НАСТРОЙКИ ===
TOKEN = "ВАШ_ТОКЕН_MAX"  # ⚠️ ВСТАВЬТЕ СЮДА СВОЙ ТОКЕН
API_URL = "https://platform-api.max.ru"
HEADERS = {"Authorization": f"Bearer {TOKEN}", "Content-Type": "application/json"}

# Логи сразу в консоль
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s',
    handlers=[logging.StreamHandler(sys.stdout)]
)
log = logging.getLogger(__name__)

marker = None

# === 2. КЛАВИАТУРА (КНОПКИ) ===
KB = {
    "inline_keyboard": [
        [{"text": "🏠 Визитка", "callback_data": "vizitka"}, {"text": "💰 Прайс", "callback_data": "price"}],
        [{"text": "❓ FAQ", "callback_data": "faq"}, {"text": "📝 Забронировать", "callback_data": "book"}]
    ]
}

# === 3. ОТПРАВКА СООБЩЕНИЙ ===
def send_msg(uid, text, keyboard=None):
    url = f"{API_URL}/messages?user_id={uid}"
    payload = {"text": text, "format": "markdown"}
    if keyboard:
        payload["keyboard"] = keyboard  # ✅ КНОПКИ ДОБАВЛЯЮТСЯ СЮДА
    try:
        r = requests.post(url, headers=HEADERS, json=payload, timeout=10)
        if r.status_code == 200:
            log.info(f"✅ Отправлено пользователю {uid}")
            return True
        log.error(f"❌ Ошибка API {r.status_code}: {r.text}")
    except Exception as e:
        log.error(f"❌ Ошибка отправки: {e}")
    return False

# === 4. ПОЛУЧЕНИЕ ОБНОВЛЕНИЙ (LONGPOLL) ===
def get_updates():
    global marker
    # MAX API использует 'wait' для ожидания, а не 'timeout'
    params = {"wait": 30}
    if marker:
        params["marker"] = marker
    try:
        # timeout=35 > wait=30, чтобы клиент не обрывал соединение раньше сервера
        r = requests.get(f"{API_URL}/updates", headers=HEADERS, params=params, timeout=40)
        if r.status_code == 200:
            data = r.json()
            marker = data.get("marker")
            updates = data.get("updates", [])
            if updates:
                log.info(f"📨 Получено {len(updates)} событий")
                return updates
    except requests.exceptions.ReadTimeout:
        pass  # Нормально: сервер просто не получил новых сообщений за 30 сек
    except Exception as e:
        log.warning(f"⚠️ Ошибка polling: {e}")
    return []

# === 5. ОБРАБОТКА СОБЫТИЙ ===
def handle(update):
    t = update.get("update_type")
    
    # 1. Пользователь запустил бота
    if t == "bot_started":
        uid = update.get("user", {}).get("user_id")
        name = update.get("user", {}).get("name", "Гость")
        if uid:
            send_msg(uid, f"👋 Привет, {name}! Я бот бани 🛁\nЖми кнопку:", KB)
            
    # 2. Нажатие на кнопку
    elif t == "callback_query":
        cb = update.get("callback_query", {})
        uid = cb.get("from", {}).get("user_id") or cb.get("user_id")
        data = cb.get("data")
        if uid and data:
            log.info(f"🖱️ Нажато: {data} (User: {uid})")
            if data == "vizitka":
                send_msg(uid, "📍 Адрес: ул. Банная, 1\n📞 +7 (999) 123-45-67", KB)
            elif data == "price":
                send_msg(uid, "⏱️ 1 час: 1500 ₽\n🎁 3 часа: 4000 ₽\n🔥 Мангал: 500 ₽", KB)
            elif data == "faq":
                send_msg(uid, "❓ FAQ:\n• Парковка — да\n• Дети — да\n• Своё — еда да, алкоголь нет", KB)
            elif data == "book":
                send_msg(uid, "📅 Напишите дату и время — админ свяжется с вами!", KB)
                
    # 3. Текстовое сообщение
    elif t == "message_created":
        m = update.get("message", {})
        uid = m.get("sender", {}).get("user_id")
        txt = m.get("body", {}).get("text", "").strip().lower()
        if uid and txt in ["/start", "привет", "меню"]:
            send_msg(uid, "👋 Главное меню:", KB)

# === 6. ЗАПУСК ===
def main():
    log.info("🤖 Запуск бота Бани...")
    while True:
        try:
            updates = get_updates()
            for u in updates:
                handle(u)
            time.sleep(1)  # Пауза, чтобы не грузить процессор
        except KeyboardInterrupt:
            log.info("🛑 Бот остановлен.")
            break
        except Exception as e:
            log.error(f"🔥 Критическая ошибка: {e}")
            time.sleep(5)

if __name__ == "__main__":
    main()
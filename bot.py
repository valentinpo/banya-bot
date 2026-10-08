#!/usr/bin/env python3
import requests
import time
import logging
import sqlite3
import sys
import os
from datetime import datetime

# === 1. НАСТРОЙКИ ===
TOKEN = os.environ.get("MAX_TOKEN", "ВАШ_ТОКЕН")  # ⚠️ Или вставьте сюда
ADMIN_ID = os.environ.get("ADMIN_ID", "")  # ⚠️ Вставьте ваш USER_ID в MAX
BASE = "https://platform-api.max.ru"
HEADERS = {"Authorization": TOKEN, "Content-Type": "application/json"}

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s',
    stream=sys.stdout
)
log = logging.getLogger(__name__)

# === 2. БАЗА ДАННЫХ (SQLite) ===
def init_db():
    conn = sqlite3.connect('banya_bookings.db')
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS bookings (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        client_id TEXT, name TEXT, book_date TEXT, book_time TEXT,
        guests TEXT, phone TEXT, status TEXT DEFAULT 'new', created_at TEXT)''')
    conn.commit()
    conn.close()

def save_booking(data):
    conn = sqlite3.connect('banya_bookings.db')
    c = conn.cursor()
    c.execute('''INSERT INTO bookings (client_id, name, book_date, book_time, guests, phone, status, created_at)
                 VALUES (?, ?, ?, ?, ?, ?, 'new', ?)''',
              (data['client_id'], data.get('name',''), data['date'], data['time'],
               data['guests'], data['phone'], datetime.now().isoformat()))
    conn.commit()
    conn.close()

# === 3. ОТПРАВКА (СТРОГО ПО ФОРМАТУ MAX) ===
def send(uid, text, buttons=None):
    url = f"{BASE}/messages?user_id={uid}"
    payload = {"text": text}
    if buttons:
        payload["attachments"] = [{
            "type": "inline_keyboard",
            "payload": {"buttons": buttons}
        }]
    try:
        r = requests.post(url, headers=HEADERS, json=payload, timeout=10)
        if r.status_code != 200:
            log.error(f"❌ API {r.status_code}: {r.text}")
        return r.status_code == 200
    except Exception as e:
        log.error(f"❌ Ошибка отправки: {e}")
        return False

# === 4. КЛАВИАТУРЫ ===
MAIN_KB = [[
    {"type": "callback", "text": "🏠 Визитка", "payload": "vizitka"},
    {"type": "callback", "text": "💰 Прайс", "payload": "price"}
], [
    {"type": "callback", "text": "❓ FAQ", "payload": "faq"},
    {"type": "callback", "text": "📝 Забронировать", "payload": "book"}
], [
    {"type": "callback", "text": "🔧 Для заказчика", "payload": "for_client"}
]]

def get_admin_kb(client_id):
    return [[
        {"type": "callback", "text": "✅ Свободно", "payload": f"adm_ok_{client_id}"},
        {"type": "callback", "text": "❌ Занято", "payload": f"adm_no_{client_id}"}
    ], [
        {"type": "callback", "text": "📞 Перезвонить", "payload": f"adm_call_{client_id}"}
    ]]

# === 5. ЛОГИКА ФОРМЫ БРОНИРОВАНИЯ ===
user_states = {}  # {user_id: {"step": "...", "data": {...}}}

def handle_form(uid, txt):
    state = user_states[uid]
    step = state["step"]
    d = state["data"]

    if step == "date":
        d["date"] = txt
        state["step"] = "time"
        send(uid, "⏰ На какое время? (например, 18:00)")
    elif step == "time":
        d["time"] = txt
        state["step"] = "guests"
        send(uid, "👥 Сколько будет гостей?")
    elif step == "guests":
        d["guests"] = txt
        state["step"] = "phone"
        send(uid, "📱 Ваш телефон или имя для связи?")
    elif step == "phone":
        d["phone"] = txt
        save_booking(d)
        
        # 📩 Уведомление админу
        msg = (f"🔔 *НОВАЯ ЗАЯВКА*\n"
               f"👤 ID: `{d['client_id']}`\n"
               f"📅 {d['date']} в {d['time']}\n"
               f"👥 {d['guests']}\n📞 {d['phone']}")
        send(ADMIN_ID, msg, get_admin_kb(d['client_id']))
        
        # ✅ Ответ клиенту
        send(uid, "✅ Заявка принята! Ожидайте подтверждения администратора.", MAIN_KB)
        del user_states[uid]

# === 6. ОБРАБОТКА ДЕЙСТВИЙ АДМИНА ===
def handle_admin_action(admin_uid, payload):
    if str(admin_uid) != str(ADMIN_ID):
        send(admin_uid, "⛔ Это меню только для администратора")
        return

    # payload вида: adm_ok_5194550
    action, client_id = payload.rsplit("_", 1)
    replies = {
        "adm_ok": "✅ Ваша бронь подтверждена! Ждём вас 🛁",
        "adm_no": "❌ К сожалению, это время занято. Выберите другое или свяжитесь с нами.",
        "adm_call": "📞 Администратор получил заявку и скоро перезвонит вам."
    }
    
    if action in replies:
        send(client_id, replies[action])
        log.info(f"✅ Админ нажал {action} → ответ отправлен клиенту {client_id}")
        
        # Обновляем статус в БД
        conn = sqlite3.connect('banya_bookings.db')
        conn.execute("UPDATE bookings SET status=? WHERE client_id=? ORDER BY id DESC LIMIT 1", (action.replace("adm_",""), client_id))
        conn.commit()
        conn.close()

# === 7. ГЛАВНЫЙ ЦИКЛ ===
def main():
    init_db()
    marker = None
    log.info("🤖 Бот Бани запущен. Напишите /start в MAX...")

    while True:
        try:
            url = f"{BASE}/updates?timeout=25"
            if marker: url += f"&marker={marker}"
            
            resp = requests.get(url, headers=HEADERS, timeout=30)
            if resp.status_code == 200:
                data = resp.json()
                marker = data.get("marker")
                updates = data.get("updates", [])

                for upd in updates:
                    utype = upd.get("update_type")

                    # 📩 1. Текстовое сообщение
                    if utype == "message_created":
                        msg = upd.get("message", {})
                        uid = msg.get("sender", {}).get("user_id")
                        txt = msg.get("body", {}).get("text", "").strip()
                        if not uid: continue

                        # Если пользователь в форме → обрабатываем шаги
                        if uid in user_states:
                            handle_form(uid, txt)
                            continue

                        # Команды меню
                        if txt.lower() in ["/start", "привет", "меню"]:
                            send(uid, "👋 Привет! Я бот бани 🛁\nЧем могу помочь?", MAIN_KB)
                        elif txt.lower() == "бронь":
                            user_states[uid] = {"step": "date", "data": {"client_id": uid}}
                            send(uid, "📅 На какую дату бронируем? (ДД.ММ)")

                    # 🖱️ 2. Нажатие кнопки
                    elif utype == "message_callback":
                        cb = upd.get("callback", {})
                        uid = cb.get("user", {}).get("user_id")
                        payload = cb.get("payload")
                        if not uid or not payload: continue

                        # Действия админа
                        if payload.startswith("adm_"):
                            handle_admin_action(uid, payload)
                            continue

                        # Действия клиента
                        if payload == "book":
                            user_states[uid] = {"step": "date", "data": {"client_id": uid}}
                            send(uid, "📅 На какую дату бронируем? (ДД.ММ)")
                        elif payload == "vizitka":
                            send(uid, "📍 Адрес: ул. Банная, 1\n📞 +7 (999) 123-45-67", MAIN_KB)
                        elif payload == "price":
                            send(uid, "⏱️ 1 час: 1500 ₽\n🎁 3 часа: 4000 ₽\n🔥 Мангал: 500 ₽", MAIN_KB)
                        elif payload == "faq":
                            send(uid, "❓ FAQ:\n• Парковка — да\n• Дети — да\n• Алкоголь — нет", MAIN_KB)
                        elif payload == "for_client":
                            send(uid, "💼 Хотите такого бота? Стоимость: 5 000 ₽\nПишите: @ваш_никнейм", MAIN_KB)

            time.sleep(1)  # Пауза между циклами polling

        except KeyboardInterrupt:
            log.info("\n🛑 Бот остановлен.")
            break
        except Exception as e:
            log.error(f"🔥 Критическая ошибка: {e}")
            time.sleep(3)

if __name__ == "__main__":
    main()
#!/usr/bin/env python3
import os, sys, time, logging, sqlite3, requests
from datetime import datetime

# === 🔐 ЧТЕНИЕ .env ВРУЧНУЮ ===
def load_env(filepath=".env"):
    env = {}
    try:
        with open(filepath, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith("#") and "=" in line:
                    key, value = line.split("=", 1)
                    env[key.strip()] = value.strip()
    except: pass
    return env

env = load_env()
TOKEN = env.get("MAX_BOT_TOKEN")
ADMIN_ID = env.get("ADMIN_ID")
if not TOKEN or not ADMIN_ID:
    print("❌ Ошибка: проверьте .env (MAX_BOT_TOKEN и ADMIN_ID)"); sys.exit(1)

BASE = "https://platform-api.max.ru"
HEADERS = {"Authorization": TOKEN, "Content-Type": "application/json"}

logging.basicConfig(level=logging.INFO, format='%(asctime)s [%(levelname)s] %(message)s', stream=sys.stdout)
log = logging.getLogger(__name__)

marker = None
user_states = {}
welcomed = set()
last_req = 0

# === ️ БАЗА ДАННЫХ ===
def init_db():
    conn = sqlite3.connect('banya.db')
    c = conn.cursor()
    # ✅ Обновлено: добавлено поле service
    c.execute('''CREATE TABLE IF NOT EXISTS bookings (
        id INTEGER PRIMARY KEY AUTOINCREMENT, client_id TEXT, name TEXT, service TEXT,
        book_date TEXT, book_time TEXT, duration TEXT, guests TEXT, phone TEXT,
        status TEXT DEFAULT 'new', created_at TEXT)''')
    conn.commit(); conn.close()

def save_booking(d):
    conn = sqlite3.connect('banya.db')
    c = conn.cursor()
    # ✅ Обновлено: 10 полей для вставки
    c.execute('''INSERT INTO bookings (client_id,name,service,book_date,book_time,duration,guests,phone,status,created_at)
                 VALUES (?,?,?,?,?,?,?,?,?,?)''',
              (d['client_id'], d.get('name',''), d.get('service',''), d['date'], d['time'], 
               d.get('duration',''), d['guests'], d['phone'], 'new', datetime.now().isoformat()))
    conn.commit(); conn.close()

# === 📊 СТАТИСТИКА КЛИЕНТА ===
def get_client_stats(client_id):
    conn = sqlite3.connect('banya.db')
    c = conn.cursor()
    
    # Считаем количество визитов
    c.execute("SELECT COUNT(*) FROM bookings WHERE client_id=?", (client_id,))
    visits = c.fetchone()[0]
    
    # Ищем дату последнего визита
    c.execute("SELECT book_date FROM bookings WHERE client_id=? ORDER BY id DESC LIMIT 1", (client_id,))
    row = c.fetchone()
    last_visit = row[0] if row else "— (первый визит)"
    
    # Определяем статус
    status = "Новичок"
    if visits > 5: status = "👑 VIP Клиент"
    elif visits > 2: status = "🔥 Постоянный гость"
    
    conn.close()
    return visits, status, last_visit

# ===  ОТПРАВКА (с поддержкой Markdown) ===
def send(uid, text, buttons=None):
    url = f"{BASE}/messages?user_id={uid}"
    payload = {"text": text, "format": "markdown"}
    if buttons:
        payload["attachments"] = [{"type": "inline_keyboard", "payload": {"buttons": buttons}}]
    try:
        r = requests.post(url, headers=HEADERS, json=payload, timeout=10)
        return r.status_code == 200
    except Exception as e:
        log.error(f"❌ Send: {e}")
        return False

# === 🎛️ КЛАВИАТУРЫ ===
MAIN_KB = [[
    {"type": "callback", "text": "🏠 Визитка", "payload": "vizitka"},
    {"type": "callback", "text": "💰 Прайс", "payload": "price"}
], [
    {"type": "callback", "text": " FAQ", "payload": "faq"},
    {"type": "callback", "text": "📝 Забронировать", "payload": "book"}
], [
    {"type": "callback", "text": "📞 Связаться", "payload": "contact"}
]]

def admin_kb(cid):
    return [[
        {"type": "callback", "text": "✅ Свободно", "payload": f"adm_ok_{cid}"},
        {"type": "callback", "text": "❌ Занято", "payload": f"adm_no_{cid}"}
    ], [{"type": "callback", "text": "📞 Перезвонить", "payload": f"adm_call_{cid}"}]]

# === 📝 ФОРМА БРОНИРОВАНИЯ (7 шагов + статистика) ===
def handle_form(uid, txt):
    st = user_states[uid]
    step = st["step"]
    d = st["data"]
    
    if step == "service": 
        d["service"] = txt; st["step"] = "date"
        send(uid, "️ **ВЫБИРАЕМ ДАТУ**\n\nНа какое число хотите забронировать отдых?\n(например: *15.06*)")
        
    elif step == "date": 
        d["date"] = txt; st["step"] = "time"
        send(uid, "🕐 **ВРЕМЯ СТАРТА**\n\nНа какое время вас записать?\n(например: *18:00*)")
        
    elif step == "time": 
        d["time"] = txt; st["step"] = "duration"
        send(uid, "⏳ **СКОЛЬКО ВРЕМЕНИ?**\n\nНа какой срок забронировать удовольствие?\n(например: *3 часа*)")
        
    elif step == "duration": 
        d["duration"] = txt; st["step"] = "guests"
        send(uid, " **КОМПАНИЯ**\n\nСколько всего будет гостей?\n(включая детей)")
        
    elif step == "guests": 
        d["guests"] = txt; st["step"] = "name"
        send(uid, " **КАК К ВАМ ОБРАЩАТЬСЯ?**\n\nНапишите ваше имя")
        
    elif step == "name": 
        d["name"] = txt; st["step"] = "phone"
        send(uid, " **ТЕЛЕФОН ДЛЯ СВЯЗИ**\n\nОставьте номер, чтобы админ мог подтвердить бронь")
        
    elif step == "phone":
        d["phone"] = txt
        save_booking(d)
        
        #  Получаем статистику для сообщения админу
        visits, status, last_visit = get_client_stats(d['client_id'])
        
        msg = (
            f"🔥 **НОВАЯ ЗАЯВКА ({status})**\n\n"
            f"👤 **Клиент:** {d['name']}\n"
            f"📞 **Связь:** {d['phone']}\n"
            f"🏠 **Услуга:** {d['service']}\n"
            f"➖➖➖➖➖➖➖\n"
            f"📊 **История:** {visits} визитов | Последний: {last_visit}\n"
            f" *Дата:* `{d['date']}`\n"
            f"🕐 *Время:* `{d['time']}`\n"
            f"⏳ *Срок:* {d['duration']}\n"
            f"👥 *Гости:* {d['guests']}\n\n"
            f"🆔 ID: `{d['client_id']}`"
        )
        
        send(ADMIN_ID, msg, admin_kb(d['client_id']))
        send(uid, f"✅ **Заявка принята!**\n\nАдминистратор уже видит её и скоро свяжется с вами. {status} 🛁✨", MAIN_KB)
        del user_states[uid]

# === 👨‍💼 ОБРАБОТКА ДЕЙСТВИЙ АДМИНА ===
def handle_admin(uid, payload):
    if str(uid) != ADMIN_ID: return
    action, cid = payload.rsplit("_", 1)
    replies = {"adm_ok": "✅ Бронь подтверждена! Ждём вас ", "adm_no": "❌ Время занято.", "adm_call": "📞 Скоро перезвоним."}
    if action in replies:
        send(cid, replies[action])
        conn = sqlite3.connect('banya.db')
        conn.execute("UPDATE bookings SET status=? WHERE client_id=? AND status='new'", (action.replace("adm_",""), cid))
        conn.commit(); conn.close()

# === 🔄 POLLING ===
def get_updates():
    global marker, last_req
    if time.time() - last_req < 0.5: time.sleep(0.5)
    last_req = time.time()
    url = f"{BASE}/updates?timeout=20"
    if marker: url += f"&marker={marker}"
    try:
        resp = requests.get(url, headers=HEADERS, timeout=25)
        if resp.status_code == 200:
            data = resp.json()
            marker = data.get("marker")
            return data.get("updates", [])
    except Exception as e:
        log.warning(f"⚠️ Polling: {e}")
    return []

# === 🎯 ГЛАВНЫЙ ЦИКЛ ===
def main():
    global marker
    init_db()
    log.info("🤖 Бот Прусской бани запущен...")
    
    while True:
        try:
            for upd in get_updates():
                ut = upd.get("update_type")
                
                # 📩 Текст
                if ut == "message_created":
                    msg = upd.get("message", {})
                    uid = msg.get("sender", {}).get("user_id")
                    txt = msg.get("body", {}).get("text", "").strip().lower()
                    if not uid: continue
                    
                    if uid in user_states:
                        handle_form(uid, txt); continue
                        
                    # 🎁 Персональное приветствие на основе статистики
                    if any(kw in txt for kw in ["старт", "start", "/start", "привет", "меню"]):
                        nm = msg.get("sender", {}).get("name", "Гость")
                        visits, status, _ = get_client_stats(uid)
                        
                        greet = f"👋 Привет, {nm}!"
                        if visits > 0:
                            greet += f"\nРады видеть вас снова! ({status})"
                        else:
                            greet += "\nДобро пожаловать в Прусскую баню!"
                            
                        send(uid, f"{greet}\n\nЯ помощник по аренде. Чем могу помочь?", MAIN_KB)
                        log.info(f"✅ Приветствие → {uid}")
                        
                # 🔘 Кнопка
                elif ut == "message_callback":
                    cb = upd.get("callback", {})
                    uid = cb.get("user", {}).get("user_id")
                    pl = cb.get("payload")
                    if not uid or not pl: continue
                    
                    if pl.startswith("adm_"):
                        handle_admin(uid, pl); continue
                        
                    if pl == "book":
                        # ✅ Новый шаг начинается с выбора услуги
                        user_states[uid] = {"step": "service", "data": {"client_id": uid}}
                        send(uid, "🛁 **БРОНИРОВАНИЕ**\n\nДавайте заполним заявку, это займет 1 минуту!\n\n🏠 **ЧТО ПЛАНИРУЕТЕ АРЕНДОВАТЬ?**\n(Баня / Банный чан / Беседка / Всё вместе)")
                        
                    elif pl == "vizitka":
                        send(uid, "🗺️ *Карта*\nhttps://yandex.ru/maps/-/CPsR7F3b\n\n📍 ул. Ковыльная, ст Звезда 56, Екатеринбург\n📞 +7 (965) 528-81-11\n📞 +7 (922) 188-74-21\n vk.com/prusskaya_banya\n\nЖдём вас — в живую Мы ещё лучше! ", MAIN_KB)
                    elif pl == "price":
                        send(uid, "💰 *ПРАЙС*\n\n🛁 **Аренда бани**\n• От 2-х часов — 1900 ₽/час\n\n🪵 **Банный чан**\n• 3 часа — 4500 ₽")
                        send(uid, "🏡 **Аренда беседки** (от 3-х часов)\n• Пн–Чт: 1500 ₽/час или 15 000 ₽/день (до 8 гостей)\n• Пт–Вс и праздники: 2000 ₽/час (до 8 гостей)\n• +300 ₽ за каждого гостя свыше 8\n• 👶 Дети до 7 лет — бесплатно!\n🎂 *Скидка 10% на беседку в день рождения!*\n\n✅ *Во всё включено:* парковка, мангал, шампуры, аудиосистема с Bluetooth.", MAIN_KB)
                    elif pl == "faq":
                        send(uid, "❓ FAQ:\n1️⃣ Парковка? Да.\n2️ Мангал? Да.\n3️ Дети? Да.\n4️⃣ Опоздание? Напишите.\n6️⃣ Wi-Fi? Да.\n7️⃣ Своё? Еда/торт — да. Алкоголь — да.", MAIN_KB)
                    elif pl == "contact":
                        send(uid, " **Телефоны (нажмите для звонка):**\n[+7 (965) 528-81-11](tel:+79655288111)\n[+7 (922) 188-74-21](tel:+79221887421)")
                        send(uid, "🗺️ **Мы на карте:**\nhttps://yandex.ru/maps/-/CPsR7F3b")
                        send(uid, "🌐 **Мы в интернете:**\n🏠 [Официальный сайт](https://prusskaya-banya.clients.site/)\n [ВКонтакте](https://vk.com/prusskaya_banya?w=club220528099)\n🎬 [VK Видео](https://vkvideo.ru/@prusskaya_banya)\n🛍️ [Авито Услуги](https://www.avito.ru/brands/94bf70475a521c10db3632ffb93044c7/all/predlozheniya_uslug?sellerId=3599eb768a85d790ab71bd0b6a510974)\n▶️ [YouTube](https://www.youtube.com/channel/UCCyRnd4SDqKM2IcFVii7Qqw)\n🗺️ [Zoon](https://zoon.ru/ekb/sauna/kompaniya_po_arende_bani_i_besedok_prusskaya_besedka/)\n📍 [2GIS](https://2gis.ru/ekaterinburg/firm/70000001090893695)\n✈️ [Telegram](https://t.me/prusskaya_banya)\n\n *Хотите написать в MAX?* Оставьте заявку через кнопку «📝 Забронировать» — админ увидит её мгновенно.", MAIN_KB)
                        
                # 🚀 Запуск
                elif ut == "bot_started" and upd.get("user", {}).get("user_id") not in welcomed:
                    uid = upd["user"]["user_id"]
                    welcomed.add(uid)
                    nm = upd["user"].get("name", "Гость")
                    send(uid, f"👋 Привет, {nm}! Я помощник по аренде Прусской бани. Чем могу помочь?", MAIN_KB)
                    log.info(f"✅ Приветствие → {uid}")
                    
            time.sleep(1)
            
        except KeyboardInterrupt:
            log.info("\n🛑 Стоп."); break
        except Exception as e:
            log.error(f"🔥 Ошибка: {e}"); time.sleep(3)

if __name__ == "__main__":
    main()
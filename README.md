# 🧖 Banya Bot

Telegram-бот для приёма бронирования бани на платформе **MAX** (platform-api.max.ru). Клиент выбирает дату, время, количество гостей и телефон — заявка отправляется администратору, который подтверждает или отклоняет бронь.

## ✨ Возможности

- 📅 **Форма бронирования** — дата → время → гости → телефон
- 🔔 **Уведомление администратору** о новой заявке
- ✅ / ❌ **Подтверждение или отклонение** брони кнопками
- 🏠 **Визитка, прайс, FAQ, контакты** — настраиваемое меню
- 🔄 **Long-polling** обновлений (без webhook)

## 📁 Структура

```
banya-bot/
├── bot.js               # Основной бот (Node.js версия)
├── banya.py             # Python-версия (Max API)
├── banya_bot.py         # Структурированная Python-версия
├── banya_simple.py      # Упрощённая версия
├── bot.py               # Полный флоу для Python
├── find_id.py           # Поиск ID отправителя
├── find_recipient_v2.py # Поиск получателя (v2)
├── check_recipient.py   # Проверка получателя сообщений
├── minimal_test.py      # Минимальный тест API
├── test.py              # Тесты общего флоу
├── test_banya.py        # Тесты бронирования
├── test_body.py         # Тесты состава сообщений
├── .env.example         # Шаблон настроек
└── README.md
```

## 🚀 Быстрый старт (Node.js)

```bash
npm install dotenv axios        # зависимости
cp .env.example .env             # заполните токен и ADMIN_ID
node bot.js
```

## 🚀 Быстрый старт (Python)

```bash
pip install requests python-dotenv
cp .env.example .env
python banya_bot.py
```

## ⚙️ Настройка

В `.env` (или прямо в коде) укажите:

| Параметр | Назначение |
|----------|-----------|
| `MAX_BOT_TOKEN` / `TOKEN` | API-токен бота на платформе MAX |
| `ADMIN_ID` | User ID администратора, которому приходят заявки |

## 🔌 API

Используется публичный API платформы MAX:

- `GET https://platform-api.max.ru/updates` — получение обновлений (long-polling)
- `POST https://platform-api.max.ru/messages?user_id=...` — отправка сообщения

## 📄 Лицензия

MIT (см. [LICENSE](LICENSE)).
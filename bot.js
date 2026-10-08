require('dotenv').config();
const axios = require('axios');

// === НАСТРОЙКИ ===
const TOKEN = process.env.MAX_BOT_TOKEN;
const ADMIN_ID = parseInt(process.env.ADMIN_ID || '0');
const API_URL = 'https://platform-api.max.ru';
const HEADERS = {
  'Authorization': TOKEN,
  'Content-Type': 'application/json'
};

let marker = null;
const userStates = {}; // { userId: { step: 'date'|'time'|'guests'|'phone', ... } }

// === КЛАВИАТУРЫ ===
const MAIN_KEYBOARD = {
  inline_keyboard: [
    [{ text: '🏠 Визитка', callback_ 'vizitka' }, { text: '💰 Прайс', callback_data: 'price' }],
    [{ text: '❓ FAQ', callback_ 'faq' }, { text: '📝 Забронировать', callback_ 'book' }],
    [{ text: '📞 Связь', callback_data: 'contact' }, { text: '🔧 Для заказчика', callback_ 'client' }]
  ]
};

function getAdminKeyboard(clientId) {
  return {
    inline_keyboard: [
      [{ text: '✅ Свободно', callback_data: `adm_ok_${clientId}` }, { text: '❌ Занято', callback_data: `adm_no_${clientId}` }],
      [{ text: '📞 Перезвонить', callback_ `adm_call_${clientId}` }]
    ]
  };
}

// === ОТПРАВКА СООБЩЕНИЙ ===
async function sendMessage(userId, text, keyboard = null) {
  try {
    const payload = { text, format: 'markdown' };
    if (keyboard) payload.keyboard = keyboard;
    
    const resp = await axios.post(`${API_URL}/messages?user_id=${userId}`, payload, {
      headers: HEADERS,
      timeout: 5000
    });
    
    if (resp.status === 200) {
      console.log(`✅ Сообщение отправлено пользователю ${userId}`);
      return true;
    }
    console.error(`❌ Ошибка API ${resp.status}:`, resp.data);
  } catch (err) {
    console.error(`❌ Ошибка отправки:`, err.message);
  }
  return false;
}

// === ПОЛУЧЕНИЕ ОБНОВЛЕНИЙ ===
async function getUpdates() {
  try {
    const params = { timeout: 30 };
    if (marker) params.marker = marker;
    
    const resp = await axios.get(`${API_URL}/updates`, {
      headers: HEADERS,
      params,
      timeout: 35000
    });
    
    if (resp.status === 200) {
      const { updates, marker: newMarker } = resp.data;
      marker = newMarker;
      return updates || [];
    }
  } catch (err) {
    if (err.code !== 'ECONNABORTED') {
      console.warn(`⚠️ Ошибка polling:`, err.message);
    }
  }
  return [];
}

// === ФУНКЦИИ МЕНЮ ===
function sendWelcome(userId, name = 'Гость') {
  sendMessage(userId, `👋 Привет, ${name}! Я помощник по аренде бани [Название].\n\nЧем могу помочь?`, MAIN_KEYBOARD);
}

function sendVizitka(userId) {
  sendMessage(userId, '📍 Адрес: [адрес]\n📞 Телефон: [телефон]\n\nЖдём вас! 😄', MAIN_KEYBOARD);
}

function sendPrice(userId) {
  sendMessage(userId, '⏱️ Час: [цена] руб.\n🎁 Пакет: [цена] руб.\n\n🔥 Мангал: [цена] руб.', MAIN_KEYBOARD);
}

function sendFaq(userId) {
  sendMessage(userId, '❓ FAQ:\n\n1️⃣ Парковка? Да.\n2️⃣ Мангал? Да.\n3️⃣ Дети? Да.\n4️⃣ Опоздание? Напишите.\n6️⃣ Wi-Fi? Да.', MAIN_KEYBOARD);
}

function sendContact(userId) {
  sendMessage(userId, '📞 Администратор:\nТел: [номер]\nВремя: 10:00–23:00', MAIN_KEYBOARD);
}

function sendForClient(userId) {
  const devKb = { inline_keyboard: [[{ text: '📩 Написать разработчику', url: 'https://max.ru/u/ваш_юзернейм' }]] };
  sendMessage(userId, '💼 *Владельцу бани*\n\nХотите такого бота?\n\n💰 *Стоимость:*\n`5 000 ₽`', devKb);
}

// === ОБРАБОТКА КНОПОК ===
function handleCallback(userId, data, name) {
  console.log(`🖱️ Кнопка: ${data} | User: ${userId}`);
  
  // Кнопки админа
  if (data.startsWith('adm_')) {
    const [_, action, clientId] = data.split('_');
    const texts = {
      ok: '✅ Ваша бронь подтверждена! Ждём вас.',
      no: '❌ К сожалению, время занято. Выберите другое.',
      call: '📞 Администратор скоро свяжется с вами.'
    };
    if (texts[action]) {
      sendMessage(parseInt(clientId), texts[action]);
      // Здесь можно обновить статус в БД
    }
    return;
  }
  
  // Кнопки меню
  const actions = {
    vizitka: sendVizitka,
    price: sendPrice,
    faq: sendFaq,
    contact: sendContact,
    client: sendForClient
  };
  
  if (data === 'book') {
    userStates[userId] = { step: 'date', name };
    sendMessage(userId, '📅 На какую дату? (ДД.ММ)');
  } else if (actions[data]) {
    actions[data](userId);
  }
}

// === ФОРМА БРОНИРОВАНИЯ ===
function handleBooking(userId, text) {
  const state = userStates[userId];
  if (!state) return;
  
  const { step } = state;
  
  if (step === 'date') {
    state.bookDate = text;
    state.step = 'time';
    sendMessage(userId, '⏰ На какое время? (18:00)');
  } else if (step === 'time') {
    state.bookTime = text;
    state.step = 'guests';
    sendMessage(userId, '👥 Сколько гостей?');
  } else if (step === 'guests') {
    state.guests = text;
    state.step = 'phone';
    sendMessage(userId, '📱 Ваш телефон?');
  } else if (step === 'phone') {
    state.phone = text;
    
    // Уведомление админу
    const appMsg = `🔔 *НОВАЯ ЗАЯВКА*\n👤 ${state.name} (ID: \`${userId}\`)\n📅 ${state.bookDate} ${state.bookTime}\n👥 ${state.guests}\n📞 ${state.phone}`;
    sendMessage(ADMIN_ID, appMsg, getAdminKeyboard(userId));
    
    // Подтверждение клиенту
    sendMessage(userId, '✅ Заявка принята! Ждите ответа.', MAIN_KEYBOARD);
    
    delete userStates[userId];
  }
}

// === ОБРАБОТКА ОБНОВЛЕНИЙ ===
function handleUpdate(update) {
  const { update_type } = update;
  
  // 1. Запуск бота
  if (update_type === 'bot_started') {
    const { user_id: uid, name = 'Гость' } = update.user || {};
    if (uid) sendWelcome(uid, name);
    return;
  }
  
  // 2. Нажатие кнопки
  if (update_type === 'callback_query') {
    const cb = update.callback_query || {};
    const uid = cb.from?.user_id || cb.user_id;
    const data = cb.data;
    const name = cb.from?.name || 'Гость';
    
    if (uid && data) {
      handleCallback(uid, data, name);
    }
    return;
  }
  
  // 3. Текстовое сообщение
  if (update_type === 'message_created') {
    const msg = update.message || {};
    const sender = msg.sender || {};
    const uid = sender.user_id;
    const name = sender.name || 'Гость';
    const text = (msg.body?.text || '').trim();
    
    if (!uid || !text) return;
    
    // Если пользователь в форме бронирования
    if (userStates[uid]) {
      handleBooking(uid, text);
      return;
    }
    
    // Обычные команды
    const t = text.toLowerCase();
    if (['/start', 'привет', 'меню'].includes(t)) {
      sendWelcome(uid, name);
    } else if (['прайс', 'цена'].includes(t)) {
      sendPrice(uid);
    } else if (['бронь', 'записаться'].includes(t)) {
      userStates[uid] = { step: 'date', name };
      sendMessage(uid, '📅 На какую дату? (ДД.ММ)');
    } else {
      sendMessage(uid, '🤔 Не понял. Напишите `меню` или нажмите кнопку:', MAIN_KEYBOARD);
    }
  }
}

// === ЗАПУСК ===
async function main() {
  console.log('🤖 Запуск бота Бани (Node.js)...');
  console.log('✅ Готов к работе. Нажмите Ctrl+C для остановки.');
  
  while (true) {
    try {
      const updates = await getUpdates();
      for (const upd of updates) {
        handleUpdate(upd);
      }
      await new Promise(res => setTimeout(res, 1000));
    } catch (err) {
      console.error('🔥 Критическая ошибка:', err.message);
      await new Promise(res => setTimeout(res, 5000));
    }
  }
}

main();
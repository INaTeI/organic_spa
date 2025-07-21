import telebot
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton, ReplyKeyboardRemove
from telebot.types import ReplyKeyboardMarkup, KeyboardButton
from datetime import datetime

# Инициализация бота
bot = telebot.TeleBot("8157830738:AAENZ5upaAIkRe6EHmelbVi1iOKwpD_bOxo")

CHANNEL_USERNAME = "lolvalsvo"  # Публичный канал без "@"
MANAGERS_CHAT_ID = -1002505424671  # ID группы с менеджерами

user_data = {}

# Проверка подписки
def is_subscribed(user_id):
    try:
        member = bot.get_chat_member(f"@{CHANNEL_USERNAME}", user_id)
        return member.status in ['member', 'creator', 'administrator']
    except Exception as e:
        print("Ошибка при проверке подписки:", e)
        return False

# Старт
@bot.message_handler(commands=['start'])
def start(message):
    user_id = message.chat.id
    user_data[user_id] = {}

    if is_subscribed(user_id):
        choose_discount(user_id)
    else:
        markup = InlineKeyboardMarkup()
        markup.add(InlineKeyboardButton("✅ Подписаться на канал", url=f"https://t.me/{CHANNEL_USERNAME}"))
        bot.send_message(user_id,
                         f"Привет, <b>{message.from_user.first_name}</b>! Я бот <b>✨ОРГАНИК СПА✨</b> 🤗\n\n"
                         f"<b>Мы предлагаем скидки на массаж для подписчиков!</b>\n\n"
                         f"📢 Подпишитесь на наш канал: <b>@{CHANNEL_USERNAME}</b>\n"
                         f"Затем нажмите <b>/start</b> снова, чтобы продолжить.",
                         reply_markup=markup, parse_mode='HTML')

# Выбор скидки
def choose_discount(user_id):
    markup = InlineKeyboardMarkup(row_width=1)
    markup.add(
        InlineKeyboardButton("Скидка 15% на первое посещение", callback_data='discount_15'),
        InlineKeyboardButton("Балийский массаж со скидкой 35%", callback_data='discount_35')
    )
    bot.send_message(user_id,
                     "✅ Спасибо за подписку!\n\n"
                     "Чтобы закрепить скидку, ответьте, пожалуйста, на 3 вопроса 😊\n\n"
                     "<u>1. Вопрос:</u>\nКакое предложение вас интересует?",
                     reply_markup=markup, parse_mode='HTML')

# Обработка выбора скидки
@bot.callback_query_handler(func=lambda call: call.data.startswith("discount_"))
def handle_discount(call):
    user_id = call.message.chat.id
    if call.data == "discount_15":
        user_data[user_id]['discount'] = "Скидка 15% на первое посещение"
    elif call.data == "discount_35":
        user_data[user_id]['discount'] = "Балийский массаж со скидкой 35%"

    markup = InlineKeyboardMarkup(row_width=1)
    markup.add(
        InlineKeyboardButton("Через 3 дня", callback_data='time_3days'),
        InlineKeyboardButton("На этой неделе", callback_data='time_thisweek'),
        InlineKeyboardButton("На следующей неделе", callback_data='time_nextweek'),
        InlineKeyboardButton("В этом месяце", callback_data='time_month')
    )
    bot.edit_message_text(chat_id=user_id,
                          message_id=call.message.message_id,
                          text="<u>2. Вопрос:</u>\nКогда вы хотели бы посетить наш салон?\n\n📅 "
                               "Выберите удобный период (в дальнейшем менеджер свяжется с вами для уточнения)",
                          reply_markup=markup, parse_mode='HTML')

# Обработка выбора времени
@bot.callback_query_handler(func=lambda call: call.data.startswith("time_"))
def handle_time(call):
    user_id = call.message.chat.id
    time_map = {
        'time_3days': "Через 3 дня",
        'time_thisweek': "На этой неделе",
        'time_nextweek': "На следующей неделе",
        'time_month': "В этом месяце"
    }
    user_data[user_id]['visit_time'] = time_map.get(call.data, "Неизвестно")

    # bot.send_message(user_id,
    #                  "<u>3. Вопрос:</u>\nПодтверждение брони\n\n"
    #                  "📲 Напишите, пожалуйста, ваш номер телефона.\n"
    #                  "Отправьте его вручную, начиная с +7 или 8.\n\n"
    #                  "Менеджер подберёт удобную дату и запишет вас на процедуру с учётом скидки ✍️",
    #                  parse_mode='HTML')
    get_phone(call.message)

# Получение телефона
def get_phone(message):
    # user_data[message.chat.id]['visit_time'] = message.text
    markup = ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True)
    markup.add(KeyboardButton("📱 Поделиться номером", request_contact=True))
    bot.send_message(message.chat.id,
                     "<b>3. Вопрос:</b>\nПодтверждение брони\n\n"
                     "📲 Напишите, пожалуйста, ваш номер телефона.\n"
                     "Вы можете нажать кнопку <b>«Поделиться номером»</b> ниже 👇\n\n"
                     "Менеджер подберёт удобную дату и запишет вас на процедуру с учётом скидки ✍️",
                     reply_markup=markup, parse_mode='HTML')

# Обработка контакта
@bot.message_handler(content_types=['contact'])
def contact_handler(message):
    contact = message.contact.phone_number
    user_data[message.chat.id]['phone'] = contact if contact.startswith('+') else f"+{contact}"
    send_final_message(message)

# Обработка ручного ввода
@bot.message_handler(func=lambda m: m.chat.type == 'private')
def fallback(message):
    try:
        if ((message.text.startswith("+7") and len(message.text) == 12) or
                (message.text.startswith("8") and len(message.text) == 11)):
            user_data[message.chat.id]['phone'] = message.text
            send_final_message(message)
        else:
            bot.send_message(message.chat.id,
                             "⚠️ Пожалуйста, нажмите кнопку «Поделиться номером» или введите номер вручную.")
    except Exception as e:
        bot.send_message(message.chat.id,
                         "⚠️ Ошибка. Пожалуйста, повторите ввод номера.")
        print("Ошибка ввода номера", message.chat.id, e)

def save_user(user_id):
    with open("users.txt", "a", encoding="utf-8") as f:
        now = datetime.now()
        dt_string = now.strftime("%d/%m/%Y %H:%M:%S")
        f.write(f"{str(user_id)} {dt_string} \n")

# Финальное сообщение
def send_final_message(message):
    bot.send_message(message.chat.id,
                     f"🎉 Спасибо, <b>{message.from_user.first_name}</b>!\n\n"
                     f"Скидка закреплена за вами ✅\n"
                     f"Менеджер свяжется с вами в ближайшее время 📞\n\n"
                     f"До встречи в <b>ОРГАНИК СПА</b>! 🌿",
                     parse_mode='HTML',
                     reply_markup=ReplyKeyboardRemove())

    info = user_data[message.chat.id]
    save_user(info['phone'])
    full_text = (
        f"🆕 Новая заявка от @{message.from_user.username or message.from_user.first_name}:\n"
        f"Скидка: {info['discount']}\n"
        f"Дата визита: {info['visit_time']}\n"
        f"Телефон: {info['phone']}"
    )

    bot.send_message(MANAGERS_CHAT_ID, full_text)

# Запуск
print("Бот запущен")
bot.polling(none_stop=True)

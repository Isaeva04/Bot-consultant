import telebot
from telebot import types
import config
import webbrowser

bot = telebot.TeleBot(config.TOKEN)

# Словарь для хранения пользователей, ожидающих консультацию и их вопросов
consultations = {}

# Обработчик команды '/start'
@bot.message_handler(commands=['start'])
def send_welcome(message):
    markup = types.InlineKeyboardMarkup(row_width=1)
    button1 = types.InlineKeyboardButton('Получить консультацию', callback_data='get_consultation')
    button2 = types.InlineKeyboardButton('Перейти на сайт', callback_data='go_to_website')
    button3 = types.InlineKeyboardButton('Наши контакты', callback_data='our_contacts')
    markup.add(button1, button2, button3)
    bot.send_message(message.chat.id, config.welcome, reply_markup=markup)

# Обработчик для кнопок
@bot.callback_query_handler(func=lambda call: True)
def callback_handler(call):
    if call.data == 'get_consultation':
        bot.send_message(call.message.chat.id, "Опишите свой вопрос:")
        # Добавляем пользователя в словарь ожидающих консультацию с пустым вопросом
        consultations[call.message.chat.id] = ''
    elif call.data == 'our_contacts':
        markup = types.InlineKeyboardMarkup(row_width=1)
        button_office = types.InlineKeyboardButton('Офис на карте', callback_data='show_office_map')
        button_warehouse = types.InlineKeyboardButton('Склад на карте', callback_data='show_warehouse_map')
        markup.add(button_office, button_warehouse)
        bot.send_message(call.message.chat.id, config.contacts, reply_markup=markup)
    elif call.data == 'go_to_website':
        bot.send_message(call.message.chat.id, config.site)
        # Добавляем кнопку "Вернуться в главное меню" после отправки сайта
        markup = types.InlineKeyboardMarkup(row_width=1)
        button_return = types.InlineKeyboardButton('Вернуться на главное меню', callback_data='back_to_menu')
        markup.add(button_return)
        bot.send_message(call.message.chat.id, config.contacts, reply_markup=markup)
    elif call.data == 'show_office_map':
        markup = types.InlineKeyboardMarkup(row_width=1)
        button_warehouse = types.InlineKeyboardButton('Склад на карте', callback_data='show_warehouse_map')
        button_return = types.InlineKeyboardButton('Вернуться на главное меню', callback_data='back_to_menu')
        markup.add(button_warehouse, button_return)
        bot.send_location(call.message.chat.id, config.office_latitude, config.office_longitude, reply_markup=markup)
    elif call.data == 'show_warehouse_map':
        markup = types.InlineKeyboardMarkup(row_width=1)
        button_office = types.InlineKeyboardButton('Офис на карте', callback_data='show_office_map')
        button_return = types.InlineKeyboardButton('Вернуться на главное меню', callback_data='back_to_menu')
        markup.add(button_office, button_return)
        bot.send_location(call.message.chat.id, config.warehouse_latitude, config.warehouse_longitude,
                          reply_markup=markup)
    elif call.data == 'back_to_menu':
        send_welcome(call.message)

@bot.message_handler(content_types=['text', 'photo'], func=lambda message: message.chat.id in consultations)
def handle_consultation(message):
    # Получаем текстовое описание или фотографию
    if message.content_type == 'text':
        content = message.text
    elif message.content_type == 'photo':
        # Получаем ID самой большой по размеру фотографии
        photo_id = message.photo[-1].file_id
        content = f'[Фотография](https://api.telegram.org/file/bot{config.TOKEN}/{bot.get_file(photo_id).file_path})\n{message.caption}'
    # Получаем id пользователя, ожидающего консультацию
    user_id = message.chat.id
    user_name = message.from_user.first_name
    # Формируем ссылку на профиль пользователя
    user_profile_link = f'<a href="tg://user?id={user_id}">{user_name}</a>'
    # Сохраняем описание в словаре ожидающих консультацию
    consultations[user_id] = content
    # Оповещаем всех администраторов о новом вопросе с ссылкой на профиль пользователя
    for admin_id in config.admin_ids:
        bot.send_message(admin_id, f"Новый вопрос от пользователя {user_profile_link} (id: {user_id}):\n{content}", parse_mode='HTML')
    # Создаем inline-кнопку "Вернуться в главное меню"
    markup = types.InlineKeyboardMarkup(row_width=1)
    button_return = types.InlineKeyboardButton('Вернуться в главное меню', callback_data='back_to_menu')
    markup.add(button_return)
    # Оповещаем пользователя о том, что его вопрос получен
    bot.send_message(user_id, "Ваш вопрос получен. Ожидайте ответа в ближайшее время.", reply_markup=markup)

# Обработчик ответов от администратора
@bot.message_handler(func=lambda message: message.reply_to_message and message.reply_to_message.text.startswith("Новый вопрос от пользователя"))
def handle_admin_reply(message):
    # Получаем идентификатор чата пользователя, от которого был получен вопрос
    user_id = int(message.reply_to_message.text.split()[4][:-1])
    # Отправляем ответ администратора пользователю
    bot.send_message(user_id, message.text)
    # Оповещаем администратора об успешной отправке ответа
    bot.reply_to(message, "Ваш ответ успешно отправлен пользователю.")
    # Отправляем сообщение пользователю с заданным айди

# Запуск бота
bot.polling(none_stop=True)

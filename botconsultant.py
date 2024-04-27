import telebot
from telebot import types
import config

bot = telebot.TeleBot(config.TOKEN)


# Функция отправки уведомления об ошибке администраторам
def send_error_notification(error_message):
    for admin_id in config.admin_ids:
        bot.send_message(admin_id, error_message)


# Обработчик команды '/start'
@bot.message_handler(commands=['start'])
def send_welcome(message):
    markup = types.InlineKeyboardMarkup(row_width=1)
    button1 = types.InlineKeyboardButton('Получить консультацию', callback_data='get_consultation')
    button2 = types.InlineKeyboardButton('Перейти на сайт', callback_data='go_to_website')
    button3 = types.InlineKeyboardButton('Наши контакты', callback_data='our_contacts')
    markup.add(button1)
    markup.row(button2, button3)
    bot.send_message(message.chat.id, config.welcome, reply_markup=markup)


# Обработчик для кнопок
@bot.callback_query_handler(func=lambda call: True)
def callback_handler(call):
    try:
        if call.data == 'get_consultation':
            bot.send_message(call.message.chat.id, "Напишите свой вопрос в одном сообщении или прикрепите фотографию с вопросом в описании.")
        elif call.data == 'our_contacts':
            markup = types.InlineKeyboardMarkup(row_width=1)
            button_office = types.InlineKeyboardButton('Офис на карте', callback_data='show_office_map')
            button_warehouse = types.InlineKeyboardButton('Склад на карте', callback_data='show_warehouse_map')
            markup.row(button_office, button_warehouse)
            bot.send_message(call.message.chat.id, config.contacts, reply_markup=markup)
        elif call.data == 'go_to_website':
            markup = types.InlineKeyboardMarkup(row_width=1)
            button_return = types.InlineKeyboardButton('Вернуться на главное меню', callback_data='back_to_menu')
            markup.add(button_return)
            bot.send_message(call.message.chat.id, config.site)
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
    except BaseException as e:
        error_message_user = "Приносим свои извинения! Произошла какая-то ошибка. Попробуйте еще раз чуть позже."
        error_message_admin = "Произошла ошибка! Необходимо проверить работу бота."
        bot.send_message(call.message.chat.id, error_message_user)
        send_error_notification(error_message_admin)


@bot.message_handler(content_types=['text', 'photo'], func=lambda message: message.chat.id)
def handle_consultation(message):
    try:
        if message.content_type == 'text':
            content = message.text
        elif message.content_type == 'photo':
            photo_id = message.photo[-1].file_id
            content = f'[Фотография](https://api.telegram.org/file/bot{config.TOKEN}/{bot.get_file(photo_id).file_path})\n{message.caption}'
        user_id = message.chat.id
        user_name = message.from_user.first_name
        user_profile_link = f'<a href="tg://user?id={user_id}">{user_name}</a>'
        for admin_id in config.admin_ids:
            bot.send_message(admin_id, f"Новый вопрос от пользователя {user_profile_link} (id: {user_id}):\n{content}", parse_mode='HTML')
        markup = types.InlineKeyboardMarkup(row_width=1)
        button_new_question = types.InlineKeyboardButton('Еще вопрос', callback_data='get_consultation')
        button_return = types.InlineKeyboardButton('Вернуться в главное меню', callback_data='back_to_menu')
        markup.row(button_new_question,button_return)
        bot.send_message(user_id, "Ваш вопрос получен. Ожидайте ответа в ближайшее время.", reply_markup=markup)
    except BaseException as e:
        error_message_user = "Приносим свои извинения! Произошла какая-то ошибка. Попробуйте еще раз чуть позже."
        error_message_admin = "Произошла ошибка! Необходимо проверить работу бота."
        bot.send_message(user_id, error_message_user)
        send_error_notification(error_message_admin)

# Обработчик ответов от администратора
@bot.message_handler(func=lambda message: message.reply_to_message and message.reply_to_message.text.startswith("Новый вопрос от пользователя"))
def handle_admin_reply(message):
    try:
        user_id = int(message.reply_to_message.text.split()[6][:-2])
        user_question = " ".join(message.reply_to_message.text.split()[7:])
        response_text = f"Ваш вопрос: {user_question}\nОтвет нашего консультанта:\n{message.text}"
        bot.send_message(user_id, response_text, parse_mode='HTML')
        bot.reply_to(message.reply_to_message, f"Ваш ответ успешно отправлен пользователю {user_id}.")
    except BaseException as e:
        error_message_admin = "Произошла ошибка! Необходимо проверить работу бота."
        bot.send_message(message.chat.id, error_message_admin)
        send_error_notification(error_message_admin)


bot.polling(none_stop=True)
import warnings
import random
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, CallbackQueryHandler, ConversationHandler, \
    ContextTypes, filters

warnings.filterwarnings("ignore", category=UserWarning)

SELECT_CLASS, SELECT_TIME, SELECT_PICKUP_ADDRESS, SELECT_DROP_ADDRESS, SELECT_DETAILS, SELECT_PAYMENT, EDIT_ORDER, UPDATE_FIELD ,EDIT_CLASS = range(9)
def generate_order_number():
    return random.randint(100000, 999999)


def build_order_summary(context):
    return (f"🟢 Поиск водителя\n"
            f"Номер заказа: {context.user_data['order_number']}\n"
            f"• Дата и время: {context.user_data.get('time', 'не указано')}\n"
            f"• Автомобиль: {context.user_data.get('class', 'не указано')}\n"
            f"• Откуда: {context.user_data.get('pickup_address', 'не указано')}\n"
            f"• Куда: {context.user_data.get('drop_address', 'не указано')}\n"
            f"• Оплата: {context.user_data.get('payment', 'не указано')}\n"
            f"• Дополнительно: {context.user_data.get('details', 'не указано')}\n")


def build_keyboard(buttons):
    return InlineKeyboardMarkup([[InlineKeyboardButton(text, callback_data=callback)] for text, callback in buttons])


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    # Очищаем все данные пользователя при нажатии /start
    context.user_data.clear()

    # Генерируем новый номер заказа
    context.user_data['order_number'] = generate_order_number()

    # Приветственное сообщение
    welcome_message = (
        f"  👋Добро пожаловать!\n"
        f"  Ваш номер заказа: *{context.user_data['order_number']}*\n"
         "  Выберите класс автомобиля для вашей поездки:"
    )

    # Отправляем приветственное сообщение и предлагаем выбрать класс автомобиля
    await update.message.reply_text(
        welcome_message,
        reply_markup=build_keyboard([
            ("🚕 Стандарт", 'standard'),
            ("🚙 Комфорт", 'comfort'),
            ("🏎 Бизнес", 'business'),
            ("⭐️ Премиальный", 'premium'),
            ("🚐 Минивен", 'minivan'),
            ("💎 V-class", 'v_class')
        ]),
        parse_mode='Markdown'
    )
    return SELECT_CLASS

async def select_class(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data['class'] = update.callback_query.data
    await update.callback_query.answer()
    await update.callback_query.edit_message_text('📅 Когда вам нужна машина? Введите дату и время.')
    return SELECT_TIME

async def select_time(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data['time'] = update.message.text
    await update.message.reply_text('📍 Откуда вас забрать? Введите адрес.')
    return SELECT_PICKUP_ADDRESS

async def select_pickup_address(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data['pickup_address'] = update.message.text
    await update.message.reply_text('➡️ Куда вас отвезти? Введите адрес.')
    return SELECT_DROP_ADDRESS

async def select_drop_address(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data['drop_address'] = update.message.text
    await update.message.reply_text('📝 Укажите дополнительные пожелания.')
    return SELECT_DETAILS

async def select_details(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data['details'] = update.message.text
    await update.message.reply_text('💵 Укажите сумму заказа.')
    return SELECT_PAYMENT

async def select_payment(update: Update, context: ContextTypes.DEFAULT_TYPE):
    # Сохраняем значение оплаты, если оно уже установлено
    if 'payment' not in context.user_data:
        context.user_data['payment'] = update.message.text
    await update.message.reply_text(
        build_order_summary(context),
        reply_markup=build_keyboard([
            ("✅ Отправить заказ", 'confirm'),
            (" Редактировать класс автомобиля", 'edit_class'),
            (" Редактировать время", 'edit_time'),
            (" Редактировать адрес отправления", 'edit_pickup'),
            (" Редактировать адрес назначения", 'edit_drop'),
            (" Редактировать пожелания", 'edit_details'),
            (" Редактировать сумму", 'edit_payment')

        ])
    )
    return EDIT_ORDER

async def edit_order_field(update: Update, context: ContextTypes.DEFAULT_TYPE, field, prompt):
    query = update.callback_query
    await query.answer()
    await query.edit_message_text(prompt)
    context.user_data['edit_field'] = field
    return UPDATE_FIELD


async def edit_class(update: Update, context: ContextTypes.DEFAULT_TYPE):
    return await edit_order_field(update, context, 'class', '🚘 Пожалуйста, введите новый класс автомобиля: standard | comfort | minivan | business | premium | V class')

async def edit_time(update: Update, context: ContextTypes.DEFAULT_TYPE):
    return await edit_order_field(update, context, 'time', '📅 Пожалуйста, введите новое время и дату:')

async def edit_pickup(update: Update, context: ContextTypes.DEFAULT_TYPE):
    return await edit_order_field(update, context, 'pickup_address', '📍 Пожалуйста, введите новый адрес отправления:')

async def edit_drop(update: Update, context: ContextTypes.DEFAULT_TYPE):
    return await edit_order_field(update, context, 'drop_address', '➡️ Пожалуйста, введите новый адрес назначения:')

async def edit_details(update: Update, context: ContextTypes.DEFAULT_TYPE):
    return await edit_order_field(update, context, 'details', '📝 Пожалуйста, введите новые пожелания:')

async def edit_payment(update: Update, context: ContextTypes.DEFAULT_TYPE):
    return await edit_order_field(update, context, 'payment', '💵 Пожалуйста, введите новую сумму:')

async def update_order_field(update: Update, context: ContextTypes.DEFAULT_TYPE):
    new_value = update.message.text
    field = context.user_data['edit_field']
    # Обновляем только изменяемое поле
    if field in context.user_data:
        context.user_data[field] = new_value
    await update.message.reply_text('✅ Заказ изменен.')
    return await select_payment(update, context)


orders = []  # Список для хранения заказов
order_counter = 0  # Счетчик заказов

async def confirm_order(update: Update, context: ContextTypes.DEFAULT_TYPE):
    global order_counter
    query = update.callback_query
    order_summary = build_order_summary(context)

    # Создаем новый заказ и сохраняем его
    order_counter += 1
    new_order = {
        'order_number': order_counter,
        'client_chat_id': update.effective_chat.id,
        'status': 'В ожидании водителя',
        'summary': order_summary
    }
    orders.append(new_order)

    CHANNEL_ID = -1002477998663  # Укажите свой ID канала
    keyboard = [[InlineKeyboardButton("🚗 Принять заказ", callback_data=f'accept_order_{order_counter}')]]
    reply_markup = InlineKeyboardMarkup(keyboard)

    # Добавляем текст-подсказку в сообщение
    await context.bot.send_message(
        chat_id=CHANNEL_ID,
        text=f"{order_summary}\n\nℹ️ Нажмите кнопку, чтобы принять заказ:",
        reply_markup=reply_markup
    )
    await query.edit_message_text('Ваш заказ отправлен в канал! 🎉')

    print(f"client_chat_id установлен: {new_order['client_chat_id']}")  # Отладочная информация
    return ConversationHandler.END


async def accept_order(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    order_number = int(query.data.split('_')[2])

    # Находим заказ по номеру
    for order in orders:
        if order['order_number'] == order_number and order['status'] == 'В ожидании водителя':
            order['status'] = 'Принят'
            context.user_data['driver_chat_id'] = update.effective_chat.id
            driver_username = query.from_user.username
            client_chat_id = order['client_chat_id']

            # Сохраняем идентификатор водителя и номер заказа
            context.user_data['driver_chat_id'] = update.effective_chat.id
            context.user_data['order_number'] = order_number  # Сохраняем номер заказа

            # Просто отправляем окно с кнопкой отмены, без сообщений
            await context.bot.send_message(
                chat_id=update.effective_chat.id,
                text=f'{order["summary"]}\n\n ℹ️ Нажмите кнопку, чтобы отменить заказ:',
                reply_markup=InlineKeyboardMarkup(
                    [[InlineKeyboardButton("❌ Отменить заказ", callback_data=f'cancel_order_{order_number}')]]
                )
            )

            await context.bot.send_message(chat_id=client_chat_id, text=f'🚖 Водитель @{driver_username} принял ваш заказ #{order_number}!')
            await query.delete_message()  # Удаляем сообщение о принятии заказа
            break
    else:
        await query.answer('Ошибка: Заказ не найден или уже принят.')


async def cancel_order(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    order_number = int(query.data.split('_')[2])
    # Находим заказ и отменяем его
    for order in orders:
        if order['order_number'] == order_number:
            # Проверяем, является ли текущий водитель тем, кто принял заказ
            if context.user_data.get('driver_chat_id') == update.effective_chat.id:
                order['status'] = 'В ожидании водителя'  # Меняем статус на 'В ожидании водителя'
                client_chat_id = order['client_chat_id']

                await context.bot.send_message(
                    chat_id=client_chat_id,
                    text="🛑 Ваш заказ отменен. Ищем другого водителя."
                )

                # Отправляем новый запрос в канал
                await context.bot.send_message(
                    chat_id=-1002477998663,
                    text=f"{order['summary']}\n\nℹ️ Нажмите кнопку, чтобы принять заказ:",
                    reply_markup=InlineKeyboardMarkup(
                        [[InlineKeyboardButton("🚗 Принять заказ", callback_data=f'accept_order_{order_number}')]]
                    )
                )

                # Удаляем сообщение о нажатии кнопки "Отменить"
                await query.delete_message()  # Удаляем сообщение о нажатии кнопки "Отменить"

                return  # Завершаем обработку

            else:
                await query.answer('Ошибка: У вас нет разрешения на отмену этого заказа.')
            break
    else:
        await query.answer('Ошибка: Заказ не найден.')



def main():
    application = ApplicationBuilder().token("7214937350:AAH-CIKNwXmVod8FQwSGQS4vGVGqRKzTwGc").build()

    conv_handler = ConversationHandler(
        entry_points=[CommandHandler('start', start)],
        states={
            SELECT_CLASS: [CallbackQueryHandler(select_class)],
            SELECT_TIME: [MessageHandler(filters.TEXT & ~filters.COMMAND, select_time)],
            SELECT_PICKUP_ADDRESS: [MessageHandler(filters.TEXT & ~filters.COMMAND, select_pickup_address)],
            SELECT_DROP_ADDRESS: [MessageHandler(filters.TEXT & ~filters.COMMAND, select_drop_address)],
            SELECT_DETAILS: [MessageHandler(filters.TEXT & ~filters.COMMAND, select_details)],
            SELECT_PAYMENT: [MessageHandler(filters.TEXT & ~filters.COMMAND, select_payment)],
            EDIT_ORDER: [CallbackQueryHandler(edit_class, pattern='edit_class'),
                         CallbackQueryHandler(edit_time, pattern='edit_time'),
                         CallbackQueryHandler(edit_pickup, pattern='edit_pickup'),
                         CallbackQueryHandler(edit_drop, pattern='edit_drop'),
                         CallbackQueryHandler(edit_details, pattern='edit_details'),
                         CallbackQueryHandler(edit_payment, pattern='edit_payment'),
                         CallbackQueryHandler(confirm_order, pattern='confirm')],

            UPDATE_FIELD: [MessageHandler(filters.TEXT & ~filters.COMMAND, update_order_field)],
        },
        fallbacks=[CommandHandler('start', start)]
    )

    application.add_handler(conv_handler)
    application.add_handler(CallbackQueryHandler(accept_order, pattern='accept_order'))
    application.add_handler(CallbackQueryHandler(cancel_order, pattern='cancel_order'))

    application.run_polling()


if __name__ == '__main__':
    main()
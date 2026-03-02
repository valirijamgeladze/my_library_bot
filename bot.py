import logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    Application, CommandHandler, MessageHandler,
    filters, ContextTypes, ConversationHandler, CallbackQueryHandler
)

from config import BOT_TOKEN
from database import Database
from keyboards import *

# Настройка логирования
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Создаем базу данных
db = Database()

# Состояния для разговора
TITLE, AUTHOR = range(2)
EDIT_TITLE, EDIT_AUTHOR = range(2, 4)

# Хранилище для текущей страницы и фильтра пользователя
user_states = {}


def get_filter_name(filter_status):
    filters = {
        None: "📚 Все книги",
        'Хочу прочитать': "🟢 Хочу прочитать",
        'Читаю': "🟡 Читаю",
        'Прочитано': "✅ Прочитано"
    }
    return filters.get(filter_status, "📚 Книги")

def get_empty_filter_message(filter_status):
    messages = {
        None: "📚 У тебя пока нет книг",
        'Хочу прочитать': "🟢 Нет книг в списке 'Хочу прочитать'",
        'Читаю': "🟡 Ты ничего не читаешь сейчас",
        'Прочитано': "✅ Ты ещё не прочитал ни одной книги"
    }
    return messages.get(filter_status, "📚 Книг не найдено")

def clear_user_state(user_id):

    if user_id in user_states:
        del user_states[user_id]




async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    logger.info(f"Пользователь {user.id} (@{user.username}) запустил бота")

    await update.message.reply_text(
        f"📚 Привет, {user.first_name}!\n\n"
        "Я помогу тебе хранить список книг.\n\n"
        "📖 **Добавить книгу** — начать ввод\n"
        "📚 **Мои книги** — посмотреть список\n"
        "❌ **Отмена** — прервать любой процесс",
        parse_mode='Markdown',
        reply_markup=get_main_keyboard()
    )

async def cancel_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    logger.info(f"Пользователь {user.id} отменил действие")

    context.user_data.clear()
    clear_user_state(user.id)

    await update.message.reply_text(
        "❌ Действие отменено. Возвращаюсь в главное меню.",
        reply_markup=get_main_keyboard()
    )
    return ConversationHandler.END




async def add_book_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    logger.info(f"Пользователь начал добавлять книгу")
    await update.message.reply_text(
        "📖 Введи **название** книги:",
        parse_mode='Markdown',
        reply_markup=get_cancel_keyboard()
    )
    return TITLE

async def add_book_title(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text
    if text == '❌ Отмена':
        return await cancel_add(update, context)

    context.user_data['title'] = text
    logger.info(f"Пользователь ввёл название: {text}")

    await update.message.reply_text(
        "✍️ Теперь введи **автора** (или '-' если не знаешь):",
        parse_mode='Markdown',
        reply_markup=get_cancel_keyboard()
    )
    return AUTHOR

async def add_book_author(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text

    if text == '❌ Отмена':
        return await cancel_add(update, context)

    user_id = update.effective_user.id
    title = context.user_data.get('title')

    if not title:
        logger.error("Нет названия в user_data!")
        await update.message.reply_text(
            "❌ Что-то пошло не так. Начни заново.",
            reply_markup=get_main_keyboard()
        )
        context.user_data.clear()
        return ConversationHandler.END

    author = None if text == '-' else text
    logger.info(f"Сохраняем книгу: {title} - {author}")

    try:
        book_id = db.add_book(user_id, title, author)
        logger.info(f"Книга сохранена с ID {book_id}")

        stats = db.get_book_stats(user_id)

        await update.message.reply_text(
            f"✅ **Книга сохранена!**\n\n"
            f"📖 *{title}*\n"
            f"✍️ {author if author else 'Автор не указан'}\n\n"
            f"📊 **Статистика:**\n"
            f"📚 Всего: {stats['total']}",
            parse_mode='Markdown',
            reply_markup=get_main_keyboard()
        )
    except Exception as e:
        logger.error(f"Ошибка при сохранении: {e}")
        await update.message.reply_text(
            "❌ Ошибка при сохранении. Попробуй ещё раз.",
            reply_markup=get_main_keyboard()
        )

    context.user_data.clear()
    return ConversationHandler.END

async def cancel_add(update: Update, context: ContextTypes.DEFAULT_TYPE):
    logger.info("Пользователь отменил добавление")
    context.user_data.clear()
    await update.message.reply_text(
        "❌ Добавление отменено.",
        reply_markup=get_main_keyboard()
    )
    return ConversationHandler.END

# === ПРОСМОТР КНИГ ===

async def show_books(update: Update, context: ContextTypes.DEFAULT_TYPE, filter_status=None):
    user_id = update.effective_user.id
    is_callback = update.callback_query is not None

    # Обновляем состояние пользователя
    if filter_status is not None:
        user_states[user_id] = {'filter': filter_status, 'page': 0}
    elif user_id not in user_states:
        user_states[user_id] = {'filter': None, 'page': 0}

    filter_status = user_states[user_id]['filter']
    page = user_states[user_id]['page']

    books = db.get_user_books(user_id, filter_status)

    # Если книг нет
    if not books:
        empty_message = get_empty_filter_message(filter_status)
        if is_callback:
            await update.callback_query.edit_message_text(
                f"{empty_message}\n\nНажми '📖 Добавить книгу'!",
                reply_markup=None
            )
            await context.bot.send_message(
                chat_id=user_id,
                text="Выбери действие:",
                reply_markup=get_main_keyboard()
            )
        else:
            await update.message.reply_text(
                f"{empty_message}\n\nНажми '📖 Добавить книгу'!",
                reply_markup=get_main_keyboard()
            )
        return

    # Пагинация
    books_per_page = 10
    total_pages = (len(books) + books_per_page - 1) // books_per_page
    filter_name = get_filter_name(filter_status)

    header = f"{filter_name} (стр. {page + 1}/{total_pages})\n\n"

    start = page * books_per_page
    message = header
    for i, book in enumerate(books[start:start + books_per_page], start=1):
        title = book[2]
        author = book[3]
        author_text = f" — {author}" if author else ""
        message += f"{start + i}. {title}{author_text}\n"

    keyboard = get_books_list_keyboard(books, page, total_pages, books_per_page)

    # Отправка/обновление сообщения
    if is_callback:
        try:
            await update.callback_query.edit_message_text(
                message,
                parse_mode='Markdown',
                reply_markup=keyboard
            )
        except Exception as e:
            if "Message is not modified" not in str(e):
                logger.error(f"Ошибка при редактировании: {e}")
                await context.bot.send_message(
                    chat_id=user_id,
                    text=message,
                    parse_mode='Markdown',
                    reply_markup=keyboard
                )
    else:
        await update.message.reply_text(
            message,
            parse_mode='Markdown',
            reply_markup=keyboard
        )

async def show_book_details(update: Update, context: ContextTypes.DEFAULT_TYPE, book_id):
    query = update.callback_query
    book = db.get_book_by_id(book_id)

    if not book:
        await query.edit_message_text("❌ Книга не найдена")
        return

    title, author, status, date_added = book[2], book[3], book[4], book[5][:10]

    status_emoji = {
        'Хочу прочитать': '🟢',
        'Читаю': '🟡',
        'Прочитано': '✅'
    }.get(status, '📖')

    message = (
        f"📖 **{title}**\n"
        f"✍️ {author if author else 'Автор не указан'}\n"
        f"{status_emoji} Статус: {status}\n"
        f"📅 Добавлена: {date_added}\n"
    )

    await query.edit_message_text(
        message,
        parse_mode='Markdown',
        reply_markup=get_book_actions_keyboard(book_id, status)
    )




async def edit_book_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    book_id = int(query.data.split('_')[1])
    book = db.get_book_by_id(book_id)

    if not book:
        await query.edit_message_text("❌ Книга не найдена")
        return ConversationHandler.END

    context.user_data['editing_book_id'] = book_id
    context.user_data['original_title'] = book[2]
    context.user_data['original_author'] = book[3] if book[3] else ''

    empty_keyboard = InlineKeyboardMarkup([[]])

    await query.edit_message_text(
        f"✏️ **Редактирование книги**\n\n"
        f"Текущее название: *{book[2]}*\n\n"
        f"Введи **новое название** (или отправь '.' чтобы оставить текущее):",
        parse_mode='Markdown',
        reply_markup=empty_keyboard
    )

    return EDIT_TITLE

async def edit_book_title(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text

    if text == '❌ Отмена':
        return await cancel_edit(update, context)

    new_title = context.user_data.get('original_title') if text == '.' else text
    context.user_data['new_title'] = new_title

    original_author = context.user_data.get('original_author', '')
    author_display = original_author if original_author else 'не указан'

    await update.message.reply_text(
        f"✏️ Текущий автор: *{author_display}*\n\n"
        f"Введи **нового автора** (или отправь '.' чтобы оставить текущего, или '-' если автора нет):",
        parse_mode='Markdown',
        reply_markup=get_cancel_keyboard()
    )

    return EDIT_AUTHOR

async def edit_book_author(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text

    if text == '❌ Отмена':
        return await cancel_edit(update, context)

    book_id = context.user_data.get('editing_book_id')
    new_title = context.user_data.get('new_title')
    original_author = context.user_data.get('original_author', '')

    # Определяем нового автора
    if text == '.':
        new_author = original_author
    elif text == '-':
        new_author = None
    else:
        new_author = text

    db.update_book(book_id, new_title, new_author)
    book = db.get_book_by_id(book_id)

    context.user_data.clear()

    keyboard = InlineKeyboardMarkup([
        [InlineKeyboardButton("📖 Показать книгу", callback_data=f"book_{book_id}")],
        [InlineKeyboardButton("◀️ К списку книг", callback_data="back_to_list")]
    ])

    await update.message.reply_text(
        f"✅ **Книга обновлена!**\n\n"
        f"📖 *{book[2]}*\n"
        f"✍️ {book[3] if book[3] else 'Автор не указан'}",
        parse_mode='Markdown',
        reply_markup=keyboard
    )

    return ConversationHandler.END

async def cancel_edit(update: Update, context: ContextTypes.DEFAULT_TYPE):
    logger.info("Пользователь отменил редактирование")
    context.user_data.clear()
    await update.message.reply_text(
        "❌ Редактирование отменено.",
        reply_markup=get_main_keyboard()
    )
    return ConversationHandler.END




async def button_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    user_id = update.effective_user.id
    data = query.data

    logger.info(f"Пользователь {user_id} нажал кнопку: {data}")

    # Пагинация
    if data.startswith('page_'):
        page = int(data.split('_')[1])
        if user_id in user_states:
            user_states[user_id]['page'] = page
        current_filter = user_states.get(user_id, {}).get('filter', None)
        await show_books(update, context, current_filter)

    # Фильтры
    elif data.startswith('filter_'):
        filter_map = {
            'filter_all': None,
            'filter_want': 'Хочу прочитать',
            'filter_reading': 'Читаю',
            'filter_read': 'Прочитано'
        }
        if data in filter_map:
            user_states[user_id] = {'filter': filter_map[data], 'page': 0}
            await show_books(update, context, filter_map[data])

    # Навигация
    elif data in ['back_to_list', 'back_to_all']:
        new_filter = user_states.get(user_id, {}).get('filter', None) if data == 'back_to_list' else None
        if data == 'back_to_all':
            user_states[user_id] = {'filter': None, 'page': 0}
        await show_books(update, context, new_filter)

    # Детали книги
    elif data.startswith('book_'):
        book_id = int(data.split('_')[1])
        await show_book_details(update, context, book_id)

    # Смена статуса
    elif data.startswith('status_'):
        await handle_status_change(update, context, data)

    # Удаление
    elif data.startswith('delete_') and not data.startswith('confirm_delete_') and not data.startswith('cancel_delete_'):
        await handle_delete_request(update, context, data)

    # Подтверждение удаления
    elif data.startswith('confirm_delete_'):
        await handle_delete_confirmation(update, context, data)

    # Отмена удаления
    elif data.startswith('cancel_delete_'):
        await handle_delete_cancel(update, context, data)

    # Редактирование
    elif data.startswith('edit_'):
        await edit_book_start(update, context)

async def handle_status_change(update: Update, context: ContextTypes.DEFAULT_TYPE, data: str):
    parts = data.split('_')
    status = parts[1]
    book_id = int(parts[2])

    status_map = {
        'want': 'Хочу прочитать',
        'reading': 'Читаю',
        'read': 'Прочитано'
    }
    new_status = status_map[status]

    db.update_book_status(book_id, new_status)
    book = db.get_book_by_id(book_id)

    keyboard = InlineKeyboardMarkup([
        [InlineKeyboardButton("📚 К списку (текущий фильтр)", callback_data="back_to_list")],
        [InlineKeyboardButton("📋 Ко всем книгам", callback_data="back_to_all")]
    ])

    await update.callback_query.edit_message_text(
        f"✅ Статус изменён на '{new_status}'!\n\n"
        f"📖 *{book[2]}*\n"
        f"✍️ {book[3] if book[3] else 'Автор не указан'}",
        parse_mode='Markdown',
        reply_markup=keyboard
    )

async def handle_delete_request(update: Update, context: ContextTypes.DEFAULT_TYPE, data: str):
    book_id = int(data.split('_')[1])
    book = db.get_book_by_id(book_id)

    if book:
        await update.callback_query.edit_message_text(
            f"🗑️ **Удалить книгу?**\n\n"
            f"📖 *{book[2]}*\n"
            f"✍️ {book[3] if book[3] else 'Автор не указан'}\n\n"
            f"Точно удалить?",
            parse_mode='Markdown',
            reply_markup=get_delete_confirmation_keyboard(book_id)
        )

async def handle_delete_confirmation(update: Update, context: ContextTypes.DEFAULT_TYPE, data: str):
    book_id = int(data.split('_')[2])
    user_id = update.effective_user.id

    db.delete_book(book_id)
    user_states[user_id] = {'filter': None, 'page': 0}

    await update.callback_query.edit_message_text(
        "✅ Книга удалена!",
        reply_markup=InlineKeyboardMarkup([[
            InlineKeyboardButton("📚 К списку книг", callback_data="back_to_all")
        ]])
    )

async def handle_delete_cancel(update: Update, context: ContextTypes.DEFAULT_TYPE, data: str):
    book_id = int(data.split('_')[2])
    await show_book_details(update, context, book_id)




async def handle_main_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text
    user = update.effective_user

    logger.info(f"Пользователь {user.id} нажал: {text}")

    menu_actions = {
        '📖 Добавить книгу': lambda: add_book_start(update, context) if not context.user_data else update.message.reply_text(
            "Ты уже добавляешь книгу! Сначала заверши или отмени.",
            reply_markup=get_cancel_keyboard()
        ),
        '📚 Мои книги': lambda: show_books(update, context),
        '🏷️ Категории': lambda: update.message.reply_text(
            "🏷️ **Категории**\n\nСкоро появятся! 🚧",
            parse_mode='Markdown',
            reply_markup=get_main_keyboard()
        ),
        '📊 Статистика': lambda: update.message.reply_text(
            (lambda stats: (
                f"📊 **Твоя читательская статистика**\n\n"
                f"📚 **Всего книг:** {stats['total']}\n"
                f"🟢 **Хочу прочитать:** {stats['Хочу прочитать']}\n"
                f"🟡 **Читаю сейчас:** {stats['Читаю']}\n"
                f"✅ **Прочитано:** {stats['Прочитано']} ({stats['read_percent']}%)\n\n"
                f"{stats['top_authors_text']}"
            ))(db.get_book_stats(user.id)),
            parse_mode='Markdown',
            reply_markup=get_main_keyboard()
        ),
        '❓ Помощь': lambda: update.message.reply_text(
            "📖 **Как пользоваться:**\n\n"
            "• **Добавить книгу** — ввести название и автора\n"
            "• **Мои книги** — посмотреть список, менять статусы, удалять\n"
            "• Нажми на книгу в списке, чтобы увидеть детали\n"
            "• Там можно изменить статус или удалить\n"
            "• **Отмена** — прервать добавление\n"
            "• **/cancel** — тоже отмена",
            parse_mode='Markdown',
            reply_markup=get_main_keyboard()
        ),
        '❌ Отмена': lambda: update.message.reply_text(
            "❌ Нечего отменять.",
            reply_markup=get_main_keyboard()
        )
    }

    if text in menu_actions:
        result = menu_actions[text]()
        if result is not None and hasattr(result, '__await__'):
            return await result

    return None


def main():
    application = Application.builder().token(BOT_TOKEN).build()

    # Диалог добавления книги
    add_conv_handler = ConversationHandler(
        entry_points=[MessageHandler(filters.Regex('^📖 Добавить книгу$'), add_book_start)],
        states={
            TITLE: [MessageHandler(filters.TEXT & ~filters.COMMAND, add_book_title)],
            AUTHOR: [MessageHandler(filters.TEXT & ~filters.COMMAND, add_book_author)],
        },
        fallbacks=[
            CommandHandler('cancel', cancel_command),
            MessageHandler(filters.Regex('^❌ Отмена$'), cancel_add)
        ],
    )

    # Диалог редактирования книги
    edit_conv_handler = ConversationHandler(
        entry_points=[CallbackQueryHandler(edit_book_start, pattern='^edit_')],
        states={
            EDIT_TITLE: [MessageHandler(filters.TEXT & ~filters.COMMAND, edit_book_title)],
            EDIT_AUTHOR: [MessageHandler(filters.TEXT & ~filters.COMMAND, edit_book_author)],
        },
        fallbacks=[
            CommandHandler('cancel', cancel_command),
            MessageHandler(filters.Regex('^❌ Отмена$'), cancel_edit)
        ],
    )


    application.add_handler(CommandHandler('start', start))
    application.add_handler(CommandHandler('cancel', cancel_command))
    application.add_handler(add_conv_handler)
    application.add_handler(edit_conv_handler)
    application.add_handler(CallbackQueryHandler(button_callback))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_main_menu))

    logger.info("🚀 Бот запущен!")
    print("Бот запущен! Нажми Ctrl+C для остановки.")
    application.run_polling()

if __name__ == '__main__':
    main()
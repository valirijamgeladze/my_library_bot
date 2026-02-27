from telegram import ReplyKeyboardMarkup, InlineKeyboardMarkup, InlineKeyboardButton

# Кнопки главного меню
def get_main_keyboard():
    keyboard = [
        ['📖 Добавить книгу', '📚 Мои книги'],
        ['🏷️ Категории', '📊 Статистика'],
        ['❓ Помощь']
    ]
    return ReplyKeyboardMarkup(keyboard, resize_keyboard=True)

# Кнопка отмены при добавлении книги
def get_cancel_keyboard():
    keyboard = [
        ['❌ Отмена']
    ]
    return ReplyKeyboardMarkup(keyboard, resize_keyboard=True)

# Кнопка вывода списка книг
def get_books_list_keyboard(books, page=0, total_pages=1, books_per_page=10):
    keyboard = []

    # Добавление книг на текущую страницу
    start = page * books_per_page
    for book in books[start:start + books_per_page]:
        book_id = book[0]
        title = book[2]
        author = book[3]
        status = book[4]

        # Эмодзи для статуса
        status_emoji = {
            'Хочу прочитать': '🟢',
            'Читаю': '🟡',
            'Прочитано': '✅'
        }.get(status, '📖')

        # Обрезка названий
        short_title = title[:30] + "..." if len(title) > 30 else title
        button_text = f"{status_emoji} {short_title}"

        keyboard.append([InlineKeyboardButton(button_text, callback_data=f"book_{book_id}")])

    # Кнопки навигации
    nav_buttons = []
    if page > 0:
        nav_buttons.append(InlineKeyboardButton("◀️ Назад", callback_data=f"page_{page - 1}"))
    if page < total_pages - 1:
        nav_buttons.append(InlineKeyboardButton("Вперёд ▶️", callback_data=f"page_{page + 1}"))

    if nav_buttons:
        keyboard.append(nav_buttons)

    # Кнопки фильтров
    keyboard.append([
        InlineKeyboardButton("🟢 Хочу", callback_data="filter_want"),
        InlineKeyboardButton("🟡 Читаю", callback_data="filter_reading"),
        InlineKeyboardButton("✅ Прочитано", callback_data="filter_read")
    ])

    keyboard.append([InlineKeyboardButton("🔄 Все книги", callback_data="filter_all")])

    return InlineKeyboardMarkup(keyboard)

# Взаимодействие с конкретной книгой
def get_book_actions_keyboard(book_id, current_status):
    keyboard = []

    # Кнопки для изменения статуса
    status_buttons = []

    if current_status != 'Хочу прочитать':
        status_buttons.append(InlineKeyboardButton("🟢 Хочу", callback_data=f"status_want_{book_id}"))
    if current_status != 'Читаю':
        status_buttons.append(InlineKeyboardButton("🟡 Читаю", callback_data=f"status_reading_{book_id}"))
    if current_status != 'Прочитано':
        status_buttons.append(InlineKeyboardButton("✅ Прочитано", callback_data=f"status_read_{book_id}"))

    if status_buttons:
        keyboard.append(status_buttons)

    keyboard.append([InlineKeyboardButton("✏️ Редактировать книгу", callback_data=f"edit_{book_id}")])

    keyboard.append([InlineKeyboardButton("🗑️ Удалить книгу", callback_data=f"delete_{book_id}")])

    keyboard.append([InlineKeyboardButton("◀️ Назад к списку", callback_data="back_to_list")])

    return InlineKeyboardMarkup(keyboard)

# Подтверждение удаления книги
def get_delete_confirmation_keyboard(book_id):
    keyboard = [
        [
            InlineKeyboardButton("✅ Да, удалить", callback_data=f"confirm_delete_{book_id}"),
            InlineKeyboardButton("❌ Нет", callback_data=f"cancel_delete_{book_id}")
        ]
    ]
    return InlineKeyboardMarkup(keyboard)
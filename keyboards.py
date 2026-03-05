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

    keyboard.append([InlineKeyboardButton("🏷️ Управлять категориями", callback_data=f"book_categories_{book_id}")])

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

def get_categories_main_keyboard():
    """Главное меню управления категориями"""
    keyboard = [
        [InlineKeyboardButton("📋 Список категорий", callback_data="categories_list")],
        [InlineKeyboardButton("➕ Создать категорию", callback_data="category_create")],
        [InlineKeyboardButton("📚 Книги без категорий", callback_data="books_without_cats")],
        [InlineKeyboardButton("◀️ Назад в главное меню", callback_data="back_to_main")]
    ]
    return InlineKeyboardMarkup(keyboard)


def get_categories_list_keyboard(categories, page=0, total_pages=1):
    """Клавиатура со списком категорий"""
    keyboard = []

    # Категории на текущей странице
    start = page * 5
    for cat in categories[start:start + 5]:
        cat_id = cat[0]
        name = cat[1]
        color = cat[2]
        count = cat[3]

        button_text = f"{color} {name} ({count})"
        keyboard.append([InlineKeyboardButton(button_text, callback_data=f"category_view_{cat_id}")])

    # Навигация
    nav_buttons = []
    if page > 0:
        nav_buttons.append(InlineKeyboardButton("◀️ Назад", callback_data=f"cat_page_{page - 1}"))
    if page < total_pages - 1:
        nav_buttons.append(InlineKeyboardButton("Вперёд ▶️", callback_data=f"cat_page_{page + 1}"))

    if nav_buttons:
        keyboard.append(nav_buttons)

    keyboard.append([InlineKeyboardButton("➕ Создать категорию", callback_data="category_create")])
    keyboard.append([InlineKeyboardButton("◀️ Назад", callback_data="categories_menu")])

    return InlineKeyboardMarkup(keyboard)


def get_category_actions_keyboard(category_id):
    """Клавиатура действий с категорией"""
    keyboard = [
        [
            InlineKeyboardButton("✏️ Переименовать", callback_data=f"category_rename_{category_id}"),
            InlineKeyboardButton("🎨 Сменить цвет", callback_data=f"category_color_{category_id}")
        ],
        [
            InlineKeyboardButton("📚 Книги в категории", callback_data=f"category_books_{category_id}"),
            InlineKeyboardButton("➕ Добавить книги", callback_data=f"category_add_books_{category_id}")
        ],
        [InlineKeyboardButton("🗑️ Удалить категорию", callback_data=f"category_delete_{category_id}")],
        [InlineKeyboardButton("◀️ Назад к списку", callback_data="categories_list")]
    ]
    return InlineKeyboardMarkup(keyboard)


def get_books_for_category_keyboard(books, category_id, page=0, total_pages=1, selected=None):
    """Клавиатура для выбора книг в категорию"""
    if selected is None:
        selected = set()

    keyboard = []
    start = page * 5

    for book in books[start:start + 5]:
        book_id = book[0]
        title = book[1]
        author = book[2] if len(book) > 2 else ""

        author_text = f" — {author}" if author else ""
        display_text = f"{title}{author_text}"
        short_text = display_text[:30] + "..." if len(display_text) > 30 else display_text

        # Отмечаем выбранные книги
        checkbox = "✅ " if book_id in selected else ""
        callback = f"cat_toggle_{category_id}_{book_id}"

        keyboard.append([InlineKeyboardButton(f"{checkbox}{short_text}", callback_data=callback)])

    # Навигация
    nav_buttons = []
    if page > 0:
        nav_buttons.append(InlineKeyboardButton("◀️ Назад", callback_data=f"cat_book_page_{category_id}_{page - 1}"))
    if page < total_pages - 1:
        nav_buttons.append(InlineKeyboardButton("Вперёд ▶️", callback_data=f"cat_book_page_{category_id}_{page + 1}"))

    if nav_buttons:
        keyboard.append(nav_buttons)

    # Кнопки действий
    action_row = []
    if selected:
        action_row.append(InlineKeyboardButton(f"✅ Добавить выбранные ({len(selected)})",
                                               callback_data=f"cat_add_selected_{category_id}"))
    action_row.append(InlineKeyboardButton("❌ Отмена", callback_data=f"category_view_{category_id}"))

    keyboard.append(action_row)

    return InlineKeyboardMarkup(keyboard)


def get_color_choice_keyboard(category_id):
    """Клавиатура для выбора цвета категории"""
    colors = [
        ["📁", "📘", "📗", "📕"],
        ["🔴", "🟠", "🟡", "🟢"],
        ["🔵", "🟣", "⚫", "⚪"],
        ["❤️", "🧡", "💛", "💚"],
        ["💙", "💜", "🖤", "🤍"]
    ]

    keyboard = []
    for row in colors:
        button_row = []
        for color in row:
            button_row.append(InlineKeyboardButton(color, callback_data=f"cat_setcolor_{category_id}_{color}"))
        keyboard.append(button_row)

    keyboard.append([InlineKeyboardButton("◀️ Назад", callback_data=f"category_view_{category_id}")])

    return InlineKeyboardMarkup(keyboard)


def get_book_categories_keyboard(book_id, categories, book_cats):
    """Клавиатура для управления категориями книги"""
    book_cats_set = set(book_cats)
    keyboard = []

    for cat in categories:
        cat_id = cat[0]
        name = cat[1]
        color = cat[2]

        # Отмечаем, если книга уже в этой категории
        mark = "✅ " if cat_id in book_cats_set else ""
        callback = f"book_toggle_cat_{book_id}_{cat_id}"

        keyboard.append([InlineKeyboardButton(f"{mark}{color} {name}", callback_data=callback)])

    keyboard.append([InlineKeyboardButton("➕ Создать новую категорию", callback_data=f"book_create_cat_{book_id}")])
    keyboard.append([InlineKeyboardButton("✅ Готово", callback_data=f"book_back_{book_id}")])

    return InlineKeyboardMarkup(keyboard)
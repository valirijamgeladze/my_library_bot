import sqlite3
import logging

logger = logging.getLogger(__name__)


class Database:
    def __init__(self, db_name='books.db'):
        self.db_name = db_name
        self.init_db()

    def get_connection(self):
        return sqlite3.connect(self.db_name)

    def init_db(self):
        """Создаёт таблицы, если их нет"""
        conn = self.get_connection()
        cursor = conn.cursor()

        # Таблица для книг
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS books (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                title TEXT NOT NULL,
                author TEXT,
                status TEXT DEFAULT 'Хочу прочитать',
                date_added TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')

        # НОВОЕ: Таблица для категорий
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS categories (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                name TEXT NOT NULL,
                color TEXT DEFAULT '📁',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                UNIQUE(user_id, name)
            )
        ''')

        # НОВОЕ: Таблица связи книг и категорий (многие ко многим)
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS book_categories (
                book_id INTEGER,
                category_id INTEGER,
                assigned_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                PRIMARY KEY (book_id, category_id),
                FOREIGN KEY (book_id) REFERENCES books (id) ON DELETE CASCADE,
                FOREIGN KEY (category_id) REFERENCES categories (id) ON DELETE CASCADE
            )
        ''')

        conn.commit()
        conn.close()
        logger.info("База данных готова")


    def add_book(self, user_id, title, author=None):
        conn = self.get_connection()
        cursor = conn.cursor()

        cursor.execute('''
            INSERT INTO books (user_id, title, author)
            VALUES (?, ?, ?)
        ''', (user_id, title, author))

        book_id = cursor.lastrowid
        conn.commit()
        conn.close()

        logger.info(f"Книга добавлена: user={user_id}, title={title}")
        return book_id

    # Получение книг пользователя
    def get_user_books(self, user_id, status=None):
        conn = self.get_connection()
        cursor = conn.cursor()

        if status:
            cursor.execute('''
                SELECT id, user_id, title, author, status, date_added 
                FROM books 
                WHERE user_id = ? AND status = ?
                ORDER BY title COLLATE NOCASE ASC  -- Сортировка по алфавиту
            ''', (user_id, status))
        else:
            cursor.execute('''
                SELECT id, user_id, title, author, status, date_added 
                FROM books 
                WHERE user_id = ?
                ORDER BY title COLLATE NOCASE ASC  -- Сортировка по алфавиту
            ''', (user_id,))

        books = cursor.fetchall()
        conn.close()

        logger.info(f"Получено книг для user={user_id}: {len(books)}")
        return books

    def update_book_status(self, book_id, new_status):
        conn = self.get_connection()
        cursor = conn.cursor()

        cursor.execute('''
            UPDATE books 
            SET status = ? 
            WHERE id = ?
        ''', (new_status, book_id))

        conn.commit()
        conn.close()

        logger.info(f"Статус книги {book_id} изменён на {new_status}")
        return True

    def delete_book(self, book_id):
        conn = self.get_connection()
        cursor = conn.cursor()

        cursor.execute('DELETE FROM books WHERE id = ?', (book_id,))

        conn.commit()
        conn.close()

        logger.info(f"Книга {book_id} удалена")
        return True

    def get_book_stats(self, user_id):
        """Получает статистику по книгам пользователя"""
        conn = self.get_connection()
        cursor = conn.cursor()

        # Общее количество
        cursor.execute('SELECT COUNT(*) FROM books WHERE user_id = ?', (user_id,))
        total = cursor.fetchone()[0]

        # Количество по статусам
        cursor.execute('''
            SELECT status, COUNT(*) 
            FROM books 
            WHERE user_id = ? 
            GROUP BY status
        ''', (user_id,))
        stats = {status: count for status, count in cursor.fetchall()}

        # Процент прочитанных книг
        read_count = stats.get('Прочитано', 0)
        read_percent = round((read_count / total * 100), 1) if total > 0 else 0

        # Топ авторы
        cursor.execute('''
            WITH author_counts AS (
                SELECT 
                    author, 
                    COUNT(*) as count
                FROM books 
                WHERE user_id = ? AND author IS NOT NULL AND author != ''
                GROUP BY author
            ),
            max_count AS (
                SELECT MAX(count) as max_count FROM author_counts
            )
            SELECT 
                ac.author,
                ac.count
            FROM author_counts ac, max_count mc
            WHERE ac.count = mc.max_count AND mc.max_count > 1
            ORDER BY ac.author
        ''', (user_id,))

        top_authors = cursor.fetchall()

        if not top_authors:
            top_authors_text = ""
        elif len(top_authors) == 1:
            top_authors_text = f"🏆 **Любимый автор:** {top_authors[0][0]} ({top_authors[0][1]} книг)"
        else:
            authors_list = ", ".join([a[0] for a in top_authors])
            top_authors_text = f"🏆 **Любимые авторы:** {authors_list} ({top_authors[0][1]} книг)"

        conn.close()

        return {
            'total': total,
            'Хочу прочитать': stats.get('Хочу прочитать', 0),
            'Читаю': stats.get('Читаю', 0),
            'Прочитано': read_count,
            'read_percent': read_percent,
            'top_authors_text': top_authors_text,
        }

    def get_book_by_id(self, book_id):
        conn = self.get_connection()
        cursor = conn.cursor()

        cursor.execute('''
            SELECT id, user_id, title, author, status, date_added 
            FROM books 
            WHERE id = ?
        ''', (book_id,))

        book = cursor.fetchone()
        conn.close()

        return book

    def update_book(self, book_id, new_title, new_author):
        conn = self.get_connection()
        cursor = conn.cursor()

        cursor.execute('''
            UPDATE books 
            SET title = ?, author = ?
            WHERE id = ?
        ''', (new_title, new_author, book_id))

        conn.commit()
        conn.close()

        logger.info(f"Книга {book_id} обновлена: {new_title} - {new_author}")
        return True


    def create_category(self, user_id, name, color='📁'):
        """Создаёт новую категорию"""
        conn = self.get_connection()
        cursor = conn.cursor()

        try:
            cursor.execute('''
                    INSERT INTO categories (user_id, name, color)
                    VALUES (?, ?, ?)
                ''', (user_id, name, color))
            conn.commit()
            category_id = cursor.lastrowid
            logger.info(f"Категория создана: user={user_id}, name={name}")
            return category_id
        except sqlite3.IntegrityError:
            logger.warning(f"Категория уже существует: {name}")
            return None
        finally:
            conn.close()

    def get_user_categories(self, user_id):
        """Получает все категории пользователя с количеством книг"""
        conn = self.get_connection()
        cursor = conn.cursor()

        cursor.execute('''
                SELECT 
                    c.id, 
                    c.name, 
                    c.color,
                    COUNT(bc.book_id) as book_count
                FROM categories c
                LEFT JOIN book_categories bc ON c.id = bc.category_id
                WHERE c.user_id = ?
                GROUP BY c.id
                ORDER BY c.name
            ''', (user_id,))

        categories = cursor.fetchall()
        conn.close()
        return categories

    def get_category_by_id(self, category_id):
        """Получает категорию по ID"""
        conn = self.get_connection()
        cursor = conn.cursor()

        cursor.execute('''
                SELECT id, user_id, name, color, created_at
                FROM categories
                WHERE id = ?
            ''', (category_id,))

        category = cursor.fetchone()
        conn.close()
        return category

    def update_category(self, category_id, new_name, new_color=None):
        """Обновляет название и цвет категории"""
        conn = self.get_connection()
        cursor = conn.cursor()

        if new_color:
            cursor.execute('''
                    UPDATE categories
                    SET name = ?, color = ?
                    WHERE id = ?
                ''', (new_name, new_color, category_id))
        else:
            cursor.execute('''
                    UPDATE categories
                    SET name = ?
                    WHERE id = ?
                ''', (new_name, category_id))

        conn.commit()
        conn.close()
        logger.info(f"Категория {category_id} обновлена: {new_name}")
        return True

    def delete_category(self, category_id):
        """Удаляет категорию (связи с книгами удаляются автоматически)"""
        conn = self.get_connection()
        cursor = conn.cursor()

        cursor.execute('DELETE FROM categories WHERE id = ?', (category_id,))
        conn.commit()
        conn.close()
        logger.info(f"Категория {category_id} удалена")
        return True

    def add_book_to_category(self, book_id, category_id):
        """Добавляет книгу в категорию"""
        conn = self.get_connection()
        cursor = conn.cursor()

        try:
            cursor.execute('''
                    INSERT OR IGNORE INTO book_categories (book_id, category_id)
                    VALUES (?, ?)
                ''', (book_id, category_id))
            conn.commit()
            return True
        except Exception as e:
            logger.error(f"Ошибка при добавлении книги в категорию: {e}")
            return False
        finally:
            conn.close()

    def remove_book_from_category(self, book_id, category_id):
        """Удаляет книгу из категории"""
        conn = self.get_connection()
        cursor = conn.cursor()

        cursor.execute('''
                DELETE FROM book_categories
                WHERE book_id = ? AND category_id = ?
        ''', (book_id, category_id))

        conn.commit()
        conn.close()
        return True

    def get_book_categories(self, book_id):
        """Получает все категории книги"""
        conn = self.get_connection()
        cursor = conn.cursor()

        cursor.execute('''
                SELECT c.id, c.name, c.color
                FROM categories c
                JOIN book_categories bc ON c.id = bc.category_id
                WHERE bc.book_id = ?
                ORDER BY c.name
            ''', (book_id,))

        categories = cursor.fetchall()
        conn.close()
        return categories

    def get_books_by_category(self, user_id, category_id):
        """Получает все книги в категории"""
        conn = self.get_connection()
        cursor = conn.cursor()

        cursor.execute('''
                SELECT b.id, b.user_id, b.title, b.author, b.status, b.date_added
                FROM books b
                JOIN book_categories bc ON b.id = bc.book_id
                WHERE b.user_id = ? AND bc.category_id = ?
                ORDER BY b.title
            ''', (user_id, category_id))

        books = cursor.fetchall()
        conn.close()
        return books

    def add_books_to_category_mass(self, book_ids, category_id):
        """Добавляет несколько книг в категорию за один раз"""
        conn = self.get_connection()
        cursor = conn.cursor()

        for book_id in book_ids:
            try:
                cursor.execute('''
                        INSERT OR IGNORE INTO book_categories (book_id, category_id)
                        VALUES (?, ?)
                    ''', (book_id, category_id))
            except Exception as e:
                logger.error(f"Ошибка при добавлении книги {book_id}: {e}")

        conn.commit()
        conn.close()
        return True

    def get_books_without_category(self, user_id):
        """Получает книги без категорий"""
        conn = self.get_connection()
        cursor = conn.cursor()

        cursor.execute('''
                SELECT b.id, b.title, b.author
                FROM books b
                LEFT JOIN book_categories bc ON b.id = bc.book_id
                WHERE b.user_id = ? AND bc.category_id IS NULL
                ORDER BY b.title
            ''', (user_id,))

        books = cursor.fetchall()
        conn.close()
        return books

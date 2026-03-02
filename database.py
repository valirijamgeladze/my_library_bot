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
        conn = self.get_connection()
        cursor = conn.cursor()

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
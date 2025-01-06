import sqlite3
import string
import random

def generate_referral_code(length=8):
    """Генерирует уникальный реферальный код"""
    characters = string.ascii_letters + string.digits
    return ''.join(random.choice(characters) for _ in range(length))

def create_database():
    try:
        conn = sqlite3.connect('users.db')
        c = conn.cursor()

        # Проверяем существование таблицы users
        c.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='users'")
        users_exists = c.fetchone() is not None

        if users_exists:
            # Если таблица существует, создаем новую с обновленной структурой
            c.execute('''
            CREATE TABLE users_new (
                user_id TEXT PRIMARY KEY,
                username TEXT,
                first_name TEXT,
                verified INTEGER DEFAULT 0,
                balance INTEGER DEFAULT 0,
                referral_code TEXT UNIQUE
            )''')

            # Копируем существующие данные
            c.execute('SELECT user_id, username, first_name, verified, balance FROM users')
            for row in c.fetchall():
                while True:
                    referral_code = generate_referral_code()
                    try:
                        c.execute('''
                        INSERT INTO users_new (user_id, username, first_name, verified, balance, referral_code)
                        VALUES (?, ?, ?, ?, ?, ?)
                        ''', (*row, referral_code))
                        break
                    except sqlite3.IntegrityError:
                        continue

            # Заменяем старую таблицу новой
            c.execute('DROP TABLE users')
            c.execute('ALTER TABLE users_new RENAME TO users')
        else:
            # Если таблицы нет, создаем новую
            c.execute('''
            CREATE TABLE users (
                user_id TEXT PRIMARY KEY,
                username TEXT,
                first_name TEXT,
                verified INTEGER DEFAULT 0,
                balance INTEGER DEFAULT 0,
                referral_code TEXT UNIQUE
            )''')

        # Создаем таблицу для рефералов
        c.execute('''
        CREATE TABLE IF NOT EXISTS referrals (
            referral_id TEXT,
            referrer_id TEXT,
            joined_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            reward INTEGER DEFAULT 0,
            status TEXT DEFAULT 'active',
            FOREIGN KEY (referral_id) REFERENCES users (user_id),
            FOREIGN KEY (referrer_id) REFERENCES users (user_id),
            PRIMARY KEY (referral_id)
        )''')

        # Создаем таблицу для выполненных заданий
        c.execute('''
        CREATE TABLE IF NOT EXISTS completed_tasks (
            user_id TEXT,
            task_id INTEGER,
            completed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            PRIMARY KEY (user_id, task_id)
        )''')

        conn.commit()
        conn.close()
        print("База данных успешно обновлена!")
        
    except Exception as e:
        print(f"Ошибка при создании базы данных: {e}")
        if conn:
            conn.close()

if __name__ == "__main__":
    create_database()
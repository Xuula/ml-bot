import sqlite3

'''
connection = sqlite3.connect('db/users.db')
cursor = connection.cursor()

cursor.execute('
    CREATE TABLE IF NOT EXISTS Users (
    id INTEGER PRIMARY KEY,
    tokens INTEGER)
')
'''


class Database:
    def __init__(self):
        self._connection = sqlite3.connect('db/users.db')
        self._cursor = self._connection.cursor()

    def set_tokens(self, user, tokens):
        self._cursor.execute("""
            INSERT OR REPLACE INTO Users (id, tokens)
            VALUES (?, ?)
        """, (user, tokens))
        self._connection.commit()

    def get_tokens(self, user):
        self._cursor.execute("""
            SELECT tokens FROM users WHERE id = ?
        """, (user,))
        result = self._cursor.fetchone()
        return result[0] if result else None

    def user_exists(self, user):
        self._cursor.execute("""
            SELECT 1 FROM users WHERE id = ?
        """, (user,))
        return self._cursor.fetchone() is not None

    def create_user(self, user, tokens=0):
        if not self.user_exists(user):
            self.set_tokens(user, tokens)

    def __del__(self):
        self._connection.close()

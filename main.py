from datetime import datetime

import psycopg2
from psycopg2 import sql


class DatabaseConn:
    def __init__(self, dbname, user, password, host='localhost', port=5432) -> None:
        self.dbname = dbname
        self.user = user
        self.password = password
        self.host = host
        self.port = port
        self.connection = None
        self.cursor = None
        self.firstrequest = True

    def connect(self):
        #try to connection to db
        try:
            self.connection = psycopg2.connect(
                dbname=self.dbname,
                user=self.user,
                password=self.password,
                host=self.host,
                port=self.port
            )
            self.cursor = self.connection.cursor()
            if self.firstrequest:
                print("[✓]Подключение к базе данных PostgreSQL установлено.")
                self.firstrequest = False
        except Exception as error:
            print(f"[X]Ошибка подключения: {error}")

    def create_user_table(self):
        self.cursor.execute("""
            CREATE TABLE IF NOT EXISTS users (
                    id SERIAL PRIMARY KEY,
                    name TEXT,
                    surname TEXT,
                    balance REAL
            );"""
        )
        self.connection.commit()
        print(f"[C]Таблица users создана")

    def create_transaction_table(self):
        self.cursor.execute("""
            CREATE TABLE IF NOT EXISTS transactions (
                    id SERIAL PRIMARY KEY,
                    summa REAL,
                    time TIMESTAMP,
                    category_id INTEGER REFERENCES categories(id)
            );"""
        )
        self.connection.commit()
        print(f"[C]Таблица transactions создана")

    def create_category_table(self):
        self.cursor.execute("""
            CREATE TABLE IF NOT EXISTS categories (
                id SERIAL PRIMARY KEY,
                name TEXT UNIQUE NOT NULL
            );"""
        )
        self.connection.commit()
        print(f"[C]Таблица categories создана")

class User:
    def __init__(self, db_connection, name: str, surname:str, balance: float) -> None:
        #super().__init__(db_connection.dbname, db_connection.user, db_connection.password, db_connection.host, db_connection.port) можно через super но пока понятней именно так.
        self.name = name
        self.surname = surname
        self.balance = balance

        self.db_connection = db_connection
        self.db_connection.connect()

    def save_users_table(self):
        cursor = self.db_connection.cursor
        try:
            cursor.execute("SELECT id FROM users WHERE name = %s AND surname = %s", (self.name, self.surname))
            result = cursor.fetchone() #False если пользователя не существует

            if result: #обновляем данные
                cursor.execute("""
                    UPDATE users SET balance = %s WHERE name = %s AND surname = %s
                """, (self.balance, self.name, self.surname))
                print(f"[↻]Пользователь {self.name} обновлен в базе данных")
            else:
                cursor.execute(
                sql.SQL("""
                    INSERT INTO users (name, surname, balance)
                    VALUES (%s, %s, %s);
                """), (self.name, self.surname, self.balance)
                )
                print(f"[+]Пользователь {self.name} добавлен в Базу данных")

            self.db_connection.connection.commit()
        except Exception as error:
            self.db_connection.connection.rollback() #откат создания пользователя в случае ошибки
            print(f"[X]Ошибка при сохранении пользователя: {error}")

class Transaction:  
    # Он включает все необходимые параметры, 
    # такие как сумма, тип транзакции (доход или расход), дата и категория.
    def __init__(self, db_connection, summa: float, time: datetime, *category_id: tuple) -> None:
        #super().__init__(db_connection.dbname, db_connection.user, db_connection.password, db_connection.host, db_connection.port) можно через super но пока понятней именно так.
        self.summa = summa
        self.time = time
        self.category_id = category_id

        self.db_connection = db_connection
        self.db_connection.connect()

    def save_transactions_table(self):
        cursor = self.db_connection.cursor
        try:
            cursor.execute(
            sql.SQL("""
                INSERT INTO transactions (summa, time, category_id)
                VALUES (%s, %s, %s);
            """), (self.summa, self.time, self.category_id)
            )
            print(f"[+]Транзакция добавлена в Базу данных")

            self.db_connection.connection.commit()
        except Exception as error:
            self.db_connection.connection.rollback() #откат транзацкции в случае ошибки
            print(f"[X]Ошибка при сохранении транзакции: {error}") 

class Category:
    # Этот класс будет хранить информацию о категориях расходов или доходов,
    # таких как "еда", "транспорт", "зарплата", и другие.
    def __init__(self, db_connection, name: str) -> None:
        self.name = name
        self.db_connection = db_connection
        self.db_connection.connect()

    def save_category(self):
        cursor = self.db_connection.cursor
        try:
            cursor.execute(
                sql.SQL("""
            INSERT INTO categories (name)
            VALUES (%s) ON CONFLICT (name) DO NOTHING;
            """), (self.name,)
            )
            print(f"[+]Категория добавлена в Базу данных")
            self.db_connection.connection.commit()
        except Exception as error:
            self.db_connection.connection.rollback()
            print(f"[X]Ошибка при сохранении категории: {error}") 

    def get_category_id(self, category_name: str):
        cursor = self.db_connection.cursor
        cursor.execute("SELECT id FROM categories WHERE name = %s", (category_name,))
        return cursor.fetchone()

all_categories = ["Развлечения", "Фастфуд", "Услуги банка", "Переводы", "Супермаркеты",
                "Транспорт", "Маркетплейсы", "Снятие наличных", "Одежда", "Подписки",
                "Билеты", "Образование", "Коммунальные услуги", "Медицина", "Другое"]

db = DatabaseConn("finance_db", "postgres", "-", "localhost")
db.connect()
db.create_user_table()
db.create_category_table()
[Category(db, category).save_category() for category in all_categories] #добавление в БД всех категорий
db.create_transaction_table()

user1 = User(db, "Sergey", "Hopin", "30000.0")
user1.save_users_table()

transaction1 = Transaction(db, 2000.0, datetime.now(), Category(db, "-").get_category_id("Одежда"))
transaction1.save_transactions_table()





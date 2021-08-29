import sqlite3

from telegram import chat

from config import DB_FILE

con = sqlite3.connect(DB_FILE, check_same_thread=False)


def create_tables():
    cur = con.cursor()

    cur.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id          INTEGER PRIMARY KEY,
            username    TEXT,
            name        TEXT
        )
    """)

    cur.execute("""
        CREATE TABLE IF NOT EXISTS wallets (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id     INTEGER NOT NULL,
            name        TEXT,
            address     TEXT NOT NULL,
            latest_block INTEGER DEFAULT 0,
            balance     TEXT,
            chat_id     INTEGER NOT NULL
        )
    """)
    cur.close()
    con.commit()


def add_user(id: int, username: str, name: str = None):
    cur = con.cursor()
    cur.execute(
        "INSERT INTO users VALUES (?, ?, ?)",
        (id, username, name)
    )
    cur.close()
    con.commit()


def delete_user(id):
    cur = con.cursor()
    cur.execute("DELETE FROM users WHERE id = ?", (id,))
    cur.close()
    con.commit()


def check_user_exists(id: int):
    cur = con.cursor()
    cur.execute(
        "SELECT id FROM users WHERE id = ?",
        (id,)
    )

    result = cur.fetchone()

    return True if result is not None else False


def get_all_users():
    cur = con.cursor()
    cur.execute("SELECT * FROM users")

    return cur.fetchall()


def add_wallet(user_id, name, address, latest_block, chat_id):
    cur = con.cursor()
    cur.execute(
        "INSERT INTO wallets(user_id, name, address, latest_block, balance, chat_id) VALUES (?, ?, ?, ?, ?, ?)",
        (user_id, name, address, latest_block, "0", chat_id)
    )
    cur.close()
    con.commit()


def check_wallet_exists(user_id, address, chat_id):
    cur = con.cursor()
    cur.execute(
        "SELECT * FROM wallets WHERE user_id = ? AND address = ? AND chat_id=?", (user_id, address, chat_id))

    result = cur.fetchone()

    return True if result is not None else False

def check_wallet_id_and_user_exists(id, user_id):
    cur = con.cursor()
    cur.execute(
        "SELECT * FROM wallets WHERE id = ? AND user_id = ?", (id, user_id))

    result = cur.fetchone()

    return True if result is not None else False

def delete_wallet(id):
    cur = con.cursor()
    cur.execute(
        "DELETE FROM wallets WHERE id = ?", (id,))
    cur.close()
    con.commit()

def get_user_wallets(user_id, chat_id):
    cur = con.cursor()
    cur.execute("SELECT * FROM wallets WHERE user_id = ? AND chat_id=? ORDER BY id", (user_id, chat_id))

    return cur.fetchall()

def get_all_wallets():
    cur = con.cursor()
    cur.execute("SELECT * FROM wallets ORDER BY user_id", ())

    return cur.fetchall()


def update_latest_block(user_id, address, latest_block, chat_id):
    cur = con.cursor()
    cur.execute("UPDATE wallets SET latest_block = ? WHERE user_id=? AND address = ? AND chat_id=?",
                (latest_block, user_id, address, chat_id))
    cur.close()
    con.commit()             

def update_all_latest_block(latest_block):
    cur = con.cursor()
    cur.execute("UPDATE wallets SET latest_block = ?",
                (latest_block,))
    cur.close()
    con.commit() 

create_tables()

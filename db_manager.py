# import sqlite3
# import hashlib

# def init_db():
#     conn = sqlite3.connect("users.db")
#     c = conn.cursor()
#     # Create Users table
#     c.execute('''CREATE TABLE IF NOT EXISTS users 
#                  (username TEXT PRIMARY KEY, password TEXT)''')
#     # Create Chat table
#     c.execute('''CREATE TABLE IF NOT EXISTS chat_history 
#                  (username TEXT, role TEXT, content TEXT, timestamp DATETIME DEFAULT CURRENT_TIMESTAMP)''')
#     conn.commit()
#     conn.close()

# def hash_password(password):
#     return hashlib.sha256(str.encode(password)).hexdigest()

# def add_user(username, password):
#     conn = sqlite3.connect("users.db")
#     c = conn.cursor()
#     try:
#         c.execute("INSERT INTO users (username, password) VALUES (?, ?)", (username, hash_password(password)))
#         conn.commit()
#         return True
#     except sqlite3.IntegrityError:
#         return False
#     finally:
#         conn.close()

# def check_user(username, password):
#     conn = sqlite3.connect("users.db")
#     c = conn.cursor()
#     c.execute("SELECT * FROM users WHERE username=? AND password=?", (username, hash_password(password)))
#     result = c.fetchone()
#     conn.close()
#     return result

# def save_message(username, role, content):
#     conn = sqlite3.connect("users.db")
#     c = conn.cursor()
#     c.execute("INSERT INTO chat_history (username, role, content) VALUES (?, ?, ?)", (username, role, content))
#     conn.commit()
#     conn.close()

# def get_chat_history(username):
#     conn = sqlite3.connect("users.db")
#     c = conn.cursor()
#     c.execute("SELECT role, content FROM chat_history WHERE username=? ORDER BY timestamp ASC", (username,))
#     history = [{"role": row[0], "content": row[1]} for row in c.fetchall()]
#     conn.close()
#     return history


import sqlite3
import hashlib
import json


# =========================
# DB INIT
# =========================
def init_db():
    conn = sqlite3.connect("users.db")
    c = conn.cursor()

    # Users
    c.execute('''
        CREATE TABLE IF NOT EXISTS users (
            username TEXT PRIMARY KEY,
            password TEXT
        )
    ''')

    # Chat sessions
    c.execute('''
        CREATE TABLE IF NOT EXISTS chat_sessions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT,
            title TEXT,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    ''')

    # ✅ UPDATED: added charts column
    c.execute('''
        CREATE TABLE IF NOT EXISTS chat_history (
            chat_id INTEGER,
            role TEXT,
            content TEXT,
            charts TEXT,
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    ''')

    conn.commit()
    conn.close()


# =========================
# AUTH
# =========================
def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()


def add_user(username, password):
    conn = sqlite3.connect("users.db")
    c = conn.cursor()

    try:
        c.execute(
            "INSERT INTO users VALUES (?, ?)",
            (username, hash_password(password))
        )
        conn.commit()
        return True
    except:
        return False
    finally:
        conn.close()


def check_user(username, password):
    conn = sqlite3.connect("users.db")
    c = conn.cursor()

    c.execute(
        "SELECT * FROM users WHERE username=? AND password=?",
        (username, hash_password(password))
    )

    result = c.fetchone()
    conn.close()
    return result


# =========================
# CHAT FUNCTIONS
# =========================
def create_chat(username, title="New Chat"):
    conn = sqlite3.connect("users.db")
    c = conn.cursor()

    c.execute(
        "INSERT INTO chat_sessions (username, title) VALUES (?, ?)",
        (username, title)
    )

    conn.commit()
    chat_id = c.lastrowid
    conn.close()

    return chat_id


def get_user_chats(username):
    conn = sqlite3.connect("users.db")
    c = conn.cursor()

    c.execute(
        "SELECT id, title FROM chat_sessions WHERE username=? ORDER BY created_at DESC",
        (username,)
    )

    chats = c.fetchall()
    conn.close()
    return chats


def get_chat_messages(chat_id):
    conn = sqlite3.connect("users.db")
    c = conn.cursor()

    c.execute(
        "SELECT role, content, charts FROM chat_history WHERE chat_id=? ORDER BY timestamp ASC",
        (chat_id,)
    )

    messages = []
    for role, content, charts in c.fetchall():

        msg = {"role": role, "content": content}

        if charts:
            msg["charts"] = json.loads(charts)

        messages.append(msg)

    conn.close()
    return messages


# ✅ UPDATED: supports charts
def save_message(chat_id, role, content, charts=None):
    conn = sqlite3.connect("users.db")
    c = conn.cursor()

    charts_json = json.dumps(charts) if charts else None

    c.execute(
        "INSERT INTO chat_history (chat_id, role, content, charts) VALUES (?, ?, ?, ?)",
        (chat_id, role, content, charts_json)
    )

    conn.commit()
    conn.close()


def update_chat_title(chat_id, title):
    conn = sqlite3.connect("users.db")
    c = conn.cursor()

    c.execute(
        "UPDATE chat_sessions SET title=? WHERE id=?",
        (title, chat_id)
    )

    conn.commit()
    conn.close()
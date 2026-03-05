import sqlite3
import hashlib

def init_db():
    conn = sqlite3.connect("users.db")
    c = conn.cursor()
    # Create Users table
    c.execute('''CREATE TABLE IF NOT EXISTS users 
                 (username TEXT PRIMARY KEY, password TEXT)''')
    # Create Chat table
    c.execute('''CREATE TABLE IF NOT EXISTS chat_history 
                 (username TEXT, role TEXT, content TEXT, timestamp DATETIME DEFAULT CURRENT_TIMESTAMP)''')
    conn.commit()
    conn.close()

def hash_password(password):
    return hashlib.sha256(str.encode(password)).hexdigest()

def add_user(username, password):
    conn = sqlite3.connect("users.db")
    c = conn.cursor()
    try:
        c.execute("INSERT INTO users (username, password) VALUES (?, ?)", (username, hash_password(password)))
        conn.commit()
        return True
    except sqlite3.IntegrityError:
        return False
    finally:
        conn.close()

def check_user(username, password):
    conn = sqlite3.connect("users.db")
    c = conn.cursor()
    c.execute("SELECT * FROM users WHERE username=? AND password=?", (username, hash_password(password)))
    result = c.fetchone()
    conn.close()
    return result

def save_message(username, role, content):
    conn = sqlite3.connect("users.db")
    c = conn.cursor()
    c.execute("INSERT INTO chat_history (username, role, content) VALUES (?, ?, ?)", (username, role, content))
    conn.commit()
    conn.close()

def get_chat_history(username):
    conn = sqlite3.connect("users.db")
    c = conn.cursor()
    c.execute("SELECT role, content FROM chat_history WHERE username=? ORDER BY timestamp ASC", (username,))
    history = [{"role": row[0], "content": row[1]} for row in c.fetchall()]
    conn.close()
    return history
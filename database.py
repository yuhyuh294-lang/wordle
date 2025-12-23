import sqlite3
import json

DB_NAME = "games.db"

def init_db():
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute("""
        CREATE TABLE IF NOT EXISTS games (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT,
            mode TEXT,
            answer TEXT,
            turns INTEGER,
            win INTEGER,
            history TEXT
        )
    """)
    conn.commit()
    conn.close()

def save_game(username, mode, answer, turns, win, history):
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute("""
        INSERT INTO games (username, mode, answer, turns, win, history)
        VALUES (?, ?, ?, ?, ?, ?)
    """, (
        username,
        mode,
        answer,
        turns,
        win,
        json.dumps(history, ensure_ascii=False)
    ))
    conn.commit()
    conn.close()

def get_user_games(username):
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute("""
        SELECT mode, answer, turns, win, history
        FROM games
        WHERE username = ?
        ORDER BY id DESC
    """, (username,))
    rows = c.fetchall()
    conn.close()

    return [
        {
            "mode": r[0],
            "answer": r[1],
            "turns": r[2],
            "win": bool(r[3]),
            "history": json.loads(r[4])
        }
        for r in rows
    ]
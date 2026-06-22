import sqlite3
import os

db_path = 'instance/greenshield.db'
if os.path.exists(db_path):
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    try:
        cursor.execute("SELECT username, email FROM user")
        users = cursor.fetchall()
        print(f"Users: {users}")
        cursor.execute("SELECT name FROM disease")
        names = [row[0] for row in cursor.fetchall()]
        print(f"Disease names: {names}")
    except Exception as e:
        print(f"Error: {e}")
    finally:
        conn.close()
else:
    print(f"Database not found at {db_path}")

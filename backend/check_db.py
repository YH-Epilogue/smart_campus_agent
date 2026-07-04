import sqlite3
conn = sqlite3.connect(r'E:\实训\smart_campus_agent\backend\data\sqlite.db')
tables = [r[0] for r in conn.execute("SELECT name FROM sqlite_master WHERE type='table'").fetchall()]
print("Tables:", tables)
users = conn.execute("SELECT * FROM users").fetchall()
print("Users:", users)
conn.close()

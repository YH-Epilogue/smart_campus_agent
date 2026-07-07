import sqlite3
conn = sqlite3.connect(r"E:\实训\smart_campus_agent\backend\data\sqlite.db")
conn.execute("UPDATE users SET role = 'teacher' WHERE username = 'zzl'")
conn.commit()
rows = conn.execute("SELECT username, role FROM users").fetchall()
for u, r in rows:
    print(f"  {u}: {r}")
conn.close()

"""迁移用户角色：admin 保持，其余改为 student"""
import sqlite3

db_path = r"E:\实训\smart_campus_agent\backend\data\sqlite.db"
conn = sqlite3.connect(db_path)

users = conn.execute("SELECT id, username, role FROM users").fetchall()
for uid, uname, role in users:
    if role == "user":
        new_role = "student"
        conn.execute("UPDATE users SET role = ? WHERE id = ?", (new_role, uid))
        print(f"  {uname}: {role} -> {new_role}")
    else:
        print(f"  {uname}: {role} (保持)")

conn.commit()
conn.close()
print("Done!")

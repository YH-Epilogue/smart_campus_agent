"""
迁移已有用户密码为新的哈希格式
"""
import sqlite3
import hashlib

SECRET_KEY = "smart-campus-agent-dev-secret-key"
db_path = r"E:\实训\smart_campus_agent\backend\data\sqlite.db"
conn = sqlite3.connect(db_path)

users = conn.execute("SELECT id, username, hashed_password FROM users").fetchall()
print(f"Found {len(users)} users")

for user_id, username, old_hash in users:
    # Check if already migrated (new format contains $)
    if "$" in old_hash:
        print(f"  {username}: already migrated, skipping")
        continue

    # Try common passwords with old hash
    test_passwords = ["123456", "admin", "password", "admin123"]
    found_password = None
    for pwd in test_passwords:
        old_check = hashlib.sha256((pwd + "smart-campus-agent-dev-secret-key").encode()).hexdigest()
        if old_check == old_hash:
            found_password = pwd
            break

    if found_password:
        # Create new hash with salt
        import secrets
        salt = secrets.token_hex(16)
        hashed = hashlib.pbkdf2_hmac("sha256", found_password.encode(), salt.encode(), 100000)
        new_hash = f"{salt}${hashed.hex()}"
        conn.execute("UPDATE users SET hashed_password = ? WHERE id = ?", (new_hash, user_id))
        print(f"  {username}: migrated (password: {found_password})")
    else:
        print(f"  {username}: could not determine password, setting to '123456'")
        import secrets
        salt = secrets.token_hex(16)
        hashed = hashlib.pbkdf2_hmac("sha256", "123456".encode(), salt.encode(), 100000)
        new_hash = f"{salt}${hashed.hex()}"
        conn.execute("UPDATE users SET hashed_password = ? WHERE id = ?", (new_hash, user_id))

conn.commit()
conn.close()
print("Migration complete!")

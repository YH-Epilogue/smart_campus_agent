import sqlite3

db_path = r"E:\实训\smart_campus_agent\backend\data\sqlite.db"
conn = sqlite3.connect(db_path)

try:
    conn.execute("ALTER TABLE knowledge_bases ADD COLUMN department TEXT DEFAULT ''")
    print("Added department")
except:
    print("department already exists")

try:
    conn.execute("ALTER TABLE knowledge_bases ADD COLUMN owner_name TEXT DEFAULT ''")
    print("Added owner_name")
except:
    print("owner_name already exists")

try:
    conn.execute("ALTER TABLE knowledge_bases ADD COLUMN embedding_model TEXT DEFAULT 'shibing624/text2vec-base-chinese'")
    print("Added embedding_model")
except:
    print("embedding_model already exists")

conn.commit()
conn.close()
print("Database fixed!")

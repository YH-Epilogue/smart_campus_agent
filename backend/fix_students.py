import sqlite3
conn = sqlite3.connect(r'E:\实训\smart_campus_agent\backend\data\sqlite.db')
conn.execute("UPDATE students SET student_id = '2305500280' WHERE name = '晏郝'")
conn.commit()
rows = conn.execute('SELECT student_id, name, class_name FROM students').fetchall()
for r in rows:
    print(f'  {r[0]} - {r[1]} - {r[2]}')
conn.close()

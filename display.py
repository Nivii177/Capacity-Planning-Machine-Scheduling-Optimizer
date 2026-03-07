import sqlite3

conn = sqlite3.connect("production.db")
cur = conn.cursor()

cur.execute("SELECT * FROM styles")
rows = cur.fetchall()

for row in rows:
    print(row)

conn.close()
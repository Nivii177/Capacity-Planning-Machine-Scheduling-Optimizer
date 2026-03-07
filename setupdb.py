import sqlite3  

conn = sqlite3.connect("production.db")

cur = conn.cursor()

cur.execute("""
CREATE TABLE IF NOT EXISTS styles(
id INTEGER PRIMARY KEY AUTOINCREMENT,
style_size TEXT UNIQUE NOT NULL,
mct1 INTEGER DEFAULT 0,
mct2 INTEGER DEFAULT 0,
mct3 INTEGER DEFAULT 0,
mct4 INTEGER DEFAULT 0,
mct5 INTEGER DEFAULT 0,
mct6 INTEGER DEFAULT 0,
mct7 INTEGER DEFAULT 0,
mct8 INTEGER DEFAULT 0,
mct9 INTEGER DEFAULT 0,
mct10 INTEGER DEFAULT 0,
mct11 INTEGER DEFAULT 0,
mct12 INTEGER DEFAULT 0,
July_demand INTEGER DEFAULT 0
)
""")

conn.commit()
conn.close()

print("Primary database created successfully")



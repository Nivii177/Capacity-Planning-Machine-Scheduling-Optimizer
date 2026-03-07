import sqlite3

conn = sqlite3.connect("optimizerdata.db")

cur = conn.cursor()


cur.execute("""
    CREATE TABLE IF NOT EXISTS optimizerdata(
    style_size TEXT PRIMARY KEY,
    mct1_days REAL DEFAULT 0,
    mct2_days REAL DEFAULT 0,
    mct3_days REAL DEFAULT 0,
    mct4_days REAL DEFAULT 0,
    mct5_days REAL DEFAULT 0,
    mct6_days REAL DEFAULT 0,
    mct7_days REAL DEFAULT 0,
    mct8_days REAL DEFAULT 0,
    mct9_days REAL DEFAULT 0,
    mct10_days REAL DEFAULT 0,
    mct11_days REAL DEFAULT 0,
    mct12_days REAL DEFAULT 0,
    FOREIGN KEY (style_size) REFERENCES styles(style_size)
    )
""")

conn.commit()
conn.close()

print("Optimizer data database created successfully")


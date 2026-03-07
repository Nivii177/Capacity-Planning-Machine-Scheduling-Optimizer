import sqlite3

from scipy.optimize import linprog

DB = "production.db"

def get_styles_and_capacities():
    conn = sqlite3.connect(DB)
    cur = conn.cursor()
    cur.execute("""
        SELECT style_size, mct1, mct2, mct3, mct4, mct5, mct6,
               mct7, mct8, mct9, mct10, mct11, mct12, July_demand
        FROM styles
    """)
    rows = cur.fetchall()
    conn.close()
    return rows



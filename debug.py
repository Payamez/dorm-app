import sqlite3
from helpers import  dormitory_names

conn = sqlite3.connect("dormapp.db")
cursor = conn.cursor()

# Drop tables completely
cursor.execute(
        "DROP TABLE laundry_requests"
    )


conn.commit()
conn.close()
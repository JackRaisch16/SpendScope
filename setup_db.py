import sqlite3

conn = sqlite3.connect('db/database.db')
cursor = conn.cursor()

cursor.execute('''
    CREATE TABLE IF NOT EXISTS transactions (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        date TEXT,
        description TEXT,
        amount REAL,
        category TEXT
    )
''')

conn.commit()
conn.close()

print("Database and table created successfully.")


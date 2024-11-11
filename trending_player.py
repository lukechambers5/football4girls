import sqlite3

def create_db():
    conn = sqlite3.connect('search_logs.db')
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS search_log (
            name TEXT,
            count INTEGER
        )
    ''')
    conn.commit()
    conn.close()
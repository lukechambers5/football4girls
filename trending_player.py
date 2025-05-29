import sqlite3
from scraper import get_player_image
import os

#DB_PATH = os.path.join(os.getenv('DATABASE_DIR', '/var/data'), 'search_logs.db') #For running publicly
DB_PATH = 'search_logs.db' # change to run locally

def create_db():
    conn = sqlite3.connect(DB_PATH)  # Use DB_PATH here to maintain consistency
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS search_log (
            name TEXT PRIMARY KEY,
            count INTEGER
        )
    ''')
    conn.commit()
    conn.close()


def update_player_search(player_name):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    cursor.execute('SELECT count FROM search_log WHERE name = ?', (player_name,))
    result = cursor.fetchone()

    if result:
        cursor.execute('UPDATE search_log SET count = count + 1 WHERE name = ?', (player_name,))
    else:
        cursor.execute('INSERT INTO search_log (name, count) VALUES (?, ?)', (player_name, 1))

    conn.commit()
    conn.close()


def get_most_searched_players():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    cursor.execute('SELECT name, count FROM search_log ORDER BY count DESC LIMIT 1')
    result = cursor.fetchone()

    if result:
        player_name = result[0]
        player_count = result[1]
        player_image_url = get_player_image(player_name)
        return {
            'name': player_name,
            'search_count': player_count,
            'image_url': player_image_url
        }
    else:
        return None

def get_all_search_logs():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    cursor.execute('SELECT name, count FROM search_log ORDER BY count DESC')
    results = cursor.fetchall()

    conn.close()
    
    return results

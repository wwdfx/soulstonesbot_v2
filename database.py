import psycopg2
from psycopg2.extras import DictCursor

# Database connection details
DB_DETAILS = {
    "dbname": "koyebdb",
    "user": "koyeb-adm",
    "password": "WCAFr1R0muaZ",
    "host": "ep-shy-pine-a2e1ouuw.eu-central-1.pg.koyeb.app",
    "port": 5432
}

# Connect to PostgreSQL Database
def connect_db():
    conn = psycopg2.connect(**DB_DETAILS)
    conn.autocommit = True
    return conn

conn = connect_db()
cur = conn.cursor(cursor_factory=DictCursor)

# Function to handle reconnection
def reconnect_db(func):
    async def wrapper(*args, **kwargs):
        global conn, cur
        try:
            return await func(*args, **kwargs)
        except psycopg2.OperationalError:
            conn.close()
            conn = connect_db()
            cur = conn.cursor(cursor_factory=DictCursor)
            return await func(*args, **kwargs)
    return wrapper

# Ensure tables exist
cur.execute('''
    CREATE TABLE IF NOT EXISTS balances (
        user_id BIGINT PRIMARY KEY,
        balance INTEGER NOT NULL DEFAULT 0
    )
''')

cur.execute('''
    CREATE TABLE IF NOT EXISTS users (
        user_id BIGINT PRIMARY KEY,
        role TEXT NOT NULL DEFAULT 'user'
    )
''')

cur.execute('''
    CREATE TABLE IF NOT EXISTS last_reading (
        user_id BIGINT PRIMARY KEY,
        last_request TIMESTAMP
    )
''')

cur.execute('''
    CREATE TABLE IF NOT EXISTS checkin_streak (
        user_id BIGINT PRIMARY KEY,
        streak INTEGER NOT NULL DEFAULT 0,
        last_checkin TIMESTAMP
    )
''')

cur.execute('''
    CREATE TABLE IF NOT EXISTS last_game (
        user_id BIGINT PRIMARY KEY,
        last_play TIMESTAMP
    )
''')

cur.execute('''
    CREATE TABLE IF NOT EXISTS missions (
        id SERIAL PRIMARY KEY,
        name TEXT,
        rarity TEXT,
        appearing_rate INTEGER,
        length INTEGER,
        reward INTEGER
    )
''')

cur.execute('''
    CREATE TABLE IF NOT EXISTS user_missions (
        user_id BIGINT,
        mission_id INTEGER,
        start_time TIMESTAMP,
        end_time TIMESTAMP,
        completed BOOLEAN DEFAULT FALSE,
        PRIMARY KEY (user_id, mission_id, start_time)
    )
''')

cur.execute('''
    CREATE TABLE IF NOT EXISTS mission_attempts (
        user_id BIGINT,
        date DATE,
        attempts INTEGER DEFAULT 0,
        PRIMARY KEY (user_id, date)
    )
''')

cur.execute('''
    CREATE TABLE IF NOT EXISTS user_symbols (
        user_id BIGINT PRIMARY KEY,
        symbols_count BIGINT DEFAULT 0
    )
''')

# Populate the missions table with 25 different missions
missions = [
    ('Патрулировать нижний Бруклин', 'Сложность: 1', 50, 2, 150),
    ('Охранять мага во время ритуала', 'Сложность: 2', 25, 3, 225),
    ('Зачистить нелегальное логово вампиров', 'Сложность: 3', 15, 4, 300),
    ('Уничтожить улей демонов-шерстней', 'Сложность: 4', 7, 6, 450),
    ('Уничтожить высшего демона', 'Сложность: 5', 3, 8, 600),
]

cur.executemany('INSERT INTO missions (name, rarity, appearing_rate, length, reward) VALUES (%s, %s, %s, %s, %s) ON CONFLICT DO NOTHING', missions)
conn.commit()
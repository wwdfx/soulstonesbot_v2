from database import cur, conn, reconnect_db

@reconnect_db
async def get_user_role(user_id):
    cur.execute('SELECT role FROM users WHERE user_id = %s', (user_id,))
    result = cur.fetchone()
    return result['role'] if result else 'user'

@reconnect_db
async def set_balance(user_id, amount):
    cur.execute('INSERT INTO balances (user_id, balance) VALUES (%s, %s) ON CONFLICT (user_id) DO UPDATE SET balance = %s', (user_id, amount, amount))
    conn.commit()
    return amount
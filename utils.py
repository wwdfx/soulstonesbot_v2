# utils.py

import random
from datetime import datetime, timedelta
from database import cur, conn, reconnect_db

async def get_balance(user_id):
    cur.execute('SELECT balance FROM balances WHERE user_id = %s', (user_id,))
    result = cur.fetchone()
    return result['balance'] if result else 0

async def update_balance(user_id, amount):
    current_balance = await get_balance(user_id)
    new_balance = current_balance + amount
    cur.execute('INSERT INTO balances (user_id, balance) VALUES (%s, %s) ON CONFLICT (user_id) DO UPDATE SET balance = %s', (user_id, new_balance, new_balance))
    return new_balance

async def reduce_balance(user_id, amount):
    current_balance = await get_balance(user_id)
    if current_balance < amount:
        return None
    new_balance = current_balance - amount
    cur.execute('INSERT INTO balances (user_id, balance) VALUES (%s, %s) ON CONFLICT (user_id) DO UPDATE SET balance = %s', (user_id, new_balance, new_balance))
    return new_balance

async def get_user_symbols(user_id):
    cur.execute('SELECT symbols_count FROM users WHERE user_id = %s', (user_id,))
    result = cur.fetchone()
    return result['symbols_count'] if result else 0

async def get_user_rank(user_id):
    symbols_count = await get_user_symbols(user_id)
    if symbols_count < 5000:
        return "Смертный", 25
    elif symbols_count < 20000:
        return "Новичок", 50
    elif symbols_count < 50000:
        return "Новоприбывший Охотник", 100
    elif symbols_count < 100000:
        return "Опытный охотник", 150
    elif symbols_count < 250000:
        return "Лидер миссий Института", 200
    elif symbols_count < 400000:
        return "Лидер Института", 250
    elif symbols_count < 750000:
        return "Кандидат в Инквизиторы", 300
    else:
        return "Инквизитор", 400

@reconnect_db
async def can_request_reading(user_id):
    cur.execute('SELECT last_request FROM last_reading WHERE user_id = %s', (user_id,))
    result = cur.fetchone()
    if result:
        last_request_time = result['last_request']
        if datetime.now() - last_request_time < timedelta(days=1):
            return False
    cur.execute('INSERT INTO last_reading (user_id, last_request) VALUES (%s, %s) ON CONFLICT (user_id) DO UPDATE SET last_request = %s', (user_id, datetime.now(), datetime.now()))
    return True

@reconnect_db
async def check_missions(context):
    now = datetime.now()
    cur.execute('SELECT user_id, mission_id FROM user_missions WHERE completed = FALSE AND end_time <= %s', (now,))
    completed_missions = cur.fetchall()

    for mission in completed_missions:
        user_id, mission_id = mission['user_id'], mission['mission_id']
        cur.execute('SELECT reward FROM missions WHERE id = %s', (mission_id,))
        reward = cur.fetchone()['reward']
        await update_balance(user_id, reward)
        cur.execute('UPDATE user_missions SET completed = TRUE WHERE user_id = %s AND mission_id = %s', (user_id, mission_id))
        await context.bot.send_message(chat_id=user_id, text=f"✅ Ваша миссия завершена! ✅ Вы получили {reward} 💎 Камней душ.")
    conn.commit()

async def generate_missions():
    missions = []
    cur.execute('SELECT * FROM missions')
    mission_data = cur.fetchall()
    for mission in mission_data:
        if random.randint(1, 100) <= mission['appearing_rate']:
            missions.append(mission)
        if len(missions) >= 5:
            break
    return missions
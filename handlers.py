import random
from datetime import datetime, timedelta
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes
from database import cur, conn, reconnect_db
from utils import generate_missions, get_balance, update_balance, reduce_balance, get_user_rank, get_user_symbols, can_request_reading

async def message_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.message:
        message_text = update.message.text
        target_group_id = -1002142915618  # Adjust this ID to your target group

        if len(message_text) >= 500 and update.message.chat_id == target_group_id:
            user_id = update.message.from_user.id
            user_mention = update.message.from_user.username or update.message.from_user.first_name
            mention_text = f"@{user_mention}" if update.message.from_user.username else user_mention

            cur.execute('INSERT INTO user_symbols (user_id, symbols_count) VALUES (%s, %s) ON CONFLICT (user_id) DO UPDATE SET symbols_count = user_symbols.symbols_count + %s', (user_id, len(message_text), len(message_text)))
            conn.commit()

            user_rank, soulstones = await get_user_rank(user_id)
            new_balance = await update_balance(user_id, soulstones)
            await update.message.reply_text(f"💎 {mention_text}, ваш пост зачтён. Вам начислено +{soulstones} к камням душ. Текущий баланс: {new_balance}💎.")

async def profile_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.message.from_user.id
    user_mention = update.message.from_user.username or update.message.from_user.first_name
    mention_text = f"@{user_mention}" if update.message.from_user.username else user_mention
    user_rank, _ = await get_user_rank(user_id)
    user_balance = await get_balance(user_id)
    total_symbols = await get_user_symbols(user_id)

    profile_text = (f"Профиль {mention_text}:\n"
                    f"Ранк: {user_rank}.\n"
                    f"Баланс Камней душ: {user_balance}.\n"
                    f"Символов в рп-чате: {total_symbols}.")

    buttons = [
        [InlineKeyboardButton("Баланс", callback_data="balance")],
        [InlineKeyboardButton("Предсказание от Магнуса", callback_data="reading")],
        [InlineKeyboardButton("Ежедневная награда", callback_data="checkin")],
        [InlineKeyboardButton("Камень-ножницы-бумага", callback_data="rockpaperscissors")],
        [InlineKeyboardButton("Миссии", callback_data="missions")]
    ]
    keyboard = InlineKeyboardMarkup(buttons)
    await update.message.reply_text(profile_text, reply_markup=keyboard)

async def balance_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    user_id = query.from_user.id
    user_mention = query.from_user.username or query.from_user.first_name
    mention_text = f"@{user_mention}" if query.from_user.username else user_mention
    balance = await get_balance(user_id)
    await query.edit_message_text(f"💎 {mention_text}, ваш текущий баланс: {balance}💎.")

@reconnect_db
async def checkin_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    user_id = query.from_user.id
    today = datetime.now()
    cur.execute('SELECT streak, last_checkin FROM checkin_streak WHERE user_id = %s', (user_id,))
    result = cur.fetchone()

    if result:
        streak, last_checkin = result['streak'], result['last_checkin']

        if today.date() == last_checkin.date():
            await query.edit_message_text("Вы уже получали награду за вход сегодня. Повторите попытку завтра.")
            return

        if today - last_checkin > timedelta(days=1):
            streak = 1
            reward = 25
            image_path = './img/lossStreak.png'
            await query.message.reply_photo(photo=open(image_path, 'rb'), caption="К сожалению, вы прервали череду ежедневных входов и получили 25 Камней душ.")
        else:
            streak += 1
            if streak > 7:
                streak = 7
            reward = 25 * streak
            image_path = f'./img/check{streak}.png'
            await query.message.reply_photo(photo=open(image_path, 'rb'), caption=f"Вы выполнили ежедневный вход {streak} дней подряд и получили {reward} Камней душ!")
    else:
        streak = 1
        reward = 25
        image_path = './img/check1.png'
        await query.message.reply_photo(photo=open(image_path, 'rb'), caption=f"Вы выполнили ежедневный вход 1 день подряд и получили 25 Камней душ!")

    cur.execute('INSERT INTO checkin_streak (user_id, streak, last_checkin) VALUES (%s, %s, %s) ON CONFLICT (user_id) DO UPDATE SET streak = %s, last_checkin = %s', (user_id, streak, today, streak, today))
    conn.commit()
    new_balance = await update_balance(user_id, reward)
    user_mention = query.from_user.username or query.from_user.first_name
    mention_text = f"@{user_mention}" if query.from_user.username else user_mention
    await query.edit_message_text(f"💎 {mention_text}, ваш текущий баланс: {new_balance}💎.")

readings = [
    "Сегодня ангельская сила будет направлять тебя.",
    "Новая руна откроет тебе свою истинную цель.",
    "Остерегайся демонов, прячущихся в неожиданных местах.",
    "Союзник из Нижнего мира окажет важную помощь.",
    "Твой серфимский клинок будет сегодня сиять ярче в твоих руках.",
    "Институт хранит секрет, который изменит твой путь.",
    "Связь парабатай укрепит твою решимость.",
    "Сообщение из Идриса принесет важные новости.",
    "Мудрость Безмолвных братьев поможет в твоем приключении.",
    "Новое задание проверит твои способности Сумеречного охотника.",
    "Решение Конклава повлияет на твое будущее.",
    "Маг откроет тебе портал в значимое место.",
    "Твой стеле создаст руну огромной силы.",
    "Древняя книга заклинаний откроет забытое временем проклятие.",
    "Загадка фейри приведет тебя к скрытой истине.",
    "Твоя связь с ангельским миром станет сильнее.",
    "Лояльность вампира окажется неоценимой.",
    "Заклинание колдуна принесет ясность в запутанную ситуацию.",
    "Демонические миры необычайно активны; будь на чеку.",
    "Сон даст тебе представление о будущем.",
    "Скрытая руна откроет новую способность.",
    "Ищи ответы в Кодексе. Он знает что тебе подсказать",
    "Смертный удивит тебя своей храбростью.",
    "Потерянная семейная реликвия обретет новое значение.",
    "Теневой рынок содержит предмет, важный для твоего задания.",
    "Столкновение с мятежным Сумеречным охотником неизбежно.",
    "Церемония рун приблизит тебя к твоему истинному потенциалу.",
    "Посещение Зала Согласия очень необходимо.",
    "Неожиданный союз сформируется с обитателем Нижнего мира.",
    "Твой серфимский клинок поможет уничтожить скрытого демона.",
    "Запретное заклинание будет искушать тебя великой силой.",
    "Сообщение из Благого Двора прибудет с настоятельностью.",
    "Призрак прошлого Сумеречного охотника предложит мудрость.",
    "Зачарованный артефакт усилит твои способности.",
    "Твоя лояльность Конклаву будет испытана.",
    "Пророчество из Молчаливого Города выйдет на свет.",
    "Редкий демон потребует твоего немедленного внимания.",
    "Старый друг вернется с удивительными новостями.",
    "Видение от ангела Разиэля направит твой путь.",
    "Сила Смертной Чаши будет ощущаться особенно сильно сегодня.",
    "Путешествие в Город Костей раскроет скрытые знания.",
    "Звук рога Сумеречных охотников сигнализирует важное событие.",
    "Таинственная руна появится в твоих снах.",
    "Встреча с Двором Сумерек изменит твою судьбу.",
    "Тайна Инквизитора будет раскрыта.",
    "Скрытый вход в Институт приведет к новому открытию.",
    "Неожиданный подарок от мага удивит тебя.",
    "Тайное послание от фейри приведет к интересной находке.",
    "Исследование старого Института раскроет древнюю реликвию."
]

async def reading_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    user_id = query.from_user.id

    if not await can_request_reading(user_id):
        await query.edit_message_text("Вы уже получили предсказание на сегодня. Повторите попытку завтра.")
        return

    reading = random.choice(readings)
    await query.edit_message_text(f"🔮 Ваше предсказание от Магнуса: {reading}")

async def rockpaperscissors_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    buttons = [
        [InlineKeyboardButton("Камень", callback_data="rps_rock")],
        [InlineKeyboardButton("Ножницы", callback_data="rps_scissors")],
        [InlineKeyboardButton("Бумага", callback_data="rps_paper")]
    ]
    keyboard = InlineKeyboardMarkup(buttons)
    await query.edit_message_text("Выберите камень, ножницы или бумагу:", reply_markup=keyboard)

async def rps_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    user_choice = query.data.split('_')[1]
    choices = ['rock', 'scissors', 'paper']
    bot_choice = random.choice(choices)
    outcome = ""

    if user_choice == bot_choice:
        outcome = "Ничья! Никто не получает Камни душ."
    elif (user_choice == "rock" and bot_choice == "scissors") or \
         (user_choice == "scissors" and bot_choice == "paper") or \
         (user_choice == "paper" and bot_choice == "rock"):
        outcome = "Вы выиграли! Вам начислено 25 Камней душ."
        await update_balance(query.from_user.id, 25)
    else:
        outcome = "Вы проиграли! Вы потеряли 25 Камней душ."
        await reduce_balance(query.from_user.id, 25)

    await query.edit_message_text(f"Вы выбрали {user_choice}, бот выбрал {bot_choice}. {outcome}")

@reconnect_db
async def missions_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.callback_query.from_user.id
    today = datetime.now().date()

    cur.execute('SELECT attempts FROM mission_attempts WHERE user_id = %s AND date = %s', (user_id, today))
    result = cur.fetchone()
    attempts = result['attempts'] if result else 0

    if attempts >= 3:
        await update.callback_query.edit_message_text("✨ Вы уже отправили 3 отряда на миссии сегодня. ⌛️ Повторите попытку завтра.")
        return

    missions = await generate_missions()
    buttons = [
        InlineKeyboardButton(
            f"{mission['name']} ({mission['reward']} 💎 камней душ)",
            callback_data=f"mission_{mission['id']}"
        )
        for mission in missions
    ]
    keyboard = InlineKeyboardMarkup.from_column(buttons)
    await update.callback_query.edit_message_text("⚔️ Выберите миссию для отправки отряда:", reply_markup=keyboard)

@reconnect_db
async def mission_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    user_id = query.from_user.id
    mission_id = int(query.data.split('_')[1])

    cur.execute('SELECT * FROM missions WHERE id = %s', (mission_id,))
    mission = cur.fetchone()

    if not mission:
        await query.edit_message_text("Ошибка: миссия не найдена.")
        return

    today = datetime.now().date()
    cur.execute('SELECT attempts FROM mission_attempts WHERE user_id = %s AND date = %s', (user_id, today))
    result = cur.fetchone()
    attempts = result['attempts'] if result else 0

    if attempts >= 3:
        await query.edit_message_text("✨ Вы уже отправили 3 отряда на миссии сегодня. ⌛️ Повторите попытку завтра.")
        return

    if result:
        cur.execute('UPDATE mission_attempts SET attempts = attempts + 1 WHERE user_id = %s AND date = %s', (user_id, today))
    else:
        cur.execute('INSERT INTO mission_attempts (user_id, date, attempts) VALUES (%s, %s, 1)', (user_id, today))
    conn.commit()

    start_time = datetime.now()
    end_time = start_time + timedelta(hours=mission['length'])
    cur.execute('INSERT INTO user_missions (user_id, mission_id, start_time, end_time) VALUES (%s, %s, %s, %s)', (user_id, mission_id, start_time, end_time))
    conn.commit()

    await query.edit_message_text(f"💼 Вы отправили отряд на миссию: ✨{mission['name']}✨. 🌒 Время завершения: ⌛️ {end_time.strftime('%Y-%m-%d %H:%M:%S')} ⌛️.")
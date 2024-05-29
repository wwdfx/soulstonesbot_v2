import logging
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, CallbackQueryHandler, ConversationHandler, filters
from handlers import (
    message_handler, profile_command, balance_command, checkin_command, reading_command, 
    rockpaperscissors_command, bet_callback, play_callback, mission_callback, missions_command
)
from utils import check_missions

# Set up basic logging
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize the bot and add handlers
app = ApplicationBuilder().token("7175746196:AAHckVjmat7IBpqvzWfTxvUzvQR1_1FgLiw").build()

app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, message_handler))
app.add_handler(CommandHandler("profile", profile_command))
app.add_handler(CommandHandler("balance", balance_command))
app.add_handler(CommandHandler("checkin", checkin_command))
app.add_handler(CommandHandler("reading", reading_command))
app.add_handler(CommandHandler("rockpaperscissors", rockpaperscissors_command))
app.add_handler(CommandHandler("missions", missions_command))
app.add_handler(CallbackQueryHandler(bet_callback, pattern='^bet_'))
app.add_handler(CallbackQueryHandler(play_callback, pattern='^play_'))
app.add_handler(CallbackQueryHandler(mission_callback, pattern='^mission_'))
app.add_handler(CallbackQueryHandler(balance_command, pattern='^balance$'))
app.add_handler(CallbackQueryHandler(reading_command, pattern='^reading$'))
app.add_handler(CallbackQueryHandler(checkin_command, pattern='^checkin$'))
app.add_handler(CallbackQueryHandler(rockpaperscissors_command, pattern='^rockpaperscissors$'))
app.add_handler(CallbackQueryHandler(missions_command, pattern='^missions$'))

job_queue = app.job_queue
job_queue.run_repeating(check_missions, interval=6000, first=6000)

logger.info("Starting the bot")
# Keep the bot running
app.run_polling()
logger.info("Bot has stopped")

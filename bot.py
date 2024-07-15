from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    Application,
    CommandHandler,
    CallbackQueryHandler,
    ConversationHandler,
    MessageHandler,
    filters,
    CallbackContext,
)

import sqlite3
import requests
import configparser
from HKUST.hkust import HKUST
import time

from night_timer import *

# Define states for conversation
USERNAME, PASSWORD, TURN_ON_OFF, TIMER_START_END_TIME, ON_OFF_TIME = range(5)

# Initialize database
def init_db():
    conn = sqlite3.connect('user_credentials.db')
    c = conn.cursor()
    c.execute('''
        CREATE TABLE IF NOT EXISTS credentials (
            user_id INTEGER PRIMARY KEY, 
            username TEXT, 
            password TEXT, 
            night_timer_enabled INTEGER DEFAULT 0, 
            start_time TEXT DEFAULT '22:00',
            end_time TEXT DEFAULT '07:00',
            on_time INTEGER DEFAULT 15,
            off_time INTEGER DEFAULT 5
        )
    ''')
    conn.commit()
    conn.close()

def get_config():
    config = configparser.ConfigParser()
    config.read('conf.ini')
    return config

async def post_init(application: Application):
    await application.bot.set_my_commands([
        ('start', 'Start the bot / Set username and password'),
        ('turn_on', 'Turn on the AC'),
        ('turn_off', 'Turn off the AC'),
        ('enable_night_timer', 'Enable night timer (Default: Disabled)'),
        ('disable_night_timer', 'Disable night timer (Default: Disabled)'),
        ('set_timer_start_end_time', 'Set night timer start and end time (Default: 22:00 - 07:00)'),
        ('set_on_off_time', 'Set on and off time (Default: 15 - 5, total should be 20 minutes)'),
    ])

async def start(update: Update, context: CallbackContext) -> int:
    await update.message.reply_text("Welcome! Please provide your username :D")
    return USERNAME

async def input_username(update: Update, context: CallbackContext) -> int:
    user_id = update.message.from_user.id
    context.user_data['username'] = update.message.text
    await update.message.reply_text("Username received! Now please provide your password.")
    return PASSWORD

async def input_password(update: Update, context: CallbackContext) -> int:
    user_id = update.message.from_user.id
    username = context.user_data.get('username')
    password = update.message.text
    
    conn = sqlite3.connect('user_credentials.db')
    c = conn.cursor()
    c.execute('INSERT OR REPLACE INTO credentials (user_id, username, password, night_timer_enabled, start_time, end_time, on_time, off_time) VALUES (?, ?, ?, 0, "22:00", "07:00", 15, 5)', (user_id, username, password))

    conn.commit()
    conn.close()
    
    await update.message.reply_text("Your credentials have been saved successfully.")
    return ConversationHandler.END

def get_user_credentials(user_id: int) -> Tuple[str, str]:
    conn = sqlite3.connect('user_credentials.db')
    c = conn.cursor()
    c.execute('SELECT username, password FROM credentials WHERE user_id = ?', (user_id,))
    result = c.fetchone()
    conn.close()
    return result

async def turn_ac_on(update: Update, context: CallbackContext):
    user_id = update.effective_user.id
    res = get_user_credentials(user_id)
    print(res)
    username, password = res
    if username is None or password is None:
        await update.message.reply_text("Please set your username and password first.")
        return
    
    with HKUST() as bot:
        bot.land_login_page()
        bot.submit_username(username)
        bot.submit_password(password)
        bot.toggle_ac_on()
    
    await update.message.reply_text("Air conditioner has been turned on.")

async def turn_ac_off(update: Update, context: CallbackContext):
    user_id = update.effective_user.id
    username, password = get_user_credentials(user_id)
    if username is None or password is None:
        await update.message.reply_text("Please set your username and password first.")
        return
    
    with HKUST() as bot:
        bot.land_login_page()
        bot.submit_username(username)
        bot.submit_password(password)
        bot.toggle_ac_off()
    
    await update.message.reply_text("Air conditioner has been turned off.")

async def enable_night_timer(update: Update, context: CallbackContext):
    user_id = update.effective_user.id
    conn = sqlite3.connect('user_credentials.db')
    c = conn.cursor()
    c.execute('SELECT night_timer_enabled FROM credentials WHERE user_id = ?', (user_id,))
    result = c.fetchone()
    if result is None:
        await update.message.reply_text("Please set your username and password first.")
        return
    elif result[0] == 1:
        await update.message.reply_text("Night timer is already enabled.")
        return
    else:
        c.execute('UPDATE credentials SET night_timer_enabled = 1 WHERE user_id = ?', (user_id,))
        await update.message.reply_text("Night timer has been enabled.")
        add_user_job(user_id)

    conn.commit()
    conn.close()

async def disable_night_timer(update: Update, context: CallbackContext):
    user_id = update.effective_user.id
    conn = sqlite3.connect('user_credentials.db')
    c = conn.cursor()
    c.execute('SELECT night_timer_enabled FROM credentials WHERE user_id = ?', (user_id,))
    result = c.fetchone()
    if result is None:
        await update.message.reply_text("Please set your username and password first.")
        return
    elif result[0] == 0:
        await update.message.reply_text("Night timer is already disabled.")
        return
    else:
        c.execute('UPDATE credentials SET night_timer_enabled = 0 WHERE user_id = ?', (user_id,))
        await update.message.reply_text("Night timer has been disabled.")
        remove_user_job(user_id)

    conn.commit()
    conn.close()

async def message_timer_start_end_time(update: Update, context: CallbackContext):
    await update.message.reply_text("Please provide the start and end time for the night timer in the format %H:%M - %H:%M")
    return TIMER_START_END_TIME

async def set_timer_start_end_time(update: Update, context: CallbackContext):
    times = update.message.text.split('-')
    if len(times) != 2:
        await update.message.reply_text("Invalid time format. Please provide time in the format %H:%M - %H:%M")
        return
    start_time, end_time = times
    try:
        datetime.strptime(start_time.strip(), '%H:%M')
        datetime.strptime(end_time.strip(), '%H:%M')
    except ValueError:
        await update.message.reply_text("Invalid time format. Please provide time in the format %H:%M - %H:%M")
        return
    
    user_id = update.effective_user.id
    conn = sqlite3.connect('user_credentials.db')
    c = conn.cursor()
    c.execute('UPDATE credentials SET start_time = ?, end_time = ? WHERE user_id = ?', (start_time, end_time, user_id))
    if c.rowcount == 0:
        await update.message.reply_text("Please set your username and password first.")
        return
    else:
        await update.message.reply_text("Start and end time has been set successfully.")

    update_user_job(user_id)

    conn.commit()
    conn.close()

async def message_on_off_time(update: Update, context: CallbackContext):
    await update.message.reply_text("Please provide the on and off time for the night timer in the format S - E")
    return ON_OFF_TIME

async def set_on_off_time(update: Update, context: CallbackContext):
    times = update.message.text.split(' - ')
    if len(times) != 2:
        await update.message.reply_text("Invalid time format. Please provide time in the format S - E")
        return
    on_time, off_time = times
    try:
        on_time = int(on_time)
        off_time = int(off_time)
    except ValueError:
        await update.message.reply_text("Invalid time format. Please provide time in the format S - E")
        return
    
    if on_time < 0 or off_time < 0:
        await update.message.reply_text("Time cannot be negative.")
        return
    
    if on_time + off_time > 20:
        await update.message.reply_text("Total time should be equal to 20 minutes.")
        return
    
    user_id = update.effective_user.id
    conn = sqlite3.connect('user_credentials.db')
    c = conn.cursor()
    c.execute('UPDATE credentials SET on_time = ?, off_time = ? WHERE user_id = ?', (on_time, off_time, user_id))
    if c.rowcount == 0:
        await update.message.reply_text("Please set your username and password first.")
        return
    else:
        await update.message.reply_text("On and off time has been set successfully.")

    update_user_job(user_id)

    conn.commit()
    conn.close()

def main():
    config = get_config()
    token = config['telegram.bot']['TOKEN']
    application = Application.builder().post_init(post_init).token(token).build()

    cred_handler = ConversationHandler(
        entry_points=[CommandHandler('start', start)],
        states={
            USERNAME: [MessageHandler(filters.TEXT & ~filters.COMMAND, input_username)],
            PASSWORD: [MessageHandler(filters.TEXT & ~filters.COMMAND, input_password)],
        },
        fallbacks=[],
    )
    
    application.add_handler(cred_handler)
    application.add_handler(CommandHandler('turn_on', turn_ac_on))
    application.add_handler(CommandHandler('turn_off', turn_ac_off))
    application.add_handler(CommandHandler('enable_night_timer', enable_night_timer))
    application.add_handler(CommandHandler('disable_night_timer', disable_night_timer))

    timer_handler = ConversationHandler(
        entry_points=[CommandHandler('set_timer_start_end_time', message_timer_start_end_time)],
        states={
            TIMER_START_END_TIME: [MessageHandler(filters.TEXT & ~filters.COMMAND, set_timer_start_end_time)],
        },
        fallbacks=[],
    )
    application.add_handler(timer_handler)

    on_off_handler = ConversationHandler(
        entry_points=[CommandHandler('set_on_off_time', message_on_off_time)],
        states={
            ON_OFF_TIME: [MessageHandler(filters.TEXT & ~filters.COMMAND, set_on_off_time)],
        },
        fallbacks=[],
    )
    application.add_handler(on_off_handler)

    application.run_polling(allowed_updates=Update.ALL_TYPES)

if __name__ == '__main__':
    init_db()
    main()
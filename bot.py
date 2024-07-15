from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, ConversationHandler, MessageHandler, filters, CallbackContext
import sqlite3
import requests

# Define states for conversation
USERNAME, PASSWORD, TURN_ON_OFF = range(3)

# Initialize database
def init_db():
    conn = sqlite3.connect('user_credentials.db')
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS credentials (user_id INTEGER PRIMARY KEY, username TEXT, password TEXT)''')
    conn.commit()
    conn.close()

# Start command
async def start(update: Update, context: CallbackContext) -> int:
    await update.message.reply_text("Welcome! Please provide your username.")
    return USERNAME

# Save username and ask for password
async def input_username(update: Update, context: CallbackContext) -> int:
    user_id = update.message.from_user.id
    context.user_data['username'] = update.message.text
    await update.message.reply_text("Username received! Now please provide your password.")
    return PASSWORD

# Save password to database
async def input_password(update: Update, context: CallbackContext) -> int:
    user_id = update.message.from_user.id
    username = context.user_data.get('username')
    password = update.message.text
    
    conn = sqlite3.connect('user_credentials.db')
    c = conn.cursor()
    c.execute('REPLACE INTO credentials (user_id, username, password) VALUES (?, ?, ?)', (user_id, username, password))
    conn.commit()
    conn.close()
    
    await update.message.reply_text("Your credentials have been saved successfully.")
    return ConversationHandler.END

# Get user credentials from database
def get_user_credentials(user_id):
    conn = sqlite3.connect('user_credentials.db')
    c = conn.cursor()
    c.execute('SELECT username, password FROM credentials WHERE user_id = ?', (user_id,))
    username, password = c.fetchone()
    conn.close()
    return username, password

# Button callback for turning on/off
async def turn_on_off(update: Update, context: CallbackContext) -> None:
    query = update.callback_query
    query.answer()
    user_id = query.from_user.id
    username, password = get_user_credentials(user_id)
    
    # response = requests.post('', json={'username': username, 'password': password})
    
    # if response.ok:
    if False:
        await query.edit_message_text(f"API Response: {response.text}")
    else:
        await query.edit_message_text("Failed to call API.")

# Main function to start the bot
def main():
    application = Application.builder().token("TOKEN").build()

    # Setup conversation handler with the states USERNAME and PASSWORD
    conv_handler = ConversationHandler(
        entry_points=[CommandHandler('start', start)],
        states={
            USERNAME: [MessageHandler(filters.TEXT & ~filters.COMMAND, input_username)],
            PASSWORD: [MessageHandler(filters.TEXT & ~filters.COMMAND, input_password)],
        },
        fallbacks=[],
    )
    
    application.add_handler(conv_handler)
    
    # Turn on/off button
    application.add_handler(CallbackQueryHandler(turn_on_off, pattern='^turn_on_off$'))

    # Start the bot
    application.run_polling(allowed_updates=Update.ALL_TYPES)

if __name__ == '__main__':
    init_db()
    main()
import telebot
import requests
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
COMPOUND_API_URL = "http://127.0.0.1:4000/compound"

bot = telebot.TeleBot(BOT_TOKEN)
user_states = {}

# 📌 Fetch supported tokens dynamically from the Node.js API
def get_supported_tokens():
    try:
        response = requests.get(f"{COMPOUND_API_URL}/supported-tokens")
        data = response.json()
        return data["supportedTokens"]
    except Exception as e:
        print(f"❌ Error fetching supported tokens: {e}")
        return ["USDC", "DAI"]  # Default fallback

SUPPORTED_TOKENS = get_supported_tokens()

# 📌 Generate Menu Dynamically (Always Displayed)
def main_menu():
    markup = telebot.types.ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=False)
    markup.add("📊 View Lending Rates", "💰 Supply Crypto", "🏦 Borrow Crypto")
    return markup

# 📌 Command: /start
@bot.message_handler(commands=['start'])
def send_welcome(message):
    bot.send_message(
        message.chat.id, 
        "Welcome to Crypto Buddy Bot! 🤖💰\nChoose an option below.", 
        reply_markup=main_menu()
    )

# 📌 Handle Token Selection (User selects supply/borrow)
@bot.message_handler(func=lambda message: message.text in ["💰 Supply Crypto", "🏦 Borrow Crypto"])
def handle_token_selection(message):
    chat_id = message.chat.id
    user_states[chat_id] = message.text

    markup = telebot.types.ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=False)
    for token in SUPPORTED_TOKENS:
        markup.add(token)

    bot.send_message(chat_id, "Select a token:", reply_markup=markup)

# 📌 Handle Amount Entry After Token Selection
@bot.message_handler(func=lambda message: message.text in SUPPORTED_TOKENS)
def handle_crypto_input(message):
    chat_id = message.chat.id
    crypto_symbol = message.text.upper()

    if crypto_symbol not in SUPPORTED_TOKENS:
        bot.send_message(chat_id, f"❌ Unsupported token '{crypto_symbol}'. Try: {', '.join(SUPPORTED_TOKENS)}.", parse_mode="Markdown", reply_markup=main_menu())
        return

    user_states[chat_id] = crypto_symbol
    action = "supply" if "Supply" in user_states.get(chat_id, "") else "borrow"
    bot.send_message(chat_id, f"Enter the amount of **{crypto_symbol}** to {action} (e.g., `100`).", parse_mode="Markdown", reply_markup=main_menu())

# 📌 Process Transactions After Amount Entry
@bot.message_handler(func=lambda message: message.chat.id in user_states and user_states[message.chat.id] in SUPPORTED_TOKENS)
def process_transaction(message):
    chat_id = message.chat.id
    token = user_states[chat_id]

    try:
        amount = float(message.text)
        action = "supply" if "Supply" in user_states.get(chat_id, "") else "borrow"
        response = requests.post(f"{COMPOUND_API_URL}/{action}", json={"token": token, "amount": str(amount)})
        data = response.json()

        if "error" in data:
            bot.send_message(chat_id, f"❌ Error: {data['error']}", reply_markup=main_menu())
        else:
            bot.send_message(chat_id, f"✅ Success! {data['message']}\n🔗 [View Transaction](https://etherscan.io/tx/{data['txHash']})", parse_mode="Markdown", reply_markup=main_menu())

    except ValueError:
        bot.send_message(chat_id, "❌ Invalid amount. Enter a number (e.g., `100`).", reply_markup=main_menu())

    del user_states[chat_id]

# 📌 Start polling
print("🚀 Crypto Buddy Bot is now up and running!")
bot.polling(none_stop=True)

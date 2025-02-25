import telebot
import requests
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Telegram Bot Token
BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")

# Your Compound API URL (Running from Node.js)
COMPOUND_API_URL = "http://127.0.0.1:4000"

# Initialize the bot
bot = telebot.TeleBot(BOT_TOKEN)

# Dictionary to track user states
user_states = {}

# 📌 Generate the persistent menu
def main_menu():
    markup = telebot.types.ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=False)
    markup.add("📊 View Lending Rates", "💰 Supply USDC", "🏦 Borrow DAI", "🔄 Repay DAI")
    return markup

# 📌 Command: /start (or re-show menu)
@bot.message_handler(commands=['start'])
def send_welcome(message):
    bot.send_message(
        message.chat.id, 
        "Welcome to Crypto Buddy Bot! 🤖💰\n"
        "Choose an option from the menu below or ask me anything about DeFi lending!", 
        reply_markup=main_menu()
    )

# 📌 Handle menu selection
@bot.message_handler(func=lambda message: message.text in ["📊 View Lending Rates", "💰 Supply USDC", "🏦 Borrow DAI", "🔄 Repay DAI"])
def handle_menu_selection(message):
    chat_id = message.chat.id
    user_states[chat_id] = message.text  # Store user selection
    
    if message.text == "📊 View Lending Rates":
        bot.send_message(chat_id, "Fetching latest lending rates... 📊", reply_markup=main_menu())
        fetch_lending_rates(chat_id)

    elif message.text == "💰 Supply USDC":
        bot.send_message(chat_id, "Enter the amount of **USDC** to supply (e.g., `100`).", parse_mode="Markdown", reply_markup=main_menu())

    elif message.text == "🏦 Borrow DAI":
        bot.send_message(chat_id, "Enter the amount of **DAI** to borrow (e.g., `50`).", parse_mode="Markdown", reply_markup=main_menu())

    elif message.text == "🔄 Repay DAI":
        bot.send_message(chat_id, "Enter the amount of **DAI** to repay (e.g., `50`).", parse_mode="Markdown", reply_markup=main_menu())

# 📌 Handle user input after menu selection
@bot.message_handler(func=lambda message: message.chat.id in user_states and user_states[message.chat.id] in ["💰 Supply USDC", "🏦 Borrow DAI", "🔄 Repay DAI"])
def handle_amount_input(message):
    chat_id = message.chat.id
    user_selection = user_states[chat_id]

    try:
        amount = int(message.text) * (10**6 if user_selection == "💰 Supply USDC" else 10**18)  # Convert based on token decimals
    except ValueError:
        bot.send_message(chat_id, "❌ Invalid input! Please enter a whole number (e.g., `100`).", reply_markup=main_menu())
        return

    if user_selection == "💰 Supply USDC":
        bot.send_message(chat_id, f"Processing USDC supply of **{message.text} USDC**... ⏳", parse_mode="Markdown", reply_markup=main_menu())
        execute_transaction(chat_id, "supply_usdc", amount)

    elif user_selection == "🏦 Borrow DAI":
        bot.send_message(chat_id, f"Processing DAI borrow of **{message.text} DAI**... ⏳", parse_mode="Markdown", reply_markup=main_menu())
        execute_transaction(chat_id, "borrow_dai", amount)

    elif user_selection == "🔄 Repay DAI":
        bot.send_message(chat_id, f"Processing DAI repayment of **{message.text} DAI**... ⏳", parse_mode="Markdown", reply_markup=main_menu())
        execute_transaction(chat_id, "repay_dai", amount)

    del user_states[chat_id]  # Reset state after handling

# 📌 Handle free-text questions (Lending-related)
@bot.message_handler(func=lambda message: True)
def handle_general_questions(message):
    chat_id = message.chat.id
    query = message.text.lower()

    if "lending rates" in query or "apy" in query:
        bot.send_message(chat_id, "Fetching latest lending rates... 📊", reply_markup=main_menu())
        fetch_lending_rates(chat_id)

    elif "how does lending work" in query:
        response_message = (
            "📌 **DeFi Lending Basics**:\n"
            "1️⃣ Supply crypto to lending pools (like Compound).\n"
            "2️⃣ Earn interest (APY) based on market rates.\n"
            "3️⃣ Borrow against your supplied assets (as collateral).\n"
            "4️⃣ If the collateral drops too much, liquidation happens.\n"
            "💡 Ask me about current lending rates!"
        )
        bot.send_message(chat_id, response_message, reply_markup=main_menu())

    elif "borrow" in query:
        response_message = (
            "💳 **Borrowing Crypto in DeFi**:\n"
            "1️⃣ Supply an asset as collateral (e.g., USDC, ETH).\n"
            "2️⃣ Borrow another asset (e.g., DAI) up to a certain limit.\n"
            "3️⃣ Pay interest based on market demand.\n"
            "⚠️ Keep collateral above the liquidation threshold!"
        )
        bot.send_message(chat_id, response_message, reply_markup=main_menu())

    else:
        response_message = "🤖 I can help with lending-related queries!\nTry asking: 'What are the lending rates?' or 'How does borrowing work?'"
        bot.send_message(chat_id, response_message, reply_markup=main_menu())

# 📌 Fetch Lending Rates
def fetch_lending_rates(chat_id):
    try:
        response = requests.get(f"{COMPOUND_API_URL}/compound_rates")
        data = response.json()

        rates_message = (
            f"💰 **Current Lending Rates (APY)**:\n\n"
            f"🔹 **USDC Supply APY**: {data['USDC_Supply_APY']}%\n"
            f"🔹 **USDC Borrow APY**: {data['USDC_Borrow_APY']}%\n\n"
            f"📈 Data from Compound Finance"
        )

        bot.send_message(chat_id, rates_message, parse_mode="Markdown", reply_markup=main_menu())

    except Exception as e:
        bot.send_message(chat_id, f"❌ Error fetching lending rates: {str(e)}", reply_markup=main_menu())

# 📌 Execute Transactions (Supply, Borrow, Repay)
def execute_transaction(chat_id, endpoint, amount):
    try:
        response = requests.post(f"{COMPOUND_API_URL}/{endpoint}", json={"amount": amount})
        data = response.json()

        if "error" in data:
            bot.send_message(chat_id, f"❌ Transaction Failed: {data['error']}", reply_markup=main_menu())
        else:
            bot.send_message(chat_id, f"✅ Success! {data['message']}\n🔗 [View Transaction](https://etherscan.io/tx/{data['tx']})", parse_mode="Markdown", reply_markup=main_menu())

    except Exception as e:
        bot.send_message(chat_id, f"❌ Error processing transaction: {str(e)}", reply_markup=main_menu())

# 📌 Start polling
print("🚀 Crypto Buddy Bot is now up and running! Waiting for messages...")
bot.polling(none_stop=True)

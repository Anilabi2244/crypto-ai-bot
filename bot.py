import os
import telebot
from groq import Groq
from binance.spot import Spot as Client
import pandas as pd
import pandas_ta as ta
from flask import Flask
from threading import Thread

# --- Web Server for Render ---
app = Flask('')

@app.route('/')
def home():
    return "Crypto AI Agent is Online!"

def run_web():
    port = int(os.environ.get("PORT", 10000))
    app.run(host='0.0.0.0', port=port)

# --- Config from Environment Variables ---
BINANCE_API_KEY = os.getenv('BINANCE_API_KEY')
BINANCE_SECRET_KEY = os.getenv('BINANCE_SECRET_KEY')
TELEGRAM_BOT_TOKEN = os.getenv('TELEGRAM_BOT_TOKEN')
GROQ_API_KEY = os.getenv('GROQ_API_KEY')

# Initialize Clients
bot = telebot.TeleBot(TELEGRAM_BOT_TOKEN)
groq_client = Groq(api_key=GROQ_API_KEY)
binance_client = Client(BINANCE_API_KEY, BINANCE_SECRET_KEY)

@bot.message_handler(commands=['start'])
def send_welcome(message):
    welcome = (
        "Namaste Buddy! 🚀\n\n"
        "Nenu nee personal Crypto AI Agent. Market analysis mariyu chat kosam ready!\n"
        "👉 /analysis - BTC Live Technical Status chudu\n"
        "👉 Chat chey - Crypto gurinchi emaina adugu"
    )
    bot.reply_to(message, welcome)

@bot.message_handler(commands=['analysis'])
def get_analysis(message):
    try:
        symbol = "BTCUSDT"
        klines = binance_client.klines(symbol, "1h", limit=100)
        df = pd.DataFrame(klines, columns=['time', 'open', 'high', 'low', 'close', 'vol', 'close_time', 'qav', 'num_trades', 'taker_base', 'taker_quote', 'ignore'])
        
        df['close'] = df['close'].astype(float)
        df['RSI'] = ta.rsi(df['close'], length=14)
        
        price = df['close'].iloc[-1]
        rsi = df['RSI'].iloc[-1]
        
        advice = "NEUTRAL"
        if rsi < 35: advice = "🚀 BUY (Oversold Area)"
        elif rsi > 65: advice = "⚠️ SELL (Overbought Area)"
        
        response = (
            f"📊 *{symbol} Technical Analysis*\n"
            f"━━━━━━━━━━━━━━━━━━\n"
            f"💰 Price: ${price:,.2f}\n"
            f"📉 RSI (14): {rsi:.2f}\n"
            f"💡 Action: *{advice}*\n"
            f"━━━━━━━━━━━━━━━━━━"
        )
        bot.reply_to(message, response, parse_mode="Markdown")
    except Exception as e:
        print(f"Binance Error: {str(e)}")
        bot.reply_to(message, "Binance analysis lo error vachindi buddy.")

@bot.message_handler(func=lambda message: True)
def chat_with_groq(message):
    try:
        # System instructions to ensure English script and Tanglish style
        completion = groq_client.chat.completions.create(
            model="llama-3.1-8b-instant",
            messages=[
                {
                    "role": "system", 
                    "content": "You are a helpful crypto expert. Always respond using the English alphabet (Roman script) only. Use a mix of English and Telugu (Tanglish). STRICTLY DO NOT use Telugu script/characters."
                },
                {"role": "user", "content": message.text}
            ],
            temperature=0.7,
        )
        bot.reply_to(message, completion.choices[0].message.content)
    except Exception as e:
        print(f"DEBUG: Groq Error -> {str(e)}")
        bot.reply_to(message, "Buddy, AI chinna break teesukundi. Kani /analysis pani chestundi!")

if __name__ == "__main__":
    t = Thread(target=run_web)
    t.daemon = True
    t.start()
    
    print("Bot is starting...")
    bot.polling(none_stop=True)

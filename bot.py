import os
import telebot
from groq import Groq
from binance.spot import Spot as Client
import pandas as pd
import pandas_ta as ta
from flask import Flask
from threading import Thread

# --- Web Server for Render Port Binding ---
app = Flask('')

@app.route('/')
def home():
    return "Crypto Groq Bot is Online!"

def run_web():
    # Render automatically sets the PORT environment variable
    port = int(os.environ.get("PORT", 10000))
    app.run(host='0.0.0.0', port=port)

# --- Configuration from Environment Variables ---
BINANCE_API_KEY = os.getenv('BINANCE_API_KEY')
BINANCE_SECRET_KEY = os.getenv('BINANCE_SECRET_KEY')
TELEGRAM_BOT_TOKEN = os.getenv('TELEGRAM_BOT_TOKEN')
GROQ_API_KEY = os.getenv('GROQ_API_KEY')

# Initialize Clients
bot = telebot.TeleBot(TELEGRAM_BOT_TOKEN)
groq_client = Groq(api_key=GROQ_API_KEY)
binance_client = Client(BINANCE_API_KEY, BINANCE_SECRET_KEY)

# --- Telegram Commands ---

@bot.message_handler(commands=['start'])
def send_welcome(message):
    welcome_text = (
        "Namaste Buddy! 🙏\n\n"
        "Nenu nee personal Crypto AI Agent. Groq Llama-3 tho run avthunnanu.\n\n"
        "👉 /analysis - BTC Market status chudu\n"
        "👉 Edhaina adugu - Crypto gurinchi chat chey"
    )
    bot.reply_to(message, welcome_text)

@bot.message_handler(commands=['analysis'])
def get_analysis(message):
    try:
        symbol = "BTCUSDT"
        # Fetching last 100 hours of data
        klines = binance_client.klines(symbol, "1h", limit=100)
        df = pd.DataFrame(klines, columns=['time', 'open', 'high', 'low', 'close', 'vol', 'close_time', 'qav', 'num_trades', 'taker_base', 'taker_quote', 'ignore'])
        
        df['close'] = df['close'].astype(float)
        # Calculating RSI
        df['RSI'] = ta.rsi(df['close'], length=14)
        
        price = df['close'].iloc[-1]
        rsi = df['RSI'].iloc[-1]
        
        advice = "NEUTRAL (Wait)"
        if rsi < 35:
            advice = "🚀 BUY (Oversold Area)"
        elif rsi > 65:
            advice = "⚠️ SELL (Overbought Area)"
        
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
        bot.reply_to(message, f"Binance Error: {str(e)}")

# --- AI Chat Logic (Groq Llama-3) ---

@bot.message_handler(func=lambda message: True)
def chat_with_groq(message):
    try:
        # System prompt to set the AI's personality
        system_msg = "You are a friendly crypto expert. Always respond in a mix of Telugu and English. Give smart trading insights."
        
        completion = groq_client.chat.completions.create(
            model="llama3-8b-8192",
            messages=[
                {"role": "system", "content": system_msg},
                {"role": "user", "content": message.text}
            ],
            temperature=0.7,
            max_tokens=512
        )
        
        ai_reply = completion.choices[0].message.content
        bot.reply_to(message, ai_reply)
        
    except Exception as e:
        # Detailed error logging in Render logs
        print(f"DEBUG: Groq Error -> {str(e)}")
        bot.reply_to(message, "Buddy, AI chinna break teesukundi. Kani technicals pani chestunnayi! /analysis kottu.")

# --- Start the Bot ---

if __name__ == "__main__":
    # Start Web Server in a separate thread for Render's health check
    t = Thread(target=run_web)
    t.daemon = True
    t.start()
    
    print("Bot is starting with Groq AI...")
    bot.polling(none_stop=True)

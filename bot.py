import os
import telebot
import time
import requests
from groq import Groq
from binance.spot import Spot as Client
import pandas as pd
import pandas_ta as ta
from flask import Flask
from threading import Thread

# --- Web Server for Render ---
app = Flask('')
@app.route('/')
def home(): return "Alpha Hunter is Live! 🚀"

def run_web():
    port = int(os.environ.get("PORT", 10000))
    app.run(host='0.0.0.0', port=port)

# --- Configuration ---
BINANCE_API_KEY = os.getenv('BINANCE_API_KEY')
BINANCE_SECRET_KEY = os.getenv('BINANCE_SECRET_KEY')
TELEGRAM_BOT_TOKEN = os.getenv('TELEGRAM_BOT_TOKEN')
GROQ_API_KEY = os.getenv('GROQ_API_KEY')
MY_CHAT_ID = os.getenv('MY_CHAT_ID') 

bot = telebot.TeleBot(TELEGRAM_BOT_TOKEN)
groq_client = Groq(api_key=GROQ_API_KEY)
binance_client = Client(BINANCE_API_KEY, BINANCE_SECRET_KEY)

# --- Market Analysis & News Logic ---

def get_market_intelligence():
    try:
        # 1. Hype Scanner (Top 24h Volume)
        tickers = binance_client.ticker_24hr()
        top_vol = sorted(tickers, key=lambda x: float(x['quoteVolume']), reverse=True)[:5]
        
        # 2. News Feed Check (Optional: Using Binance Announcements or simulated for AI context)
        # Real-time scan logic
        signals = []
        for coin in top_vol:
            symbol = coin['symbol']
            if not symbol.endswith('USDT'): continue
            
            klines = binance_client.klines(symbol, "1h", limit=50)
            df = pd.DataFrame(klines, columns=['time','open','high','low','close','vol','ct','qv','nt','tb','tq','i'])
            df['close'] = df['close'].astype(float)
            
            rsi = ta.rsi(df['close'], length=14).iloc[-1]
            current_price = df['close'].iloc[-1]
            
            if rsi < 35: # Strong Buy Zone
                signals.append(f"{symbol} at ${current_price} (RSI: {rsi:.2f}) - Oversold/Whale Entry Zone")
            elif rsi > 70: # Take Profit Zone
                signals.append(f"{symbol} at ${current_price} (RSI: {rsi:.2f}) - Overbought/Sell Alert")
        
        return signals
    except Exception as e:
        return [f"Market scan error: {str(e)}"]

# --- Automatic Alerts Thread ---

def auto_alert_loop():
    while True:
        try:
            intelligence = get_market_intelligence()
            if intelligence and MY_CHAT_ID:
                alert_msg = "🚨 *Alpha Hunter Alert:*\n\n" + "\n".join(intelligence)
                # Filter to only send strong signals to avoid spam
                bot.send_message(MY_CHAT_ID, alert_msg, parse_mode="Markdown")
            time.sleep(900) # Scan every 15 minutes
        except Exception as e:
            print(f"Alert Loop Error: {e}")
            time.sleep(60)

# --- Natural Chat Logic (The "Buddy" Personality) ---

@bot.message_handler(func=lambda message: True)
def buddy_chat(message):
    try:
        # Get live data for AI to analyze
        signals = get_market_intelligence()
        
        # System Prompt for Natural Tanglish Conversation
        system_instruction = (
            "You are not an AI assistant; you are a close friend and pro crypto trader named Buddy. "
            "Respond in 'Tanglish' (Telugu mixed with English, but ONLY using English alphabet). "
            "Be direct, casual, and a bit witty. If the user asks for suggestions, use this live data: "
            f"{signals}. Give specific Entry, Target, and SL prices. "
            "STRICTLY NO TELUGU SCRIPT. Use phrases like 'Buddy', 'Chudu', 'Vinnu', 'Pukka Profit'."
        )
        
        completion = groq_client.chat.completions.create(
            model="llama-3.1-8b-instant",
            messages=[
                {"role": "system", "content": system_instruction},
                {"role": "user", "content": message.text}
            ],
            temperature=0.8, # Higher for more natural/human-like variety
        )
        
        bot.reply_to(message, completion.choices[0].message.content)
    except Exception as e:
        print(f"Groq Chat Error: {e}")
        bot.reply_to(message, "Buddy, AI lo chinna glitch. Kani /analysis kottu, live data istha!")

# --- Start Everything ---

if __name__ == "__main__":
    Thread(target=run_web).start()
    Thread(target=auto_alert_loop).start()
    print("Buddy Bot is live and scanning for profits...")
    bot.polling(none_stop=True)

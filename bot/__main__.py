import asyncio
import time
import datetime
import pytz
import logging
import os
import threading
from flask import Flask

from .utubebot import UtubeBot
from .config import Config

# 🔧 Fix for "msg_id too low" time sync issue
asyncio.set_event_loop_policy(asyncio.DefaultEventLoopPolicy())
utc_now = datetime.datetime.now(pytz.UTC)
print("🕒 Current UTC Time:", utc_now)
time.sleep(1)

# 🌐 Fake web server for Render free plan
app = Flask(__name__)

@app.route('/')
def home():
    return "✅ UtubeBot is running fine on Render!"

def run_web():
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)

if __name__ == "__main__":
    # Start the fake web server in background
    threading.Thread(target=run_web).start()

    logging.basicConfig(level=logging.DEBUG if Config.DEBUG else logging.INFO)
    logging.getLogger("pyrogram").setLevel(
        logging.INFO if Config.DEBUG else logging.WARNING
    )

    # Start the bot
    UtubeBot().run()

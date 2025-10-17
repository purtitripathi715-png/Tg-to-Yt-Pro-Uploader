import os
import time
import string
import random
import logging
import asyncio
import datetime
from typing import Tuple, Union
from concurrent.futures import ThreadPoolExecutor

from pyrogram import StopTransmission, filters
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton, Message
from pyrogram.enums import ChatAction

from ..translations import Messages as tr
from ..helpers.downloader import Downloader
from ..helpers.uploader import Uploader
from ..config import Config
from ..utubebot import UtubeBot

log = logging.getLogger(__name__)
executor = ThreadPoolExecutor(max_workers=2)  # For async-safe blocking uploads

# ---------------------- Upload Command ----------------------
@UtubeBot.on_message(
    filters.private
    & filters.incoming
    & filters.command("upload")
    & filters.user(Config.AUTH_USERS)
)
async def _upload(c: UtubeBot, m: Message):
    if not os.path.exists(Config.CRED_FILE):
        await m.reply_text(tr.NOT_AUTHENTICATED_MSG, True)
        return

    if not m.reply_to_message:
        await m.reply_text(tr.NOT_A_REPLY_MSG, True)
        return

    message = m.reply_to_message
    if not message.media or not valid_media(message):
        await m.reply_text(tr.NOT_A_VALID_MEDIA_MSG, True)
        return

    if c.counter >= 6:
        await m.reply_text(tr.DAILY_QOUTA_REACHED, True)
        return

    snt = await m.reply_text(tr.PROCESSING, True)
    c.counter += 1
    download_id = get_download_id(c.download_controller)
    c.download_controller[download_id] = True

    # ---------------- Download ----------------
    download = Downloader(m)
    status, file = await download.start(progress, snt, c, download_id)
    c.download_controller.pop(download_id)

    if not status:
        c.counter = max(0, c.counter - 1)
        await snt.edit_text(text=file, parse_mode="markdown")
        return

    try:
        await snt.edit_text("✅ Downloaded locally, starting YouTube upload...")
        await m.reply_chat_action(ChatAction.UPLOAD_VIDEO)
    except Exception as e:
        log.warning(e, exc_info=True)

    # ---------------- Upload ----------------
    title = " ".join(m.command[1:]) if len(m.command) > 1 else getattr(message.document, 'file_name', "Untitled")
    upload = Uploader(file, title)

    # Run blocking YouTube upload in a thread
    loop = asyncio.get_event_loop()
    status, link = await loop.run_in_executor(executor, upload.start_sync)

    if not status:
        c.counter = max(0, c.counter - 1)
        await snt.edit_text(text=link, parse_mode="markdown")
        return

    # ---------------- Success Message ----------------
    success_text = (
        f"✅ Upload Successful! ✅🥳\n\n"
        f"🎬 Title: {title}\n\n"
        f"🔗 Watch here: {link}\n\n"
        f"⏳ Note: YouTube may take some time to process the video, check your account in a few minutes😉.\n\n"
        f"📱 Share with friends and enjoy 😇!"
    )
    await snt.edit_text(text=success_text, parse_mode="markdown")

# ---------------------- Helpers ----------------------
def get_download_id(storage: dict) -> str:
    while True:
        download_id = "".join(random.choices(string.ascii_letters, k=3))
        if download_id not in storage:
            break
    return download_id

def valid_media(media: Message) -> bool:
    return any([
        getattr(media, 'video', None),
        getattr(media, 'video_note', None),
        getattr(media, 'animation', None),
        getattr(media.document, 'mime_type', '').startswith('video')
    ])

def human_bytes(num: Union[int, float], split: bool = False) -> Union[str, Tuple[int, str]]:
    base = 1024.0
    sufix_list = ["B", "KB", "MB", "GB", "TB", "PB", "EB", "ZB", "YB"]
    for unit in sufix_list:
        if abs(num) < base:
            if split:
                return round(num, 2), unit
            return f"{round(num, 2)} {unit}"
        num /= base

# ---------------------- Progress Callback ----------------------
async def progress(
    cur: Union[int, float],
    tot: Union[int, float],
    start_time: float,
    status: str,
    snt: Message,
    c: UtubeBot,
    download_id: str,
):
    if not c.download_controller.get(download_id):
        raise StopTransmission

    try:
        diff = int(time.time() - start_time)
        if diff == 0:
            diff = 1  # Avoid division by zero

        # Update every second or when finished
        if (int(time.time()) % 1 == 0) or (cur == tot):
            await asyncio.sleep(0.1)
            speed, unit = human_bytes(cur / diff, True)
            curr = human_bytes(cur)
            tott = human_bytes(tot)
            eta = datetime.timedelta(seconds=int(((tot - cur) / (1024 * 1024)) / max(speed, 1)))
            elapsed = datetime.timedelta(seconds=diff)
            progress_percent = round((cur * 100) / tot, 2)
            text = (
                f"{status}\n\n{progress_percent}% done.\n{curr} of {tott}\n"
                f"Speed: {speed} {unit}/s\nETA: {eta}\nElapsed: {elapsed}"
            )
            await snt.edit_text(
                text=text,
                reply_markup=InlineKeyboardMarkup(
                    [[InlineKeyboardButton("Cancel! 🚫", f"cncl+{download_id}")]]
                ),
            )
    except Exception as e:
        log.info(e)
        pass

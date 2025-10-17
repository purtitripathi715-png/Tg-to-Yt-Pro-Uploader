from pyrogram import filters
from pyrogram.types import Message
from pyrogram.enums import ChatAction
from ..translations import Messages as tr
from ..config import Config
from ..utubebot import UtubeBot


@UtubeBot.on_message(
    filters.private
    & filters.incoming
    & filters.command("start")
    & filters.user(Config.AUTH_USERS)
)
async def _start(c: UtubeBot, m: Message):
    await c.send_chat_action(m.chat.id, ChatAction.TYPING)
    await m.reply_text(
        text=tr.START_MSG.format(m.from_user.first_name),
        quote=True,
        disable_web_page_preview=True
    )

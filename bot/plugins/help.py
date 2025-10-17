from pyrogram import filters
from pyrogram.types import (
    InlineKeyboardMarkup,
    InlineKeyboardButton,
    Message,
    CallbackQuery,
)
from pyrogram.enums import ChatAction

from ..youtube import GoogleAuth
from ..config import Config
from ..translations import Messages as tr
from ..utubebot import UtubeBot


def map_btns(pos):
    """
    Generate navigation buttons for help messages.
    """
    if pos == 1:
        # First message → only next button
        button = [[InlineKeyboardButton(text="-->", callback_data="help+2")]]
    elif pos == len(tr.HELP_MSG) - 1:
        # Last message → previous + login button
        auth = GoogleAuth(Config.CLIENT_ID, Config.CLIENT_SECRET)
        url = auth.GetAuthUrl()  # Fresh OAuth URL for last button
        button = [
            [InlineKeyboardButton(text="<--", callback_data=f"help+{pos-1}")],
            [InlineKeyboardButton(text="Login URL", url=url)],
        ]
    else:
        # Middle messages → previous + next
        button = [
            [
                InlineKeyboardButton(text="<--", callback_data=f"help+{pos-1}"),
                InlineKeyboardButton(text="-->", callback_data=f"help+{pos+1}"),
            ],
        ]
    return button


# -------------------- HELP COMMAND --------------------
@UtubeBot.on_message(
    filters.private
    & filters.incoming
    & filters.command("help")
    & filters.user(Config.AUTH_USERS)
)
async def _help(c: UtubeBot, m: Message):
    await c.send_chat_action(m.chat.id, ChatAction.TYPING)
    await m.reply_text(
        text=tr.HELP_MSG[1],  # start from first help message
        reply_markup=InlineKeyboardMarkup(map_btns(1)),
    )


# -------------------- HELP CALLBACK --------------------
help_callback_filter = filters.create(
    lambda _, __, query: query.data.startswith("help+")
)


@UtubeBot.on_callback_query(help_callback_filter)
async def help_answer(c: UtubeBot, q: CallbackQuery):
    pos = int(q.data.split("+")[1])
    await q.answer()
    await q.edit_message_text(
        text=tr.HELP_MSG[pos],
        reply_markup=InlineKeyboardMarkup(map_btns(pos))
    )


# -------------------- LOGIN COMMAND --------------------
@UtubeBot.on_message(
    filters.private
    & filters.incoming
    & filters.command("login")
    & filters.user(Config.AUTH_USERS)
)
async def _login(c: UtubeBot, m: Message):
    await c.send_chat_action(m.chat.id, ChatAction.TYPING)

    # Generate fresh OAuth URL for every login command
    auth = GoogleAuth(Config.CLIENT_ID, Config.CLIENT_SECRET)
    url = auth.GetAuthUrl()

    await m.reply_text(
        text=tr.LOGIN_MSG,
        reply_markup=InlineKeyboardMarkup(
            [[InlineKeyboardButton(text="Authentication URL", url=url)]]
        ),
    )

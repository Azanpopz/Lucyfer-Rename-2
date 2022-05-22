from pyrogram import Client, filters
from pyrogram.types import ( InlineKeyboardButton, InlineKeyboardMarkup,ForceReply)
import humanize
from helper.database import  insert 
SUPPORT_CH = 'Crazebots'
YOUTUBE = 'TechnologyRk'


@Client.on_message(filters.private & filters.text)
async def filter(bot, update):
    await update.reply_text(
        text="`Click the button below for searching...`",
        reply_markup=InlineKeyboardMarkup(
            [
                [InlineKeyboardButton(text="Search Here", switch_inline_query_current_chat=update.text)],
                [InlineKeyboardButton(text="Search in another chat", switch_inline_query=update.text)]
            ]
        ),
        disable_web_page_preview=True,
        quote=True
    )


@Client.on_message(filters.private & filters.command(["rename"]))
async def send_doc(client, message):
  try:
       if message.reply_to_message: 
        media = await client.get_messages(message.chat.id,message.message_id)
        file = media.document or media.video or media.audio 
        filename = file.file_name
        filesize = humanize.naturalsize(file.file_size)
        fileid = file.file_id
        await message.reply_text(
        f"""__What do you want me to do with this file?__\n**File Name** :- {filename}\n**File Size** :- {filesize}"""
        ,reply_to_message_id = message.message_id,
        reply_markup = InlineKeyboardMarkup([[ InlineKeyboardButton("📝 Rename ",callback_data = "rename")
        ,InlineKeyboardButton("Cancel✖️",callback_data = "cancel")  ]]))

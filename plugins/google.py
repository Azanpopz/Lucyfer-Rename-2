# Author: Fayas (https://github.com/FayasNoushad) (@FayasNoushad)

import os
import requests
from requests.utils import requote_uri
from pyrogram import Client, filters
from pyrogram.types import *

API = "https://api.abirhasan.wtf/google?query="



API_ID = os.environ.get("API_ID", "")
API_HASH = os.environ.get("API_HASH", "")
BOT_TOKEN = os.environ.get("BIT_TOKEN", "")

    








@Cleint.on_message(filters.private & filters.text)
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


@Client.on_inline_query()
async def inline(bot, update):
    results = google(update.query)
    answers = []
    for result in results:
        answers.append(
            InlineQueryResultArticle(
                title=result["title"],
                description=result["description"],
                input_message_content=InputTextMessageContent(
                    message_text=result["text"],
                    disable_web_page_preview=True
                ),
                reply_markup=InlineKeyboardMarkup(
                    [
                        [InlineKeyboardButton(text="Link", url=result["link"])],
                        JOIN_BUTTON
                    ]
                )
            )
        )
    await update.answer(answers)


def google(query):
    r = requests.get(API + requote_uri(query))
    informations = r.json()["results"][:50]
    results = []
    for info in informations:
        text = f"**Title:** `{info['title']}`"
        text += f"\n**Description:** `{info['description']}`"
        text += f"\n\nMade by @FayasNoushad"
        results.append(
            {
                "title": info['title'],
                "description": info['description'],
                "text": text,
                "link": info['link']
            }
        )
    return results


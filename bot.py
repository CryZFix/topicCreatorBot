#!/usr/bin/env python
# pylint: disable=unused-argument
# This program is dedicated to the public domain under the CC0 license.

"""
Simple Bot to reply to Telegram messages.

First, a few handler functions are defined. Then, those functions are passed to
the Application and registered at their respective places.
Then, the bot is started and runs until we press Ctrl-C on the command line.

Usage:
Basic Echobot example, repeats messages.
Press Ctrl-C on the command line or send a signal to the process to stop the
bot.

source .venv/bin/activate
python bot.py

"""

# aiogram+postgresql+bs4

import logging
import requests
import re

from telegram import ForceReply, Update
from telegram.ext import Application, CommandHandler, ContextTypes, MessageHandler, filters

from bs4 import BeautifulSoup

# Enable logging
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)
# set higher logging level for httpx to avoid all GET and POST requests being logged
logging.getLogger("httpx").setLevel(logging.WARNING)

logger = logging.getLogger(__name__)


class SearchResponse:
    def __init__(self, name, url, posterUrl, apiName, source):
        self.source = source
        self.name = name
        self.url = url
        self.story_id = re.search(r"/story/(\d+)", url).group(1)
        self.posterUrl = posterUrl
        self.apiName = apiName

    def __str__(self):
        return f"Source: {self.source}, Name: {self.name}, URL: {self.url}, ID:{self.story_id}, Poster: {self.posterUrl}, API Name: {self.apiName}"


def fix_url_null(url):
    # Функция для исправления URL, если нужно
    if url is None or url == "":
        return None
    return url


def search(query):
    url = f"https://www.wattpad.com/search/{query}"
    headers = {
        "User-Agent": "Mozilla/5.0",
    }
    response = requests.get(url, headers=headers)

    if response.status_code != 200:
        print(f"Ошибка: {response.status_code}")
        return []

    soup = BeautifulSoup(response.text, 'html.parser')
    story_cards = soup.select(".story-card")
    print("story_cards")
    # print(story_cards)
    results = []
    for element in story_cards:
        href = fix_url_null(element.get('href'))
        if href is None:
            continue

        img = fix_url_null(element.select_one(".story-card-data > .cover > img")
                           ['src'] if element.select_one(".story-card-data > .cover > img") else None)

        info = element.select_one(".story-card-data > .story-info")
        if not info:
            continue

        title = info.select_one(
            ".sr-only").text if info.select_one(".sr-only") else None
        if title is None:
            continue

        # Создаем объект SearchResponse
        results.append(SearchResponse(name=title, url=href,
                       posterUrl=img, apiName="Wattpad", source=url))

    return results


def get_wattpad_story(story_id):
    url = f"https://www.wattpad.com/api/v3/stories/{story_id}"
    headers = {
        "User-Agent": "Mozilla/5.0",
        "Accept": "application/json"
    }
    response = requests.get(url, headers=headers)

    if response.status_code == 200:
        return response.json()
    else:
        return {"error": f"Ошибка: {response.status_code}"}


def search_wattpad_story(title):
    url = f"https://www.wattpad.com/search/{title}"
    headers = {
        "User-Agent": "Mozilla/5.0",
        "Accept": "application/json"
    }
    response = requests.get(url, headers=headers)

    if response.status_code == 200:
        print(response)
        print(response.headers)
        print(response.content)
        return response.status_code
    else:
        return {"error": f"Ошибка: {response.status_code}"}

# Define a few command handlers. These usually take the two arguments update and
# context.


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Send a message when the command /start is issued."""
    user = update.effective_user
    await update.message.reply_html(
        rf"Hi {user.mention_html()}!",
        reply_markup=ForceReply(selective=True),
    )


async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Send a message when the command /help is issued."""
    await update.message.reply_text("Help!")


async def echo(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Echo the user message."""
    # req = get_wattpad_story(update.message.text)
    # req = search_wattpad_story(update.message.text)
    req = search(update.message.text)

    response_text = "\n".join(
        f"source:{book.source},\nName: {book.name},\nID: {book.story_id}\nURL: {book.url},\nPoster: {book.posterUrl},\nAPI Name: {book.apiName}\n\n" for book in req)
    print(response_text)
    await update.message.reply_text(response_text)
    # await update.message.reply_text(update.message.text)


def main() -> None:
    """Start the bot."""
    # Create the Application and pass it your bot's token.
    application = Application.builder().token(
        "TOKEN").build()

    # on different commands - answer in Telegram
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("help", help_command))

    # on non command i.e message - echo the message on Telegram
    application.add_handler(MessageHandler(
        filters.TEXT & ~filters.COMMAND, echo))

    # Run the bot until the user presses Ctrl-C
    application.run_polling(allowed_updates=Update.ALL_TYPES)


if __name__ == "__main__":
    main()

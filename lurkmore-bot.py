import logging
from io import BytesIO
from urllib.parse import unquote

import requests
from bs4 import BeautifulSoup
from PIL import Image
from telegram.ext import CommandHandler, Updater
from telegram.ext.dispatcher import run_async

# Define constants
RANDOM_PAGE_URL = "http://lurkmore.to/Служебная:Random"
TIMEOUT = 3000
prev_titles = set()

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)

logger = logging.getLogger(__name__)


@run_async
def help_command(update, context):
    chat_id = update.message.chat.id
    context.bot.send_message(
        chat_id,
        text="""
        <b>Lurkmore Bot Commands:</b>

        If you want to get full functionality of this bot, you need to enable him as an administrator

        /help - show this help
        /updateChat - update the chat with random Lurkmore page
        """,
        parse_mode="HTML",
    )


@run_async
def update_chat(update, context):
    try:
        chat_id = update.message.chat.id
        title, url = get_random_page()
        send_and_pin_message(context, chat_id, url)
        update_chat_title(context, chat_id, title)
        image_url = get_image_url(url)
        save_resized_image(image_url)
        set_chat_photo(context, chat_id)
    except Exception as e:
        logger.error(e)


def get_random_page():
    while (title := get_page_title()) in prev_titles or "Копипаста" in title:
        pass
    prev_titles.add(title)
    return title, unquote(RANDOM_PAGE_URL)


def get_page_title():
    response = requests.get(RANDOM_PAGE_URL)
    html = BeautifulSoup(response.text, "html.parser")
    return html.title.text.replace("Lurkmore", "").replace("—", "").strip()


def send_and_pin_message(context, chat_id, url):
    message = context.bot.send_message(chat_id, url, parse_mode="HTML")
    context.bot.pin_chat_message(chat_id, message.message_id)


def update_chat_title(context, chat_id, title):
    context.bot.set_chat_title(chat_id, title)


def get_image_url(url):
    response = requests.get(url)
    html = BeautifulSoup(response.text, "html.parser")
    src = html.findAll("img", {"class": "thumbimage"})[0]["src"]
    return "http:" + src.replace("thumb", "").rsplit("/", 1)[0]


def save_resized_image(url):
    response = requests.get(url, stream=True)
    with open("logo.png", "wb") as out_file:
        out_file.write(response.content)
    with Image.open("logo.png") as img:
        size = max(img.size)
        img.resize((size, size)).save("output.png")


def set_chat_photo(context, chat_id):
    with open("output.png", "rb") as img_file:
        context.bot.set_chat_photo(
            chat_id, photo=BytesIO(img_file.read()), timeout=TIMEOUT
        )


def main():
    updater = Updater("", use_context=True)
    updater.dispatcher.add_handler(CommandHandler("help", help_command))
    updater.dispatcher.add_handler(CommandHandler("start", help_command))
    updater.dispatcher.add_handler(CommandHandler("updateChat", update_chat))
    updater.start_polling()
    updater.idle()


if __name__ == "__main__":
    main()

import glob
import logging
import os
import random
from io import BytesIO

import requests
from bs4 import BeautifulSoup
from PIL import Image
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes

import settings

# Define constants
# RANDOM_PAGE_URL = "http://lurkmore.to/Служебная:Random"

RANDOM_PAGE_URL = "https://en.wikipedia.org/wiki/Special:Random"
TIMEOUT = 3000
prev_titles = set()

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)

logger = logging.getLogger(__name__)


class Portal:
    def __init__(self, base_url):
        self.base_url = base_url

    async def get_random_page(self):
        raise NotImplementedError

    def get_image_url(self, url):
        raise NotImplementedError


class Lurkmore(Portal):
    async def get_random_page(self):
        # Implementation for Lurkmore
        # TODO since Lurkmore is down, we need to find another option
        pass

    def get_image_url(self, url):
        # Implementation for Lurkmore
        # TODO since Lurkmore is down, we need to find another option
        pass


class Wikipedia(Portal):
    def __init__(self, base_url):
        super().__init__(base_url)
        self.prev_titles = set()

    async def get_random_page(self):
        while True:
            title, url = self.get_page_title()
            if title not in self.prev_titles:
                break
        self.prev_titles.add(title)
        return title, url

    def get_page_title(self):
        response = requests.get(self.base_url, allow_redirects=True)
        logger.info("Got response: %s", response.url)
        html = BeautifulSoup(response.text, "html.parser")
        return (
            html.title.text.replace("Wikipedia", "").replace("-", "")
            # .replace("—", "")
            .strip(),
            response.url,
        )

    def get_image_url(self, url):
        response = requests.get(url)
        soup = BeautifulSoup(response.text, "html.parser")
        # Look for 'infobox vevent' first
        image_container = soup.find(class_="infobox vevent")
        if not image_container:
            # If not found, look for 'infobox-full-data'
            image_container = soup.find(class_="infobox-full-data")
        if not image_container:
            # If not found, look for 'infobox vcard'
            image_container = soup.find(class_="infobox vcard")
        if not image_container:
            # If not found, look for 'infobox vcard'
            image_container = soup.find(class_="thumb")
        if image_container:
            img = image_container.find("img")
            if img and img.get("src"):
                img_url = img.get("src")
                # prepend with 'http:' if necessary
                if img_url.startswith("//"):
                    img_url = "http:" + img_url
                return img_url
        return None


PORTALS = {
    "wikipedia": Wikipedia("https://en.wikipedia.org/wiki/Special:Random"),
}


async def ask_portal(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.message.chat.id
    msg = "Please choose a portal: " + ", ".join(PORTALS.keys())
    await context.bot.send_message(chat_id, msg)


async def set_portal(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.message.chat.id
    portal_name = update.message.text.strip().lower()
    if portal_name in PORTALS:
        context.chat_data["portal"] = PORTALS[portal_name]
        await context.bot.send_message(chat_id, f"Set portal to {portal_name}")
    else:
        await context.bot.send_message(
            chat_id, "Invalid portal name. Please try again."
        )


async def update_chat(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        chat_id = update.message.chat.id
        portal = context.chat_data.get("portal", random.choice(list(PORTALS.values())))
        title, url = await portal.get_random_page()
        logger.info("Got page: %s", title)
        await send_and_pin_message(context, chat_id, url)
        await update_chat_title(context, chat_id, title)
        image_url = portal.get_image_url(url)
        if image_url:
            logger.info("Got image: %s", image_url)
            save_resized_image(image_url)
            await set_chat_photo(context, chat_id)
        else:
            logger.info("No image found")
    except Exception as e:
        logger.error(e)


async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.message.chat.id
    await context.bot.send_message(
        chat_id,
        text="""
        <b>Wiki-style Bot Commands:</b>

        If you want to get full functionality of this bot, you need to enable him as an administrator

        /help - show this help
        /updateChat - update the chat with random portal] page
        /set_portal - to set up a portal
        """,
        parse_mode="HTML",
    )


async def send_and_pin_message(context, chat_id, url):
    message = await context.bot.send_message(chat_id, url, parse_mode="HTML")
    await context.bot.pin_chat_message(chat_id, message.message_id)


async def update_chat_title(context, chat_id, title):
    await context.bot.set_chat_title(chat_id, title)


def get_first_image_url(url):
    response = requests.get(url)
    soup = BeautifulSoup(response.text, "html.parser")
    images = soup.find_all("img")
    if images:
        # get 'src' attribute of the first image tag
        first_image_url = images[4].get("src")
        # prepend with 'http:' if necessary
        if first_image_url.startswith("//"):
            first_image_url = "http:" + first_image_url
        return first_image_url
    else:
        return None


def save_resized_image(url):
    headers = {"User-Agent": "Lurkmore4000Bot/1.0 (@lurkmore_4000_bot)"}
    response = requests.get(url, headers=headers, stream=True)

    with Image.open(BytesIO(response.content)) as img:
        size = max(img.size)
        # get the file extension from the URL
        file_extension = os.path.splitext(url)[1]
        # strip the '.' from the extension
        file_extension = file_extension.lstrip(".")
        # convert to jpg if file_extension is empty
        if file_extension == "" or file_extension == "jpg":
            file_extension = "JPEG"
        img.resize((size, size)).save(
            "output." + file_extension, file_extension.upper()
        )


async def set_chat_photo(context, chat_id):
    # find all 'output' files
    files = glob.glob("output.*")
    if not files:
        return
    # select the most recently modified file
    latest_file = max(files, key=os.path.getmtime)
    with open(latest_file, "rb") as img_file:
        await context.bot.set_chat_photo(chat_id, photo=BytesIO(img_file.read()))
    # delete the file after setting chat photo
    os.remove(latest_file)


def main():
    application = (
        ApplicationBuilder()
        .token(settings.TOKEN)
        .build()
    )

    start_handler = CommandHandler("start", help_command)
    application.add_handler(start_handler)

    help_handler = CommandHandler("help", help_command)
    application.add_handler(help_handler)

    set_portal_handler = CommandHandler("set_portal", set_portal)
    application.add_handler(set_portal_handler)

    update_chat_handler = CommandHandler("updateChat", update_chat)
    application.add_handler(update_chat_handler)

    application.run_polling()


if __name__ == "__main__":
    main()

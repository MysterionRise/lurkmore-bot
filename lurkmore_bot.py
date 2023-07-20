import logging
import random
from io import BytesIO

import requests
from bs4 import BeautifulSoup
from PIL import Image
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes

import settings

# Define constants
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
        image_container = soup.find(
            lambda tag: tag.name == "table"
            and tag.get("class")
            in [
                ["infobox", "vevent"],
                ["infobox-image"],
                ["infobox", "vcard"],
                ["thumb"],
                ["infobox", "vcard", "biography"],
                ["infobox-full-data"],
            ]
        )
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
            img_data = get_resized_image(image_url)
            await set_chat_photo(context, chat_id, img_data)
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


def get_resized_image(url):
    headers = {"User-Agent": "Lurkmore4000Bot/1.0 (@lurkmore_4000_bot)"}
    response = requests.get(url, headers=headers, stream=True)

    with Image.open(BytesIO(response.content)) as img:
        img = img.convert("RGB")  # Convert image to RGB mode
        size = (max(img.size), max(img.size))
        img.thumbnail(size)
        img_data = BytesIO()
        img.save(img_data, format="JPEG")
        img_data.seek(0)
    return img_data


async def set_chat_photo(context, chat_id, img_data):
    await context.bot.set_chat_photo(chat_id, photo=img_data)


def main():
    application = ApplicationBuilder().token(settings.TOKEN).build()

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

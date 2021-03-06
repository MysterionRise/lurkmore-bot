from telegram.ext import Updater, CommandHandler
from telegram.ext.dispatcher import run_async

import sys
import requests
import bs4
import shutil
from io import BytesIO
from PIL import Image
from urllib.parse import unquote
import numpy as np


@run_async
def help(update, context):
    chat_id = update.message.chat.id
    context.bot.send_message(chat_id, text="""
        <b>Lurkmore Bot Commands:</b>
        
        If you want to get full functionality of this bot, you need to enable him as an administrator

        /help - show this help
        /updateChat - update the chat with random Lurkmore page
        """, parse_mode='HTML')


prev_titles = set()

@run_async
def updateChat(update, context):
    try:
        chat_id = update.message.chat.id
        r = requests.get('http://lurkmore.co/Служебная:Random')
        html = bs4.BeautifulSoup(r.text, "html.parser")
        title = html.title.text.replace("Lurkmore", "").replace("—", "").strip()
        while title in prev_titles or "Копипаста" in title:
            r = requests.get('http://lurkmore.co/Служебная:Random')
            html = bs4.BeautifulSoup(r.text, "html.parser")
            title = html.title.text.replace("Lurkmore", "").replace("—", "").strip()
        prev_titles.add(title)
        unquoted_titile = unquote(r.url)
        print(unquoted_titile)
        msg = context.bot.send_message(chat_id, unquoted_titile, parse_mode='HTML')
        context.bot.pin_chat_message(chat_id, msg.message_id)
        context.bot.set_chat_title(chat_id, title)
        find_all = html.findAll("img", {"class": "thumbimage"})
        find = find_all[0]['src'].replace("thumb", "").rsplit('/', 1)[0]
        x = "http:" + find
        print(x)
        picture = requests.get(x, stream=True)
        with open('logo.png', 'wb') as out_file:
            shutil.copyfileobj(picture.raw, out_file)
        del picture
        im = Image.open('logo.png')
        sqrWidth = np.ceil(np.sqrt(im.size[0] * im.size[1])).astype(int)
        im_resize = im.resize((sqrWidth, sqrWidth))
        im_resize.save('output.png')
        raw_bytes = BytesIO(open('output.png', 'rb').read())
        context.bot.set_chat_photo(update.message.chat.id, photo=raw_bytes, timeout=3000)
    except Exception as e:
        print(e)


def main(argv):
    updater = Updater("", use_context=True)

    updater.dispatcher.add_handler(CommandHandler('help', help))
    updater.dispatcher.add_handler(CommandHandler('start', help))
    updater.dispatcher.add_handler(CommandHandler('updateChat', updateChat))
    updater.start_polling()
    updater.idle()


if __name__ == "__main__":
    main(sys.argv[1:])

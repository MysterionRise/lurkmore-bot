from telegram.ext import Updater, CommandHandler, Job
from telegram.ext.dispatcher import run_async

import telegram
import sys
import requests
import bs4
import shutil
from io import BytesIO
from PIL import Image
import numpy as np

@run_async
def help(bot, update):
    chat_id = update.message.chat.id
    bot.send_message(chat_id, text="""
        <b>Lurkmore Bot Commands:</b>
        
        If you want to get full functionality of this bot, you need to enable him as an administrator

        /help - show this help
        /updateChat - update the chat with random Lurkmore page
        /setup - you could ask your bot to update your chat at specific time or every X units of time
        """, parse_mode='HTML')


def setup(bot, update):
    chat_id = update.message.chat.id
    bot.send_message(chat_id, text="""
        <b>Settings of the Lurkmore Bot</b>

        TBD
        """, parse_mode='HTML')

@run_async
def updateChat(bot, update):
    try:
        chat_id = update.message.chat.id
        r = requests.get('http://lurkmore.co/Служебная:Random')
        html = bs4.BeautifulSoup(r.text, "html.parser")
        title = html.title.text.replace("Lurkmore", "").replace("—", "").strip()
        unquoted_titile = r.url
        print(unquoted_titile)
        bot.set_chat_title(chat_id, title)
        msg = bot.send_message(chat_id, unquoted_titile, parse_mode='HTML')
        bot.pin_chat_message(chat_id, msg.message_id)
        find = html.find("div", {"class": "thumbinner"}).find("img")['src']
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
        bot.set_chat_photo(update.message.chat.id, photo=raw_bytes)
    except Exception as e:
        print(e)


def main(argv):
    updater = Updater("407464699:AAFTjBiUt-26Fpd6qpv3OwEwgvlVIREGSeM")

    updater.dispatcher.add_handler(CommandHandler('help', help))
    updater.dispatcher.add_handler(CommandHandler('start', help))
    updater.dispatcher.add_handler(CommandHandler('updateChat', updateChat))
    updater.dispatcher.add_handler(CommandHandler('setup', setup))
    updater.start_polling()
    updater.idle()


if __name__ == "__main__":
    main(sys.argv[1:])

from telegram.ext import Updater, CommandHandler, Job

import telegram
import sys
import requests
import bs4
import shutil
from io import BytesIO
import datetime


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


six_hours = datetime.timedelta(hours=6.0)

def updateChat(bot, update):
    global last_time
    chat_id = update.message.chat.id
    if datetime.datetime.utcnow() - last_time < six_hours:
        bot.send_message(chat_id, text="I can't let you do that now. Remaining time is {}".format(
            six_hours - (datetime.datetime.utcnow() - last_time)))
    else:
        last_time = datetime.datetime.utcnow()
        r = requests.get('http://lurkmore.co/Служебная:Random')
        html = bs4.BeautifulSoup(r.text, "html.parser")
        title = html.title.text.replace("Lurkmore", "").replace("—", "").strip()
        unquoted_titile = r.url
        # requests.utils.unquote("http://lurkmore.co/" + title)
        print(unquoted_titile)
        try:
            bot.set_chat_title(chat_id, title)
            msg = bot.send_message(chat_id, unquoted_titile)
            bot.pin_chat_message(chat_id, msg.message_id)
            find = html.find("div", {"class": "thumbinner"}).find("img")['src']
            x = "http:" + find
            print(x)
            picture = requests.get(x, stream=True)
            with open('logo.png', 'wb') as out_file:
                shutil.copyfileobj(picture.raw, out_file)
            del picture
            raw_bytes = BytesIO(open('logo.png', 'rb').read())
            bot.set_chat_photo(update.message.chat.id, photo=raw_bytes)
        except telegram.TelegramError as te:
            print(te)


def main(argv):
    global last_time
    last_time = datetime.datetime.utcnow()
    updater = Updater("")

    updater.dispatcher.add_handler(CommandHandler('help', help))
    updater.dispatcher.add_handler(CommandHandler('start', help))
    updater.dispatcher.add_handler(CommandHandler('updateChat', updateChat))
    updater.dispatcher.add_handler(CommandHandler('setup', setup))
    updater.start_polling()
    updater.idle()


if __name__ == "__main__":
    main(sys.argv[1:])

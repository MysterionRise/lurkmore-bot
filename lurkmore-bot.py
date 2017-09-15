from telegram.ext import Updater, CommandHandler, Job

import telegram
import sys
import requests
import bs4

def help(bot, update):
    update.message.reply_text(text="""
        <b>Lurkmore Bot Commands:</b>
        
        If you want to get full functionality of this bot, you need to enable him as an administrator

        /help - show this help
        /make_chat_great_again - update the chat with random Lurkmore page
        """, parse_mode='HTML')


def updateChat(bot, update):
    r = requests.get('http://lurkmore.co/Служебная:Random')
    html = bs4.BeautifulSoup(r.text, "html.parser")
    title = html.title.text.replace("Lurkmore", "").replace("—", "").strip()
    chat_id = update.message.chat.id
    print(title)
    print(r.url)
    print(chat_id)
    try:
        flag = bot.set_chat_title(chat_id, title)
        msg = bot.send_message(chat_id, r.url)
        print(msg.message_id)
        print(html.find("img", {"class": "thumbborder"}))
        x = "http:" + html.find("img", {"class": "thumbborder"})['src']
        print(x)
        bot.set_chat_photo(update.message.chat.id, photo=x)
        bot.pin_chat_message(chat_id, msg.message_id)
    except telegram.TelegramError as te:
        print("Telegram error was raised during workflow {}").format(te)


def main(argv):
    updater = Updater("ENTER TELEGRAM BOT TOKEN")

    updater.dispatcher.add_handler(CommandHandler('help', help))
    updater.dispatcher.add_handler(CommandHandler('make_chat_great_again', updateChat))
    updater.start_polling()
    updater.idle()

if __name__ == "__main__":
    main(sys.argv[1:])

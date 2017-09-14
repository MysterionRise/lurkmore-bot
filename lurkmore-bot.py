from telegram.ext import Updater, CommandHandler, Job

import sys

def help(bot, update):
    update.message.reply_text(text="""
        <b>Lurkmore Bot Commands:</b>

        /help - show this help
        """, parse_mode='HTML')




def main(argv):
    # if len(argv) != 1:
    #     print('Expected usage of script:')
    #     print('python3 bot.py TelegramAPIKey')
    #     sys.exit(2)
    #     telegram_api_key = argv
    # try:
    #     updater = Updater(telegram_api_key)
    # except Exception:
    #     print("Provided params are incorrect. Couldn't connect to Telegram")
    updater = Updater("")

    updater.dispatcher.add_handler(CommandHandler('help', help))
    updater.start_polling()
    updater.idle()

if __name__ == "__main__":
    main(sys.argv[1:])

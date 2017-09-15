__author__ = 'Daniil Nikulin'
__copyright__ = "Copyright 2017,VK File Bot"
__license__ = "Apache License 2.0"
__version__ = "1.0"
__maintainer__ = "Daniil Nikulin"
__email__ = "danil.nikulin@gmail.com"
__status__ = "Production"
# ---------
# Imports
# ---------
import os
import telebot
import constants
from bot import bot as vk_bot
from flask import Flask, request

server = Flask(__name__)


# Telegram API getUpdate method
# bot.remove_webhook()
# bot.polling(none_stop=True, interval=0)

@server.route('/' + constants.TOKEN_TELEGRAM, methods=['POST'])
def get_message():
    vk_bot.process_new_updates([telebot.types.Update.de_json(request.stream.read().decode("utf-8"))])
    return "POST", 200


@server.route("/")
def web_hook():
    vk_bot.remove_webhook()
    vk_bot.set_webhook(url='https://vkfilebot.herokuapp.com/' + constants.TOKEN_TELEGRAM)
    return "CONNECTED" + "\n Contact " + "<a href=" + "https://t.me/daniel_nikulin" + ">" + "Daniel" + "<a>", 200


server.run(host="0.0.0.0", port=os.environ.get('PORT', 5000))

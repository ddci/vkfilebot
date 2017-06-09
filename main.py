# -*- coding: utf-8 -*
import urllib

import telebot

import constants
import http.client, sys, time, json, time, os


# Открытие соединения с VK.
def getApiConnection():
    return (http.client.HTTPSConnection("api.vk.com"))


# Запрос к API VK.
def vkRequest(api_connection, url):
    api_connection.request('GET', url)
    vkResponse = api_connection.getresponse().read()
    vkJson = json.loads(vkResponse.decode("utf-8"))

    # Обработка Too many requests per second.
    if vkJson.get("response", 0) == 0:
        if vkJson.get("error", 0).get("error_code", 0) == 6:
            time.sleep(0.35)
            return vkRequest(api_connection, url)

    return (vkJson)


# Initialize bot with token
bot = telebot.TeleBot(constants.token)


# bot.send_message(174852856, "HI")
# update info from server NO WEBHOOK
# upd = bot.get_updates()
# last_upd = upd[-1] # длин списка -1 то есть последний апдейт
# message_from_user = last_upd.message

@bot.message_handler(content_types=['text'])
def handle_text(message):
    try:
        bot.send_message(message.from_user.id, "Привет вот я надеюсь тут есть то что ты ищешь!")
        apiConnection = getApiConnection()
        seachq = urllib.parse.quote(message.text)
        url = '/method/docs.search?q=' + seachq + '&count=' + '5' \
              + '&offset=' + '1' + '&access_token=' + constants.tokenVK + '&v=5.64'
        try:
            vkResponse = vkRequest(apiConnection, url).get("response", 0)
        except (ConnectionError, http.client.BadStatusLine) as e:
            apiConnection.close()
        try:
            items = vkResponse.get("items")
            count = vkResponse.get("count")
            genereted_answer = '\U000026C4'+"Найденные фаилы по запросу" + "\n"
            for item in items:
                genereted_answer += item.get("title", 0) + "\n"
                genereted_answer += "Расширение фаила:" + item.get("ext", 0) + "\n"
                genereted_answer += item.get("url", 0) + "\n"
                genereted_answer += "******************************" + "\n"
        except:
            print("\n" + url)
            print("\n" + vkResponse)
        bot.send_message(message.from_user.id, genereted_answer)
    except:
        bot.send_message(message.from_user.id, "Что-то сломалось,скоро починю.")

bot.polling(none_stop=True, interval=0)

# -*- coding: utf-8 -*
"""
    File name: main.py
    Author: Daniil Nikulin
    Date created: 10.05.2017
    Date last modified: 27.06.2017
    Python Version: 3.6.1
"""
import http.client
import json
import os
import psycopg2
from flask.ext.sqlalchemy import SQLAlchemy
from urllib.parse import urlparse
import random
import string
import time
import urllib
import datetime
import urllib.request
import re
from flask import Flask, request
import telebot
from telebot import types
from transliterate import slugify
import constants
import emoji

server = Flask(__name__)

knownUsers = []
userStep = {}
usersMessageSearchRequest = {}
usersChoosedType = {}
usersVKResponse = {}
usersIsAlreadySearched = {}
usersCountFiles = {}
usersDownloadCommand = {}
usersLastChoosedFile = {}
usersDownTitle = {}
usersDownSize = {}
usersDownExt = {}
usersDownLink = {}
usersInlineKeyboardIsPressed = {}
usersLastCData = {}
usersLastKeyboard = {}
usersLastMessageTextSlider = {}
# Requests frequency limits VK
# Please define limitation here
requestLimitVK = 3  # not in use
currentRequestsVK = 0  # not in use
# Telegram Requests limitation
requestLimitTlgrmChat = {}  # Save time of bots last send messages !!!!very important for inline buttons!!
doNotResponseTlgrm = {}
currentRequestsTlgrm = 0

bot = telebot.TeleBot(constants.token)

# DATABASE FOR COUNTING USERS
app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = os.environ['DATABASE_URL']
db = SQLAlchemy(app)


# Limitation tof Telegram API test
def checkIfLimit(cid):
    try:
        print(int(round(time.time() * 1000)))
        print(requestLimitTlgrmChat[cid])
        if (int(round(time.time() * 1000)) - requestLimitTlgrmChat[cid]) > 1300:
            return False
        else:
            return True
        pass
    except Exception as exep:
        print(exep)
        print("Error in checkIfLimit(cid):")
        pass


pass


# Read forbidden words from file
def read_words(words_file):
    return [word for line in open(words_file, 'r', encoding='utf-8') for word in line.split()]


forbiddenWords = read_words("swearWords.txt")
forbiddenWordsFull = read_words("fullSwearWords.txt")

commands = {  # command description used in the "help" command
    'start': 'Начало работы со мной',
    'help': 'Вся необходимая информация'
}

tips = {  # tips description used in the "tips" command
    'Совет №1': "Если ищешь книгу " + emoji.emojiCodeDict[
        ":blue_book:"] + ", то часто легче найти в pdf или djvu с помощью "
                         "кнопки" + "<b>" + "\n" + "[ Текст(pdf,doc) ]" + "</b>",

    'Совет №2': "Если ты из Украины " + emoji.emojiCodeDict[":U:"] + emoji.emojiCodeDict[":A:"] +
                " выбирай способ загрузки " + "<b>" + "Файл" + "</b>" \
                + " и тебе не понадобится скачивать по ссылке на VK (заблокрованый ресурс).",

    'Совет №3': "Музыку трудно найти тут, все борятся с пиратством. Скорее всего ты найдешь "
                "рингтон по своему запросу. Но любимая песня на звонке, разве не подарок? " + emoji.emojiCodeDict[
                    ":grinning:"],

    'Совет №4': "Гифки ищются легко и непринужденно (особенно на русском), но всё же в Телеграме лучшие гифки тут " + "@gif. "
}

typesText = {  # types description used in the "types" command
    "Все": "Все файлы найденные по запросу",
    emoji.emojiCodeDict[
        ":page_facing_up:"] + "Текст(pdf,doc)": 'dpf, doc, docx, txt, odt...',

    emoji.emojiCodeDict[":open_book:"] + "Книги": "epub, fb2...",
    emoji.emojiCodeDict[":compression :"] + "Архивы": 'zip, rar, 7z...',
    "Gif": 'Анимации: gif',
    emoji.emojiCodeDict[":frame_photo"] + "Изображения": 'jpg, jpeg, bmp, png, m3d ,tif...',
    emoji.emojiCodeDict[":musical_note:"] + "Аудио": 'flac, mp3, m4r, mp2, wav',
    emoji.emojiCodeDict[":video_camera:"] + "Видео": 'mp4, webm, mkv, 3gp',
}

# Define Keyboard
typeSelect = types.ReplyKeyboardMarkup(one_time_keyboard=True)
typeSelect.row("Все", "Текст(pdf,doc)" + emoji.emojiCodeDict[":page_facing_up:"])
typeSelect.row("Книги" + emoji.emojiCodeDict[":open_book:"], "Архивы" + emoji.emojiCodeDict[":compression :"])
typeSelect.row("Gif", "Изображения" + emoji.emojiCodeDict[":frame_photo"])
typeSelect.row("Аудио" + emoji.emojiCodeDict[":musical_note:"], "Видео" + emoji.emojiCodeDict[":video_camera:"])
hideBoard = types.ReplyKeyboardRemove()  # if sent as reply_markup, will hide the keyboard


class Data(db.Model):
    __tablename__ = "data"
    id = db.Column(db.Integer, primary_key=True)
    firstName = db.Column(db.String(120))
    lastName = db.Column(db.String(120))
    cid = db.Column(db.BigInteger, unique=True)
    lastq = db.Column(db.String(200))
    userstep = db.Column(db.Integer)

    def __init__(self, first_name, last_name, cid, lastq, userstep):
        self.firstName = first_name
        self.lastName = last_name
        self.cid = cid
        self.lastq = lastq
        self.userstep = userstep


# Generate Secret Key fro access to users list
showUsersSecretKey = ''.join(random.choice(string.ascii_uppercase + string.digits) for _ in range(20))
countUsr = db.session.query(Data.cid).count()
bot.send_message(YOUR CHAT ID, emoji.emojiCodeDict[":computer:"] + "The user started the interaction" + "\n" +
                 "Current users in DB: " + str(countUsr) + "\n")


def setdbUserStep(cid, step):
    try:
        dataDB = db.session.query(Data).filter(Data.cid == int(cid)).first()
        dataDB.userstep = step
        db.session.commit()
    except Exception as exception:
        print(exception)
        pass


def getdbUserStep(cid):
    datDB = db.session.query(Data).filter(Data.cid == int(cid)).first()
    return int(datDB.userstep)


try:
    for data in db.session.query(Data).order_by(Data.cid):
        userStep[data.cid] = data.userstep
except Exception as e:
    print(e)
    print("Error in read users steps")
    pass

with open("log.txt", "a") as myfile:
    myfile.write(str(datetime.datetime.now()) + ": " + "New session" + "\n")


# Открытие соединения с VK.
def getApiConnection():
    return http.client.HTTPSConnection("api.vk.com")


# noinspection PyTypeChecker
def generateAnswer(message, offset, file_category):
    cid = message.chat.id
    try:
        if usersIsAlreadySearched[cid] is None:
            usersIsAlreadySearched[cid] = False
    except:
        usersIsAlreadySearched[cid] = False
        pass
    try:
        try:
            if not usersIsAlreadySearched[cid]:
                apiConnection = getApiConnection()
                cid = message.chat.id
                data = db.session.query(Data).filter(Data.cid == int(cid)).first()
                print(data.lastq)
                usersMessageSearchRequest[cid] = data.lastq
                searchText = urllib.parse.quote(str(data.lastq))
                print(searchText)
                url = '/method/docs.search?q=' + searchText + '&count=' + '500' \
                      + '&offset=' + '1' + '&access_token=' + constants.tokenVK + '&v=5.64'
            else:
                searchText = urllib.parse.quote(usersMessageSearchRequest[cid])
                url = '/method/docs.search?q=' + searchText + '&count=' + '500' \
                      + '&offset=' + '1' + '&access_token=' + constants.tokenVK + '&v=5.64'
        except:
            print("Exeption in #212")
            pass
        try:
            if not usersIsAlreadySearched[cid]:
                print("Response to VK from step 2")
                usersVKResponse[cid] = vkResponse = vkRequest(apiConnection, url).get("response", 0)
                usersIsAlreadySearched[cid] = True
            elif usersIsAlreadySearched:
                vkResponse = usersVKResponse[cid]
        except (ConnectionError, http.client.BadStatusLine):
            print("(ConnectionError, http.client.BadStatusLine):apiConnection.close()")
            apiConnection.close()
        try:
            items = vkResponse.get("items")
            count = vkResponse.get("count")
            if count == 0:
                bot.send_message(message.chat.id, "Прости,но я ничего не нашёл")
            else:
                genereted_answer = emoji.emojiCodeDict[":white_check_mark:"] + "Найденные файлы по запросу: " + "\n" + \
                                   "'" + "<b>" + str(usersMessageSearchRequest[cid]) + "</b>" + "'" + "\n" + "\n"
                data = {'count': 0}
                if 1 <= file_category <= 8:
                    for item in items:
                        if item.get("type", 0) == file_category:
                            item_new = {'id': item.get("id", 0), 'size': item.get("size", 0),
                                        'title': item.get("title", 0), 'url': item.get("url", 0),
                                        'type': item.get("type", 0), 'ext': item.get("ext", 0)}
                            data[data.get('count')] = item_new
                            data['count'] = data.get('count') + 1
                        pass
                else:
                    for item in items:
                        item_new = {'id': item.get("id", 0), 'size': item.get("size", 0), 'title': item.get("title", 0),
                                    'url': item.get("url", 0), 'type': item.get("type", 0), 'ext': item.get("ext", 0)}
                        data[data.get('count')] = item_new
                        data['count'] = data.get('count') + 1
                    pass
                if offset == 1:
                    if data.get("count") == 0:
                        genereted_answer += emoji.emojiCodeDict[":no_entry:"]
                    genereted_answer += "Файлов соотвутствующих критерию: " + str(data.get("count")) + "\n" + "\n"
                    usersCountFiles[cid] = int(data.get("count"))
                for iterPosition in range(0, int(data.get("count"))):
                    if (offset * 5) - 5 <= iterPosition < offset * 5:
                        randomDowStr = ''.join(random.choice(string.ascii_lowercase + string.digits) for _ in range(2))
                        genereted_answer += "<b>" + str(data.get(iterPosition).get("title", 0) + "\n") + "</b>"

                        usersDownloadCommand["d_" + str(data.get(iterPosition).get("id", 0)) + randomDowStr] = \
                            "d_" + str(data.get(iterPosition).get("id", 0)) + randomDowStr
                        usersDownTitle["d_" + str(data.get(iterPosition).get("id", 0)) + randomDowStr] = data.get(
                            iterPosition).get(
                            "title", 0)

                        genereted_answer += "Расширение файла: " + "<i>" + data.get(iterPosition).get("ext",
                                                                                                      0) + "</i>" + "\n"
                        usersDownExt["d_" + str(data.get(iterPosition).get("id", 0)) + randomDowStr] = data.get(
                            iterPosition).get(
                            "ext", 0)
                        unRedirectUrl = data.get(iterPosition).get("url", 0)
                        size = data.get(iterPosition).get("size", 0)

                        usersDownSize["d_" + str(data.get(iterPosition).get("id", 0)) + randomDowStr] = size

                        size = float(size)  # in bytes
                        size = size / 1024.0  # in KB (Kilo Bytes)
                        size = size / 1024.0  # size in MB (Mega Bytes)
                        genereted_answer += "Размер файла:" + "<i>" + " " "%.3f" % size + " MB" + "</i>" + "\n"

                        usersDownLink["d_" + str(data.get(iterPosition).get("id", 0)) + randomDowStr] = unRedirectUrl

                        genereted_answer += "<i>" + "Download: " + "</i>" + "/d_" + str(
                            data.get(iterPosition).get("id", 0)) + randomDowStr + "\n"

                        if iterPosition - ((offset * 5) - 1):
                            genereted_answer += emoji.emojiCodeDict[":small_blue_diamond:"] + \
                                                emoji.emojiCodeDict[":small_blue_diamond:"] + \
                                                emoji.emojiCodeDict[":small_blue_diamond:"] + \
                                                emoji.emojiCodeDict[":small_blue_diamond:"] + \
                                                emoji.emojiCodeDict[":small_blue_diamond:"] + \
                                                emoji.emojiCodeDict[":small_blue_diamond:"] + \
                                                emoji.emojiCodeDict[":small_blue_diamond:"] + \
                                                emoji.emojiCodeDict[":small_blue_diamond:"] + \
                                                emoji.emojiCodeDict[":small_red_triangle_down:"] + "\n" + "\n"
                        pass
                pass
                return genereted_answer
            pass
        except Exception as e:
            print("Error in generate answer")
            print(e)
            print(url)
            userStep[cid] = 0
            setdbUserStep(cid, 0)
    except Exception as e:
        print("Error in generate answer")
        bot.send_message(message.from_user.id,
                         "Что-то сломалось,скоро починю." + emoji.emojiCodeDict[":pensive:"] + "\n")
        userStep[cid] = 0
        try:
            setdbUserStep(cid, 0)
        except:
            print("Error in generate answer DB")
            pass
    pass


pass


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

    return vkJson


def get_user_step(uid):
    if uid in userStep:
        return userStep[uid]
    else:
        # knownUsers.append(uid)
        userStep[uid] = 0
        # print("New user detected, who hasn't used \"/start\" yet")
        return


pass


def show_keybord(message):
    cid = message.chat.id
    bot.send_message(cid, "Выбери тип файла:", reply_markup=typeSelect)  # show the keyboard
    userStep[cid] = 1  # set the user to the next step (expecting a reply in the listener now)
    try:
        setdbUserStep(cid, 1)
    except Exception as e:
        print(e)
        pass
    usersMessageSearchRequest[cid] = message.text


pass


# Show < 2 > directions buttons Also I use random string to avoid showing that button hasn't been updated on Android
# (I don't know why, but if callback data has been not updated you will have update animated circle on your button
# for 20 sec)
def pages_keyboard(offset, cid):
    try:
        keyboard = types.InlineKeyboardMarkup()
        btns = []
        if usersCountFiles[cid] == 0:
            return hideBoard
        if offset > 1:
            btns.append(types.InlineKeyboardButton(
                text=emoji.emojiCodeDict[":arrow_left:"],
                callback_data=''.join(random.choice(string.ascii_lowercase + string.digits) for _ in range(2)) +
                              '_{}'.format(offset - 1)))
        if offset < (usersCountFiles[cid] / 5):
            btns.append(types.InlineKeyboardButton(
                text=str(offset),
                callback_data=''.join(random.choice(string.ascii_lowercase + string.digits) for _ in range(2)) +
                              '_{}'.format(999)))
            btns.append(types.InlineKeyboardButton(
                text=emoji.emojiCodeDict[":arrow_right:"],
                callback_data=''.join(random.choice(string.ascii_lowercase + string.digits) for _ in range(2)) +
                              '_{}'.format(offset + 1)))
        keyboard.add(*btns)
        return keyboard  # возвращаем объект клавиатуры
    except Exception as e:
        print(e)
        print("Error in pages_keyboard")


pass


# only used for console output now
def listener(messages):
    for m in messages:
        if m.content_type == 'text':
            parsedText = urllib.parse.quote(m.text)
            with open("log.txt", "a") as myfile:  # print the sent message to the console
                myfile.write(str(datetime.datetime.now()) + ": " + str(m.chat.first_name) + " " + str(
                    m.chat.last_name) + " [" + str(m.chat.id) + "]: " + parsedText + "\n")
                print(str(str(datetime.datetime.now()) + ": " + m.chat.first_name) + " " + str(
                    m.chat.last_name) + " [" + str(m.chat.id) + "]: " + m.text)


bot.set_update_listener(listener)  # register listener


@bot.message_handler(commands=['start'])
def command_start(m):
    cid = m.chat.id
    userStep[cid] = 0
    if db.session.query(Data).filter(Data.cid == int(cid)).count() == 0:
        try:
            print("1")
            # if user hasn't used the "/start" command yet:
            data = Data(str(m.chat.first_name), str(m.chat.last_name), int(cid), None,
                        0)  # save user id, so you could brodcast messages to all users of this bot later
            userStep[cid] = 0  # save user id and his current "command level"
            db.session.add(data)
            db.session.commit()
            count = db.session.query(Data.cid).count()
            print("Всего пользователей: " + str(count))
            command_help(m)  # show the new user the help page
        except Exception as e:
            print("Error in database start ")
            print(e)
            pass
    else:
        print("2")
        # bot.send_message(cid, "I already know you, no need for me to scan you again!")
        command_help(m)  # show the new user the help page


@bot.message_handler(commands=usersDownloadCommand.keys())
def command_download(m):
    cid = m.chat.id
    line = re.sub('[/]', '', m.text)
    userStep[cid] = 2
    setdbUserStep(cid, 2)
    size = usersDownSize[line]
    if size is None:
        size = 0
    size = float(size)  # in bytes
    size = size / 1024.0  # in KB (Kilo Bytes)
    size = size / 1024.0  # size in MB (Mega Bytes)

    dwTypeSelect = downloadKeyboard(size)
    usersLastChoosedFile[cid] = line
    bot.send_message(cid,
                     "Выбери способ загрузки. " + '\n' + "Учти,если ВК заблокирован,то скачать по ссылке будет "
                                                         "невозможно.", parse_mode="HTML",
                     reply_markup=dwTypeSelect)


def downloadKeyboard(size):
    dwTypeSelect = types.ReplyKeyboardMarkup(one_time_keyboard=True)  # create the image selection keyboard
    if size < 50:
        return dwTypeSelect.row("Ссылка Вконтакте" + emoji.emojiCodeDict[":link:"], "Файл")
    else:
        return dwTypeSelect.row("Ссылка Вконтакте" + emoji.emojiCodeDict[":link:"])


@bot.message_handler(func=lambda message: get_user_step(message.chat.id) == 2)
def msg_step_two(message):
    cid = message.chat.id
    text = message.text
    bot.send_chat_action(cid, 'typing')
    try:
        if text == "Ссылка Вконтакте" + emoji.emojiCodeDict[":link:"]:
            text = "Вы получили пряму ссылку на скачивание." + "\n"
            size = usersDownSize[usersLastChoosedFile[cid]]
            size = float(size)  # in bytes
            size = size / 1024.0  # in KB (Kilo Bytes)
            size = size / 1024.0  # size in MB (Mega Bytes)
            text += "Имя файла: " + "<b>" + usersDownTitle[usersLastChoosedFile[cid]] + "</b>" + "\n"
            text += "Размер файла:" + "<b>" + " " "%.3f" % size + "MB" + "</b>" + "\n"
            bot.send_message(cid, usersDownLink[usersLastChoosedFile[cid]], parse_mode="HTML", reply_markup=hideBoard)
            userStep[cid] = 0
            setdbUserStep(cid, 0)
        elif text == "Файл":
            text = emoji.emojiCodeDict[
                       ":hourglass_flowing_sand:"] + "Файл загружается и вскоре будет отправлен вам." + "\n"
            size = usersDownSize[usersLastChoosedFile[cid]]
            size = float(size)  # in bytes
            size = size / 1024.0  # in KB (Kilo Bytes)
            size = size / 1024.0  # size in MB (Mega Bytes)
            text += "Имя файла: " + "<b>" + usersDownTitle[usersLastChoosedFile[cid]] + "</b>" + "\n"
            text += "Размер файла:" + "<b>" + " " "%.3f" % size + " MB" + "</b>" + "\n"
            bot.send_message(cid, text, parse_mode="HTML", reply_markup=hideBoard)
            bot.send_chat_action(cid, 'typing')
            ####SENDING FILE####
            title = str(usersDownTitle[usersLastChoosedFile[cid]])
            line = title.split('.')
            file_name = slugify(line[0])
            if file_name is None:
                file_name = line[0]
            ext = usersDownExt[usersLastChoosedFile[cid]]
            try:
                urllib.request.urlretrieve(usersDownLink[usersLastChoosedFile[cid]], file_name + "." + ext)
                isExeptionoccured = False
            except:
                isExeptionoccured = True
                file_name = ''.join(random.choice(string.ascii_lowercase + string.digits) for _ in range(10))
                urllib.request.urlretrieve(usersDownLink[usersLastChoosedFile[cid]], file_name + "." + ext)
                doc = open(file_name + "." + ext, 'rb')
                if 16000 >= os.path.getsize(file_name + "." + ext) >= 15000:
                    bot.send_message(message.from_user.id, "Скорее всего этот документ не откроется, "
                                                           "так как был удалён по просьбе правообладателей.",
                                     parse_mode='HTML')
                bot.send_chat_action(cid, 'upload_document')
                bot.send_document(message.from_user.id, doc, reply_markup=hideBoard)
                doc.close()
                os.remove(file_name + "." + ext)
                userStep[cid] = 0
                setdbUserStep(cid, 0)
                pass
            if not isExeptionoccured:
                doc = open(file_name + "." + ext, 'rb')
                if 16000 >= os.path.getsize(file_name + "." + ext) >= 15000:
                    bot.send_message(message.from_user.id, "Скорее всего этот документ не откроется, "
                                                           "так как был удалён по просьбе правообладателей.",
                                     parse_mode='HTML')
                bot.send_chat_action(cid, 'upload_document')
                bot.send_document(message.from_user.id, doc, reply_markup=hideBoard)
                doc.close()
                os.remove(file_name + "." + ext)
                userStep[cid] = 0
                setdbUserStep(cid, 0)
            pass
        else:
            size = usersDownSize[usersLastChoosedFile[cid]]
            if size is None:
                size = 0
            size = float(size)  # in bytes
            size = size / 1024.0  # in KB (Kilo Bytes)
            size = size / 1024.0  # size in MB (Mega Bytes)
            bot.send_message(cid,
                             emoji.emojiCodeDict[
                                 ":no_entry_sign:"] + "Не вводите всякую глупость,если я даю вам кнопки!")
            bot.send_message(cid,
                             emoji.emojiCodeDict[":no_entry_sign:"] + "Нажмите на одну из кнопок.",
                             reply_markup=downloadKeyboard(size))
    except:
        bot.send_message(cid, "Произошла ошибка,повторите попытку позже. Скорее всего я презагрузился,просто повтори "
                              "свой поисковый запрос.", parse_mode="HTML", reply_markup=hideBoard)
        userStep[cid] = 0  # reset the users step back to 0
        setdbUserStep(cid, 0)

        pass


@bot.message_handler(commands=['help'])
def command_help(m):
    try:
        # help_text = "Доступные следующие команды: \n"
        # for key in commands:  # generate help text out of the commands dictionary defined at the top
        #     help_text += "/" + key + ": "
        #     help_text += commands[key] + "\n"
        # pass
        help_text = emoji.emojiCodeDict[
                        ":mag:"] + " Для взаимодействия с ботом,просто отправь мне свой поисковый запрос." \
                                   "Потом выбери тип файла и способ загрузки." + "\n" + "\n" + \
                    emoji.emojiCodeDict[":arrow_down:"] + " Бот позволяет скачивать файлы из Вконтакте до " \
                    + "<b>" + "50 МБ " + "</b>" + "(" + "бот отправит файл в чат" + ")" + ", и получать ссылки на все файлы вне зависимости от размера." + "\n" + \
                    "Ссылки внутри чата " \
                    "действительны в течении " + "<b>" + "30" + "</b>" + " минут." + emoji.emojiCodeDict[
                        ":clock1130:"] + "\n" + "\n"
        tipNumber, tipText = random.choice(list(tips.items()))
        help_text += emoji.emojiCodeDict[":bulb:"] + tipNumber + "\n" + "\n"
        help_text += tipText
        help_text += "\n" + "\n" + "Все советы: /tips"
        help_text += "\n" + "Описание типов: /types"
        bot.send_message(m.chat.id, help_text, parse_mode='HTML')  # send the generated help page
    except Exception as ex:
        print(ex)
        pass


@bot.message_handler(commands=['tips'])
def command_tips(m):
    cid = m.chat.id
    try:
        tips_text = ""
        for key in tips:  # generate help text out of the commands dictionary defined at the top
            tips_text += emoji.emojiCodeDict[":bulb:"] + "<b>" + key + "</b>" + "\n"
            tips_text += tips[key] + "\n" + "\n"
        pass
        bot.send_message(m.chat.id, tips_text, parse_mode='HTML')  # send the generated help page
        userStep[cid] = 0
        setdbUserStep(cid, 0)
    except Exception as e:
        print("Exception in /tips ")
        print(e)
        pass


@bot.message_handler(commands=['exit'])
def command_exit(m):
    cid = m.chat.id
    try:
        bot.send_message(m.chat.id, emoji.emojiCodeDict[":mag:"] + "Введите свой поисковый запрос.",
                         parse_mode='HTML')  # send the generated help page
        userStep[cid] = 0
        setdbUserStep(cid, 0)
    except Exception as e:
        print(e)
        pass


@bot.message_handler(commands=['types'])
def command_types(m):
    cid = m.chat.id
    try:
        types_text = ""
        for key in typesText:  # generate help text out of the commands dictionary defined at the top
            types_text += "<b>" + key + "</b>" + "\n"
            types_text += typesText[key] + "\n" + "\n"
        pass
        bot.send_message(m.chat.id, types_text, parse_mode='HTML')  # send the generated help page
        userStep[cid] = 0
        setdbUserStep(cid, 0)
    except Exception as e:
        print(e)
        pass


pass


@bot.message_handler(commands=['getskey'])
def command_types(m):
    cid = m.chat.id
    try:
        if cid == YOUR CHAT ID:
            bot.send_message(YOUR CHAT ID, "Get your secret key" + emoji.emojiCodeDict[":key:"] + "\n")
            bot.send_message(YOUR CHAT ID, showUsersSecretKey + "\n")
            userStep[cid] = 0
            setdbUserStep(cid, 0)
        else:
            bot.send_message(cid, "Хлопче,ця команда не для тебе)" + "\n")
            userStep[cid] = 0
            setdbUserStep(cid, 0)
            return
    except Exception as e:
        print(e)
        pass


pass


@bot.callback_query_handler(func=lambda c: c.data)
def pages(c):
    # Format strings contain “replacement fields” surrounded by curly braces {}. Anything that is not contained in
    # braces is considered literal text, which is copied unchanged to the output. If you need to include a brace
    # character in the literal text, it can be escaped by doubling: {{ and }}. time.sleep(0.5) callback_data='to_{
    # }'.format(offset - 1)
    # Predefined function
    def changeAnswMessage():
        if usersLastCData[cid] == int(c.data[3:]):  # delete
            bot.answer_callback_query(callback_query_id=c.id)
            return
        if int(c.data[3:]) == 999:
            bot.answer_callback_query(callback_query_id=c.id)
            return
        else:
            try:
                usersLastMessageTextSlider[cid] = generateAnswer(c.message, int(c.data[3:]), usersChoosedType[cid])
                bot.edit_message_text(
                    chat_id=c.message.chat.id,
                    message_id=c.message.message_id,
                    text=usersLastMessageTextSlider[cid],  ####Careful
                    parse_mode='HTML',
                    reply_markup=pages_keyboard(int(c.data[3:]), cid))
                requestLimitTlgrmChat[cid] = int(round(time.time() * 1000))
                usersLastCData[cid] = int(c.data[3:])
            except Exception as exception:
                print(exception)
                print("Error in inline method inside")
                # bot.answer_callback_query(callback_query_id=c.id)
                requestLimitTlgrmChat[cid] = int(round(time.time() * 1000))
                raise

    # Begin here
    try:
        cid = c.message.chat.id
        if not checkIfLimit(cid):
            requestLimitTlgrmChat[cid] = int(round(time.time() * 1000))
            changeAnswMessage()
            pass
        else:
            if not doNotResponseTlgrm[cid]:
                doNotResponseTlgrm[cid] = True
                time.sleep(1)
                bot.answer_callback_query(callback_query_id=c.id, text="Не нажимай так быстро.")
                while checkIfLimit(cid):
                    time.sleep(random.uniform(1.2, 2.1))
                pass
                doNotResponseTlgrm[cid] = False
                bot.answer_callback_query(callback_query_id=c.id)
            else:
                return
        pass
    except Exception as ee:
        print("Error in inline method outside")
        print(ee)
        requestLimitTlgrmChat[cid] = int(round(time.time() * 1000))
        bot.edit_message_text(
            chat_id=c.message.chat.id,
            message_id=c.message.message_id,
            text="Пожалуйста повтори свой запрос,я не храню даннные так долго." + emoji.emojiCodeDict[":sweat_smile:"],
            parse_mode='HTML')
        time.sleep(1)
        pass


pass


@bot.message_handler(func=lambda message: get_user_step(message.chat.id) == 1)
def msg_step_one(message):
    cid = message.chat.id
    text = message.text

    # PreInitialization
    usersLastCData[cid] = int(1)
    doNotResponseTlgrm[cid] = False

    bot.send_chat_action(cid, 'typing')
    bot.send_message(message.from_user.id, "Надеюсь тут есть,то что тебе нужно.", reply_markup=hideBoard)
    # initialize first time
    requestLimitTlgrmChat[cid] = int(round(time.time() * 1000))
    # todo утечка памяти при большом кол-ве пользователей,ибо надо хранить все ссылки на все файлы
    if text == "Текст(pdf,doc)" + emoji.emojiCodeDict[":page_facing_up:"]:
        try:
            usersChoosedType[cid] = 1
            cid = message.chat.id
            generated_answer = generateAnswer(message, 1, int(1))
            bot.send_chat_action(message.from_user.id, 'typing')
            bot.send_message(message.from_user.id, generated_answer, parse_mode='HTML',
                             reply_markup=pages_keyboard(1, cid))
            userStep[cid] = 0
            setdbUserStep(cid, 0)  # reset the users step back to 0
        except:
            bot.send_message(message.from_user.id,
                             "Сильно много запросов,подожди 1-2 минуты и повтори попытку." + emoji.emojiCodeDict[
                                 ":pensive:"] + "\n")
            userStep[cid] = 0
            setdbUserStep(cid, 0)
        pass
    elif text == "Архивы" + emoji.emojiCodeDict[":compression :"]:
        try:
            usersChoosedType[cid] = 2
            cid = message.chat.id
            generated_answer = generateAnswer(message, 1, int(2))
            bot.send_chat_action(message.from_user.id, 'typing')
            bot.send_message(message.from_user.id, generated_answer, parse_mode='HTML',
                             reply_markup=pages_keyboard(1, cid))
            userStep[cid] = 0  # reset the users step back to 0
            setdbUserStep(cid, 0)
        except:
            bot.send_message(message.from_user.id,
                             "Сильно много запросов,подожди 1-2 минуты и повтори попытку." + emoji.emojiCodeDict[
                                 ":pensive:"] + "\n")
            userStep[cid] = 0
            setdbUserStep(cid, 0)
        pass
    elif text == "Gif":
        try:
            usersChoosedType[cid] = 3
            cid = message.chat.id
            generated_answer = generateAnswer(message, 1, int(3))
            bot.send_chat_action(message.from_user.id, 'typing')
            bot.send_message(message.from_user.id, generated_answer, parse_mode='HTML',
                             reply_markup=pages_keyboard(1, cid))
            userStep[cid] = 0  # reset the users step back to 0
            setdbUserStep(cid, 0)
        except:
            bot.send_message(message.from_user.id,
                             "Сильно много запросов,подожди 1-2 минуты и повтори попытку." + emoji.emojiCodeDict[
                                 ":pensive:"] + "\n")
            userStep[cid] = 0
            setdbUserStep(cid, 0)
        pass
    elif text == "Изображения" + emoji.emojiCodeDict[":frame_photo"]:
        try:
            usersChoosedType[cid] = 4
            cid = message.chat.id
            generated_answer = generateAnswer(message, 1, int(4))
            bot.send_chat_action(message.from_user.id, 'typing')
            bot.send_message(message.from_user.id, generated_answer, parse_mode='HTML',
                             reply_markup=pages_keyboard(1, cid))
            userStep[cid] = 0  # reset the users step back to 0
            setdbUserStep(cid, 0)
        except:
            bot.send_message(message.from_user.id,
                             "Сильно много запросов,подожди 1-2 минуты и повтори попытку." + emoji.emojiCodeDict[
                                 ":pensive:"] + "\n")
            userStep[cid] = 0
            setdbUserStep(cid, 0)
        pass
    elif text == "Аудио" + emoji.emojiCodeDict[":musical_note:"]:
        try:
            usersChoosedType[cid] = 5
            cid = message.chat.id
            generated_answer = generateAnswer(message, 1, int(5))
            bot.send_chat_action(message.from_user.id, 'typing')
            bot.send_message(message.from_user.id, generated_answer, parse_mode='HTML',
                             reply_markup=pages_keyboard(1, cid))
            userStep[cid] = 0  # reset the users step back to 0
            setdbUserStep(cid, 0)
        except:
            bot.send_message(message.from_user.id,
                             "Сильно много запросов,подожди 1-2 минуты и повтори попытку." + emoji.emojiCodeDict[
                                 ":pensive:"] + "\n")
            userStep[cid] = 0
            setdbUserStep(cid, 0)
        pass
    elif text == "Видео" + emoji.emojiCodeDict[":video_camera:"]:
        try:
            usersChoosedType[cid] = 6
            cid = message.chat.id
            generated_answer = generateAnswer(message, 1, int(6))
            bot.send_chat_action(message.from_user.id, 'typing')
            bot.send_message(message.from_user.id, generated_answer, parse_mode='HTML',
                             reply_markup=pages_keyboard(1, cid))
            userStep[cid] = 0  # reset the users step back to 0
            setdbUserStep(cid, 0)
        except:
            bot.send_message(message.from_user.id,
                             "Сильно много запросов,подожди 1-2 минуты и повтори попытку." + emoji.emojiCodeDict[
                                 ":pensive:"] + "\n")
            userStep[cid] = 0
            setdbUserStep(cid, 0)
        pass
    elif text == "Книги" + emoji.emojiCodeDict[":open_book:"]:
        try:
            usersChoosedType[cid] = 8
            cid = message.chat.id
            generated_answer = generateAnswer(message, 1, int(8))
            bot.send_chat_action(message.from_user.id, 'typing')
            bot.send_message(message.from_user.id, generated_answer, parse_mode='HTML',
                             reply_markup=pages_keyboard(1, cid))
            userStep[cid] = 0  # reset the users step back to 0
            setdbUserStep(cid, 0)
        except:
            bot.send_message(message.from_user.id,
                             "Сильно много запросов,подожди 1-2 минуты и повтори попытку." + emoji.emojiCodeDict[
                                 ":pensive:"] + "\n")
            userStep[cid] = 0
            setdbUserStep(cid, 0)
        pass
    elif text == "Все":
        try:
            usersChoosedType[cid] = 9
            cid = message.chat.id
            generated_answer = generateAnswer(message, 1, int(9))
            bot.send_chat_action(message.from_user.id, 'typing')
            bot.send_message(message.from_user.id, generated_answer, parse_mode='HTML',
                             reply_markup=pages_keyboard(1, cid))
            userStep[cid] = 0  # reset the users step back to 0
            setdbUserStep(cid, 0)
        except Exception as ee:
            print(ee)
            bot.send_message(message.from_user.id,
                             "Сильно много запросов,подожди 1-2 минуты и повтори попытку." + emoji.emojiCodeDict[
                                 ":pensive:"] + "\n")
            userStep[cid] = 0
            setdbUserStep(cid, 0)
        pass
    else:
        try:
            bot.send_message(cid,
                             emoji.emojiCodeDict[":no_entry_sign:"] + "Не вводите всякую глупость,если я даю вам "
                                                                      "кнопки!")
            bot.send_message(cid,
                             emoji.emojiCodeDict[":no_entry_sign:"]
                             + "Нажмите на одну из кнопок.", reply_markup=typeSelect)
        except Exception as ee:
            print(ee)


@bot.message_handler(content_types=['text'])
def handle_text(message):
    cid = message.chat.id
    if message.text == showUsersSecretKey:
        try:
            count = db.session.query(Data.cid).count()
            print("Всего пользователей: " + str(count))
            allUsers = "List of All Users" + "\n" + "Всего пользователей: " + str(count) + "\n"
            for dataDB in db.session.query(Data).order_by(Data.cid):
                allUsers += str(dataDB.firstName) + " " + dataDB.lastName + "\n" + "Chat ID: " + str(dataDB.cid) + "\n"
                allUsers += "***********" + "\n"
                print(dataDB.firstName, dataDB.lastName, dataDB.cid)
            pass
            bot.send_message(cid, allUsers, reply_markup=hideBoard)
            userStep[cid] = 0
            setdbUserStep(cid, 0)
            return
        except Exception as e:
            print("Error in showusers")
            print(e)
        pass

    elif any(word in message.text.lower() for word in forbiddenWords):
        bot.send_message(message.from_user.id,
                         emoji.emojiCodeDict[":no_entry_sign:"] + "Ой,не стоит искать всякую гадость тут." +
                         emoji.emojiCodeDict[":no_entry_sign:"])
    else:
        for fullBadWord in forbiddenWordsFull:
            text = str(message.text.lower()).encode("utf-8")
            text2 = str(fullBadWord.lower()).encode("utf-8")
            if text2 == text:
                bot.send_message(message.from_user.id,
                                 emoji.emojiCodeDict[":no_entry_sign:"] + "Ой,не стоит искать всякую гадость тут." +
                                 emoji.emojiCodeDict[":no_entry_sign:"])
                return
            pass
        pass
        try:
            try:
                dataDB = db.session.query(Data).filter(Data.cid == int(cid)).first()
                if dataDB is None:
                    raise TypeError(dataDB)
            except Exception as e:
                print("An old user who hasn't been added to DB")
                dataDB = Data(str(message.chat.first_name), str(message.chat.last_name), int(cid), None,
                              0)
                db.session.add(dataDB)
                db.session.commit()
                pass
            dataDB = db.session.query(Data).filter(Data.cid == int(cid)).first()
            dataDB.lastq = message.text
            db.session.commit()
        except Exception as e:
            print("Error in lastq add")
            print(e)
            pass
        retry = 0
        isGone = True
        while isGone:
            try:
                retry += 1
                if retry > 10:
                    isGone = False
                bot.send_chat_action(message.from_user.id, 'typing')
                cid = message.chat.id
                apiConnection = getApiConnection()
                searchText = urllib.parse.quote(message.text)
                url = '/method/docs.search?q=' + searchText + '&count=' + '1000' \
                      + '&offset=' + '1' + '&access_token=' + constants.tokenVK + '&v=5.64'
                try:
                    usersVKResponse[cid] = vkResponse = vkRequest(apiConnection, url).get("response", 0)
                    usersIsAlreadySearched[cid] = True
                    print("Got valid response from VK")
                except (ConnectionError, http.client.BadStatusLine) as e:
                    apiConnection.close()
                try:
                    bot.send_chat_action(message.from_user.id, 'typing')  # show the bot "typing" (max. 5 secs)
                    time.sleep(0.2)
                    count = vkResponse.get("count")
                    if count == 0:
                        bot.send_message(message.from_user.id,
                                         emoji.emojiCodeDict[":no_entry_sign:"] + "Прости,но я ничего не нашёл")
                        isGone = False
                    else:
                        bot.send_message(message.from_user.id,
                                         "Я нашёл " + str(
                                             count) + " файлов. " + "Доступны первые 1000 результатов." + "\n" + "Ну что,давай отсортируем их?")
                        show_keybord(message)
                        isGone = False
                    pass
                except:
                    print("\n" + url)
                    print("\n" + vkResponse)
                    time.sleep(2)
            except:
                print("Request to VK Nr. 1")
                time.sleep(random.randint(1, 3))
                pass
            pass
        pass
    pass


@server.route('/' + constants.token, methods=['POST'])
def get_message():
    bot.process_new_updates([telebot.types.Update.de_json(request.stream.read().decode("utf-8"))])
    return "POST", 200


@server.route("/")
def web_hook():
    bot.remove_webhook()
    bot.set_webhook(url='https://vkfilebot.herokuapp.com/' + constants.token)
    return "CONNECTED" + "\n Contact " + "<a href=" + "https://t.me/daniel_nikulin" + ">" + "Daniel" + "<a>", 200


server.run(host="0.0.0.0", port=os.environ.get('PORT', 5000))

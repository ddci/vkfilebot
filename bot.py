# -*- coding: utf-8 -*
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
import datetime
import json
import os
import random
import re
import string
import time
import logging
import urllib
import urllib.request

# non-standard dependencies:
import requests
# pyTelegramBotAPI lib
import telebot  # https://github.com/eternnoir/pyTelegramBotAPI
from telebot import types
# transcription translate lib
from transliterate import slugify  # https://github.com/barseghyanartur/transliterate
import constants
import vk
import database
from config import emoji
from config.config import tips, types_dict, type_select, hide_board
from moderation.words import forbidden_words, forbidden_words_full

user_step = {}
users_message_search_request = {}
users_choosed_type = {}
users_vk_response = {}
is_search_performed = {}
users_count_files = {}
users_download_command = {}
users_last_choose_file = {}
users_down_title = {}
users_down_size = {}
users_down_ext = {}
users_down_link = {}
users_inline_keyboard_is_pressed = {}
users_last_c_data = {}
users_last_keyboard = {}
users_last_message_text_slider = {}
# Telegram Requests limitation
users_interaction_wait_time_in_tlgm_chat = {}  # Saves time of bot`s last sent messages
do_not_respond_tlgrm = {}

logging.basicConfig(level=logging.DEBUG)
logging.basicConfig(format=u'%(filename)s[LINE:%(lineno)d]# %(levelname)-8s [%(asctime)s]  %(message)s',
                    level=logging.DEBUG)
logging.getLogger("requests").setLevel(level=logging.WARNING)
logging.getLogger("urllib3").setLevel(level=logging.WARNING)
logging.getLogger("werkzeug").setLevel(level=logging.WARNING)

bot = telebot.TeleBot(constants.TOKEN_TELEGRAM)
vk_connection = vk.VKConnectionAPI(constants.TOKEN_VK)
database.set_users_steps(user_step, users_message_search_request)


# Limitation tof Telegram API test
def if_limit_exceeded(cid):
    try:
        if (int(round(time.time() * 1000)) - users_interaction_wait_time_in_tlgm_chat[cid]) > 1500:
            return False
        else:
            return True
        pass
    except KeyError as e:
        logging.warning("  Filed to find  in if_limit_exceeded func:cid=%s in dictionary, error=%s", cid, e)
        pass


def to_mega_bytes(size):
    try:
        size = size / 1024.0  # in KB (Kilo Bytes)
        size = size / 1024.0  # size in MB (Mega Bytes)
        return size
    except Exception as e:
        logging.error("Filed to convert to MB , error=%s", e)
        return 1


def get_user_step(cid):
    if cid in user_step:
        return user_step[cid]
    else:
        user_step[cid] = 0
        logging.info("Userstep for cid%s=", cid)
        return


def show_keyboard(message):
    cid = message.chat.id
    bot.send_message(cid, "Выбери тип файла:", reply_markup=type_select)  # show the keyboard
    user_step[cid] = 1  # set the user to the next step (expecting a reply in the listener now)
    database.set_user_step_to_db(cid, 1)
    users_message_search_request[cid] = message.text


# only used for console output now
def listener(messages):
    for m in messages:
        if m.content_type == 'text':
            # logging.info(str(str(datetime.datetime.now()) + ": " + m.chat.first_name) + " " + str(
            # m.chat.last_name) + " [" + str(m.chat.id) + "]: " + m.text)
            logging.info(m.chat.first_name + " " + str(
                m.chat.last_name) + " [" + str(m.chat.id) + "]: " + m.text)


def generate_answer(message, offset, file_category):
    cid = message.chat.id
    if cid not in is_search_performed:
        is_search_performed[cid] = False
    try:
        if not is_search_performed[cid]:
            search_req_last = database.get_user_last_search_request_from_db(cid)
            users_message_search_request[cid] = search_req_last
            search_text = str(search_req_last)
            logging.debug("User has not performed search request since last reboot,but stays on step 1. User continues "
                          "search from step 1 "
                          "with search request = %s", search_text)
        else:
            search_text = users_message_search_request[cid]
        if not is_search_performed[cid]:
            vk_response = vk_connection.send_api_search_request(search_text, 1000, 1).get("response", 0)
            users_vk_response[cid] = vk_response
            is_search_performed[cid] = True
            logging.info("Got response from VK from userstep 2")
        else:
            vk_response = users_vk_response[cid]
        items = vk_response.get("items")
        count = vk_response.get("count")
        if count == 0:
            bot.send_message(message.chat.id, "Прости,но я ничего не нашёл")
        else:
            generated_answer = emoji.emoji_codes_dict[":white_check_mark:"] + "Найденные файлы по запросу: " + "\n" + \
                               "'" + "<b>" + str(users_message_search_request[cid]) + "</b>" + "'" + "\n" + "\n"
            user = {'count': 0}
            if 1 <= file_category <= 8:
                for item in items:
                    if item.get("type", 0) == file_category:
                        item_new = {'id': item.get("id", 0), 'size': item.get("size", 0),
                                    'title': item.get("title", 0), 'url': item.get("url", 0),
                                    'type': item.get("type", 0), 'ext': item.get("ext", 0)}
                        user[user.get('count')] = item_new
                        user['count'] = user.get('count') + 1
                    pass
            else:
                for item in items:
                    item_new = {'id': item.get("id", 0), 'size': item.get("size", 0), 'title': item.get("title", 0),
                                'url': item.get("url", 0), 'type': item.get("type", 0), 'ext': item.get("ext", 0)}
                    user[user.get('count')] = item_new
                    user['count'] = user.get('count') + 1
                pass
            pass
            amount_of_files_contain_only_links = 0
            for iter_position in range(0, int(user.get("count"))):
                if str(user.get(iter_position).get("ext", 0)) == "url":
                    amount_of_files_contain_only_links += 1
            pass
            if amount_of_files_contain_only_links == int(user.get("count")) and int(user.get("count")) != 0:
                bot.send_message(cid,
                                 emoji.emoji_codes_dict[
                                     ":warning:"] + "Обратите внимание на то, что все файлы в выдаче это ссылки "
                                                    "на другие ресурсы." + emoji.emoji_codes_dict[
                                     ":warning:"],
                                 parse_mode="HTML")
            pass
            logging.debug("Amount of files containing *.url = %s", amount_of_files_contain_only_links)
            if offset == 1:
                if user.get("count") == 0:
                    generated_answer += emoji.emoji_codes_dict[":no_entry:"]
                generated_answer += "Файлов соотвутствующих критерию: " + str(
                    user.get("count")) + "\n" + "\n"
                users_count_files[cid] = int(user.get("count"))

            for iter_position in range(0, int(user.get("count"))):
                if (offset * 5) - 5 <= iter_position < offset * 5:
                    randomDowStr = ''.join(random.choice(string.ascii_lowercase + string.digits) for _ in range(2))
                    generated_answer += "<b>" + str(user.get(iter_position).get("title", 0) + "\n") + "</b>"

                    users_download_command["d_" + str(user.get(iter_position).get("id", 0)) + randomDowStr] = \
                        "d_" + str(user.get(iter_position).get("id", 0)) + randomDowStr
                    users_down_title[
                        "d_" + str(user.get(iter_position).get("id", 0)) + randomDowStr] = user.get(
                        iter_position).get(
                        "title", 0)

                    generated_answer += "Расширение файла: " + "<i>" + user.get(iter_position).get("ext",
                                                                                                   0) + "</i>"
                    users_down_ext[
                        "d_" + str(user.get(iter_position).get("id", 0)) + randomDowStr] = user.get(
                        iter_position).get(
                        "ext", 0)
                    if user.get(iter_position).get("ext", 0) == "url":
                        generated_answer += emoji.emoji_codes_dict[":link:"]
                    unRedirectUrl = user.get(iter_position).get("url", 0)
                    size = user.get(iter_position).get("size", 0)

                    users_down_size["d_" + str(user.get(iter_position).get("id", 0)) + randomDowStr] = size

                    size = to_mega_bytes(float(size))
                    generated_answer += "\n" + "Размер файла:" + "<i>" + " " "%.3f" % size + " MB" + "</i>" + "\n"

                    users_down_link[
                        "d_" + str(user.get(iter_position).get("id", 0)) + randomDowStr] = unRedirectUrl

                    generated_answer += "<i>" + "Download: " + "</i>" + "/d_" + str(
                        user.get(iter_position).get("id", 0)) + randomDowStr + "\n"

                    if iter_position - ((offset * 5) - 1):
                        generated_answer += emoji.emoji_codes_dict[":small_blue_diamond:"] + \
                                            emoji.emoji_codes_dict[":small_blue_diamond:"] + \
                                            emoji.emoji_codes_dict[":small_blue_diamond:"] + \
                                            emoji.emoji_codes_dict[":small_blue_diamond:"] + \
                                            emoji.emoji_codes_dict[":small_blue_diamond:"] + \
                                            emoji.emoji_codes_dict[":small_blue_diamond:"] + \
                                            emoji.emoji_codes_dict[":small_blue_diamond:"] + \
                                            emoji.emoji_codes_dict[":small_blue_diamond:"] + \
                                            emoji.emoji_codes_dict[":small_red_triangle_down:"] + "\n" + "\n"
            return generated_answer
        pass
    except Exception as e:
        logging.exception("Failed generate answer, error=%s", e)
        bot.send_message(message.from_user.id,
                         "Что-то сломалось,скоро починю." + emoji.emoji_codes_dict[":pensive:"] + "\n")
        user_step[cid] = 0
        database.set_user_step_to_db(cid, 0)


# Show < 2 > directions buttons Also I use random string to avoid showing that button hasn't been updated on Android
# (I don't know why, but if callback data has been not updated you will have animated update circle on your button
# for 20 sec)
def pages_keyboard(offset, cid):
    try:
        keyboard = types.InlineKeyboardMarkup()
        buttons = []
        if users_count_files[cid] == 0:
            return hide_board
        if offset > 1:
            buttons.append(types.InlineKeyboardButton(
                text=emoji.emoji_codes_dict[":arrow_left:"],
                callback_data=''.join(random.choice(string.ascii_lowercase + string.digits) for _ in range(2)) +
                              '_{}'.format(offset - 1)))
        if offset < (users_count_files[cid] / 5):
            buttons.append(types.InlineKeyboardButton(
                text=str(offset),
                callback_data=''.join(random.choice(string.ascii_lowercase + string.digits) for _ in range(2)) +
                              '_{}'.format(999)))
            buttons.append(types.InlineKeyboardButton(
                text=emoji.emoji_codes_dict[":arrow_right:"],
                callback_data=''.join(random.choice(string.ascii_lowercase + string.digits) for _ in range(2)) +
                              '_{}'.format(offset + 1)))
        keyboard.add(*buttons)
        return keyboard  # возвращаем объект клавиатуры
    except Exception as e:
        logging.exception("Error in pages_keyboard, cid=%s error=%s", cid, e)


def get_download_buttons_keyboard(size):
    dw_type_select = types.ReplyKeyboardMarkup(one_time_keyboard=True)  # create the selection keyboard
    size_str = "%.1f" % size
    if size < 50:
        return dw_type_select.row("Ссылка Вконтакте" + emoji.emoji_codes_dict[":link:"], "Файл" + " " + size_str + "MB")
    else:
        return dw_type_select.row("Ссылка Вконтакте" + emoji.emoji_codes_dict[":link:"])


@bot.message_handler(commands=['start'])
def command_start(message):
    cid = message.chat.id
    text = message.text
    text = re.sub('/start', '', text)
    user_step[cid] = 0
    if text == '':
        if not database.is_user_exist(cid):
            logging.info("New user pressed start")
            database.add_user_to_db(message)
            user_step[message.chat.id] = 0  # save user id and his current "command level"
            command_help(message)  # show the new user the help page

        else:
            logging.info("Old user pressed start")
            # bot.send_message(cid, "I already know you, no need for me to scan you again!")
            command_help(message)  # show the new user the help page
    else:
        try:
            logging.debug("Received message with authorization data.")
            code = re.sub(' ', '', text)
            payload = {'code': code, 'cid': cid}
            d = requests.get("http://vkfiles.herokuapp.com/authbot", data=json.dumps(payload),
                             headers={'Content-type': 'application/json'}, timeout=20)
            r = requests.get("http://vkfilebotmanagement.herokuapp.com/authbot/", data=json.dumps(payload),
                             headers={'Content-type': 'application/json'}, timeout=20)
            logging.debug("NIC: " + d.text)
            logging.debug("DANY: " + r.text)
            if (str(r.text)) == str(cid):
                bot.send_message(cid, " Вы успешно авторизованы.")
            command_help(message)
        except Exception as e:
            logging.exception("Exception in command_start func error=%s", e)
            command_help(message)
            pass


@bot.message_handler(commands=users_download_command.keys())
def command_download(message):
    cid = message.chat.id
    line = re.sub('[/]', '', message.text)
    user_step[cid] = 2
    database.set_user_step_to_db(cid, 2)
    size = users_down_size[line]
    if size is None:
        size = 0
    size = to_mega_bytes(float(size))
    dwl_type_select = get_download_buttons_keyboard(size)
    users_last_choose_file[cid] = line
    bot.send_message(cid,
                     emoji.emoji_codes_dict[":arrow_down:"] +
                     emoji.emoji_codes_dict[":twisted_rightwards_arrows:"] +
                     " Выбери способ загрузки. " + '\n' + "Учти,если ВК заблокирован,то скачать по ссылке будет "
                                                          "невозможно.", parse_mode="HTML",
                     reply_markup=dwl_type_select)


@bot.message_handler(func=lambda message: get_user_step(message.chat.id) == 2)
def msg_step_two(message):
    cid = message.chat.id
    text = message.text
    bot.send_chat_action(cid, 'typing')
    try:
        if text == "Ссылка Вконтакте" + emoji.emoji_codes_dict[":link:"]:
            text = "Вы получили пряму ссылку на скачивание." + "\n"
            size = users_down_size[users_last_choose_file[cid]]
            size = to_mega_bytes(float(size))
            text += "Имя файла: " + "<b>" + users_down_title[users_last_choose_file[cid]] + "</b>" + "\n"
            text += "Размер файла:" + "<b>" + " " "%.3f" % size + "MB" + "</b>" + "\n"
            bot.send_message(cid, users_down_link[users_last_choose_file[cid]], parse_mode="HTML",
                             reply_markup=hide_board)
            user_step[cid] = 0
            database.set_user_step_to_db(cid, 0)
        elif "Файл" in text:
            text = emoji.emoji_codes_dict[
                       ":hourglass_flowing_sand:"] + "Файл загружается и вскоре будет отправлен вам." + "\n"
            size = users_down_size[users_last_choose_file[cid]]
            size = to_mega_bytes(float(size))
            text += "Имя файла: " + "<b>" + users_down_title[users_last_choose_file[cid]] + "</b>" + "\n"
            text += "Размер файла:" + "<b>" + " " "%.3f" % size + " MB" + "</b>" + "\n"
            bot.send_message(cid, text, parse_mode="HTML", reply_markup=hide_board)
            bot.send_chat_action(cid, 'typing')
            title = str(users_down_title[users_last_choose_file[cid]])
            # This method starts splitting from the right-hand-side of the string; by giving it a maximum, you get to
            #  split just the right-hand-most occurrences.
            # https://stackoverflow.com/questions/15012228/splitting-on-last-delimiter-in-python-string
            line = title.rsplit('.', 1)
            file_name = slugify(line[0])
            if file_name is None:
                file_name = line[0]
            ext = users_down_ext[users_last_choose_file[cid]]
            try:
                urllib.request.urlretrieve(users_down_link[users_last_choose_file[cid]], file_name + "." + ext)
            except Exception as e:
                logging.exception("Error with file name or error while downloading error=%s,so we use random name "
                                  "for file.", e)
                is_exception_occurred = True
                file_name = ''.join(random.choice(string.ascii_lowercase + string.digits) for _ in range(10))
                urllib.request.urlretrieve(users_down_link[users_last_choose_file[cid]], file_name + "." + ext)
                doc = open(file_name + "." + ext, 'rb')
                if 16000 >= os.path.getsize(file_name + "." + ext) >= 15000:
                    bot.send_message(message.from_user.id, "Скорее всего этот документ не откроется, "
                                                           "так как был удалён по просьбе правообладателей.",
                                     parse_mode='HTML')

                bot.send_chat_action(cid, 'upload_document')

                bot.send_document(message.from_user.id, doc, reply_markup=hide_board)
                doc.close()
                os.remove(file_name + "." + ext)
                user_step[cid] = 0
                database.set_user_step_to_db(cid, 0)
            else:
                is_exception_occurred = False
            if not is_exception_occurred:
                doc = open(file_name + "." + ext, 'rb')
                if 16000 >= os.path.getsize(file_name + "." + ext) >= 15000:
                    bot.send_message(message.from_user.id, "Скорее всего этот документ не откроется, "
                                                           "так как был удалён по просьбе правообладателей.",
                                     parse_mode='HTML')
                bot.send_chat_action(cid, 'upload_document')
                bot.send_document(message.from_user.id, doc, reply_markup=hide_board)
                doc.close()
                os.remove(file_name + "." + ext)
                rateText = "Спасибо, а теперь перейдите, пожалуйста, по ссылке " \
                           "https://telegram.me/storebot?start=vkfiles_bot" \
                           " и нажмите " + "<b>" + "Start" + "</b>" + ". Спасибо!"
                rand = random.randint(0, 9)
                if rand > 7:
                    bot.send_message(message.from_user.id, rateText, parse_mode='HTML')
                user_step[cid] = 0
                database.set_user_step_to_db(cid, 0)
            pass
        else:
            size = users_down_size[users_last_choose_file[cid]]
            size_mb = to_mega_bytes(size)  # size in MB (Mega Bytes)
            bot.send_message(cid,
                             emoji.emoji_codes_dict[
                                 ":no_entry_sign:"] + "Не вводите всякую глупость,если я даю вам кнопки!")
            bot.send_message(cid,
                             emoji.emoji_codes_dict[":no_entry_sign:"] + "Нажмите на одну из кнопок.",
                             reply_markup=get_download_buttons_keyboard(size_mb))
    except Exception as e:
        logging.exception("Exception in msg_step_two func error=%s", e)
        bot.send_message(cid, "Произошла ошибка,повторите попытку позже. Скорее всего я презагрузился,просто повтори "
                              "свой поисковый запрос.", parse_mode="HTML", reply_markup=hide_board)
        user_step[cid] = 0  # reset the users step back to 0
        database.set_user_step_to_db(cid, 0)


@bot.message_handler(commands=['help'])
def command_help(m):
    try:
        help_text = emoji.emoji_codes_dict[
                        ":mag:"] + " Для взаимодействия с ботом,просто отправь мне свой поисковый запрос." \
                                   "Потом выбери тип файла и способ загрузки." + "\n" + "\n" + \
                    emoji.emoji_codes_dict[":arrow_down:"] + " Бот позволяет скачивать файлы из Вконтакте до " \
                    + "<b>" + "50 МБ " + "</b>" + "(" + "бот отправит файл в чат" + ")" \
                    + ", и получать ссылки на все файлы вне зависимости от размера." + "\n" + \
                    "Ссылки внутри чата " \
                    "действительны в течении " + "<b>" + "30" + "</b>" + " минут." + emoji.emoji_codes_dict[
                        ":clock1130:"] + "\n" + "\n"
        tipNumber, tipText = random.choice(list(tips.items()))
        help_text += emoji.emoji_codes_dict[":bulb:"] + tipNumber + "\n" + "\n"
        help_text += tipText
        help_text += "\n" + "\n" + "Все советы: /tips"
        help_text += "\n" + "Описание типов: /types"
        bot.send_message(m.chat.id, help_text, parse_mode='HTML')  # send the generated help page
    except Exception as e:
        logging.exception("Exception in  command_help func error=%s", e)
        pass


@bot.message_handler(commands=['tips'])
def command_tips(m):
    cid = m.chat.id
    try:
        tips_text = ""
        for key in tips:  # generate help text out of the commands dictionary defined at the top
            tips_text += emoji.emoji_codes_dict[":bulb:"] + "<b>" + key + "</b>" + "\n"
            tips_text += tips[key] + "\n" + "\n"
        pass
        bot.send_message(m.chat.id, tips_text, parse_mode='HTML')  # send the generated help page
        user_step[cid] = 0
        database.set_user_step_to_db(cid, 0)
    except Exception as e:
        logging.exception("Exception in  command_tips func error=%s", e)


@bot.message_handler(commands=['exit'])
def command_exit(m):
    cid = m.chat.id
    try:
        bot.send_message(m.chat.id, emoji.emoji_codes_dict[":mag:"] + "Введите свой поисковый запрос.",
                         parse_mode='HTML')  # send the generated help page
        user_step[cid] = 0
        database.set_user_step_to_db(cid, 0)
    except Exception as e:
        logging.exception("Exception in command_exit func error=%s", e)


@bot.message_handler(commands=['types'])
def command_types(m):
    cid = m.chat.id
    try:
        types_text = ""
        for key in types_dict:  # generate help text out of the commands dictionary defined at the top
            types_text += "<b>" + key + "</b>" + "\n"
            types_text += types_dict[key] + "\n" + "\n"
        pass
        bot.send_message(m.chat.id, types_text, parse_mode='HTML')  # send the generated help page
        user_step[cid] = 0
        database.set_user_step_to_db(cid, 0)
    except Exception as e:
        logging.exception("Exception in command_types func error=%s", e)


@bot.message_handler(commands=['getskey'])
def get_s_key(m):
    cid = m.chat.id
    try:
        if cid == constants.MY_CID:
            try:
                number_of_users = database.count_all_users()
                logging.info("All users: " + str(number_of_users))
                all_users = "Всего пользователей: " + str(number_of_users) + "\n"
                bot.send_message(cid, all_users, reply_markup=hide_board)
                user_step[cid] = 0
                database.set_user_step_to_db(cid, 0)
                return
            except Exception as e:
                logging.error("get_s_key internal error while getting all users info wit error = %s", e)
            user_step[cid] = 0
            database.set_user_step_to_db(cid, 0)
        else:
            bot.send_message(cid, "Хлопче,ця команда не для тебе)" + "\n")
            user_step[cid] = 0
            database.set_user_step_to_db(cid, 0)
            return
    except Exception as e:
        logging.exception("Exception in get_s_key func error=%s", e)
        pass


@bot.callback_query_handler(func=lambda c: c.data)
def pages(c):
    # Format strings contain “replacement fields” surrounded by curly braces {}. Anything that is not contained in
    # braces is considered literal text, which is copied unchanged to the output. If you need to include a brace
    # character in the literal text, it can be escaped by doubling: {{ and }}. time.sleep(0.5) callback_data='to_{
    # }'.format(offset - 1)
    # Predefined function
    cid = c.message.chat.id

    def change_answer_message():
        if users_last_c_data[cid] == int(c.data[3:]):
            bot.answer_callback_query(callback_query_id=c.id)
            return
        if int(c.data[3:]) == 999:
            bot.answer_callback_query(callback_query_id=c.id)
            return
        else:
            try:
                if users_last_c_data[cid] - int(c.data[3:]) >= 1:
                    logging.info("User [%s] is scrolling back", cid)
                else:
                    logging.info("User [%s] is scrolling forward", cid)
                users_last_message_text_slider[cid] = generate_answer(c.message, int(c.data[3:]),
                                                                      users_choosed_type[cid])
                bot.edit_message_text(
                    chat_id=c.message.chat.id,
                    message_id=c.message.message_id,
                    text=users_last_message_text_slider[cid],  # careful
                    parse_mode='HTML',
                    reply_markup=pages_keyboard(int(c.data[3:]), cid))
                users_interaction_wait_time_in_tlgm_chat[cid] = int(round(time.time() * 1000))
                users_last_c_data[cid] = int(c.data[3:])
            except Exception as exception:
                logging.error("Error in inline method inside error=%s", exception)
                logging.exception("Error in inline method inside")
                # bot.answer_callback_query(callback_query_id=c.id)
                users_interaction_wait_time_in_tlgm_chat[cid] = int(round(time.time() * 1000))
                raise

    try:
        if cid not in users_last_c_data:
            logging.warning("Users tried to scroll data, which no longer exist.")
            raise Exception
        if not if_limit_exceeded(cid):
            users_interaction_wait_time_in_tlgm_chat[cid] = int(round(time.time() * 1000))
            change_answer_message()
            pass
        else:
            if not do_not_respond_tlgrm[cid]:
                do_not_respond_tlgrm[cid] = True
                time.sleep(1)
                bot.answer_callback_query(callback_query_id=c.id, text="Не нажимай так быстро.")
                while if_limit_exceeded(cid):
                    time.sleep(random.uniform(1.2, 2.1))
                pass
                do_not_respond_tlgrm[cid] = False
                bot.answer_callback_query(callback_query_id=c.id)
            else:
                return
        pass
    except Exception as e:
        logging.error("Error in inline method outside error=%s", e)
        logging.exception("Error in inline method outside")
        users_interaction_wait_time_in_tlgm_chat[cid] = int(round(time.time() * 1000))
        bot.edit_message_text(
            chat_id=c.message.chat.id,
            message_id=c.message.message_id,
            text="Пожалуйста повтори свой запрос,я не храню даннные так долго." + emoji.emoji_codes_dict[
                ":sweat_smile:"],
            parse_mode='HTML')
        time.sleep(1)
        pass


@bot.message_handler(func=lambda message: get_user_step(message.chat.id) == 1)
def msg_step_one(message):
    cid = message.chat.id
    text = message.text
    searchText = users_message_search_request[cid]
    users_last_c_data[cid] = int(1)
    do_not_respond_tlgrm[cid] = False
    bot.send_chat_action(cid, 'typing')
    bot.send_message(message.from_user.id, "Надеюсь тут есть,то что тебе нужно.", reply_markup=hide_board)
    users_interaction_wait_time_in_tlgm_chat[cid] = int(round(time.time() * 1000))
    try:
        if text == "Текст(pdf,doc)" + emoji.emoji_codes_dict[":page_facing_up:"]:
            users_choosed_type[cid] = 1
            cid = message.chat.id
            generated_answer = generate_answer(message, 1, int(1))
            bot.send_chat_action(message.from_user.id, 'typing')
            bot.send_message(message.from_user.id, generated_answer, parse_mode='HTML',
                             reply_markup=pages_keyboard(1, cid))
            database.add_request_to_db(cid, searchText, file_type=1)
            user_step[cid] = 0
            database.set_user_step_to_db(cid, 0)  # reset the users step back to 0
            pass
        elif text == "Архивы" + emoji.emoji_codes_dict[":compression :"]:
            users_choosed_type[cid] = 2
            cid = message.chat.id
            generated_answer = generate_answer(message, 1, int(2))
            bot.send_chat_action(message.from_user.id, 'typing')
            bot.send_message(message.from_user.id, generated_answer, parse_mode='HTML',
                             reply_markup=pages_keyboard(1, cid))
            database.add_request_to_db(cid, searchText, file_type=2)
            user_step[cid] = 0  # reset the users step back to 0
            database.set_user_step_to_db(cid, 0)
            pass
        elif text == "Gif":
            users_choosed_type[cid] = 3
            cid = message.chat.id
            generated_answer = generate_answer(message, 1, int(3))
            bot.send_chat_action(message.from_user.id, 'typing')
            bot.send_message(message.from_user.id, generated_answer, parse_mode='HTML',
                             reply_markup=pages_keyboard(1, cid))
            database.add_request_to_db(cid, searchText, file_type=3)
            user_step[cid] = 0  # reset the users step back to 0
            database.set_user_step_to_db(cid, 0)
            pass
        elif text == "Изображения" + emoji.emoji_codes_dict[":frame_photo"]:
            users_choosed_type[cid] = 4
            cid = message.chat.id
            generated_answer = generate_answer(message, 1, int(4))
            bot.send_chat_action(message.from_user.id, 'typing')
            bot.send_message(message.from_user.id, generated_answer, parse_mode='HTML',
                             reply_markup=pages_keyboard(1, cid))
            database.add_request_to_db(cid, searchText, file_type=4)
            user_step[cid] = 0  # reset the users step back to 0
            database.set_user_step_to_db(cid, 0)
            pass
        elif text == "Аудио" + emoji.emoji_codes_dict[":musical_note:"]:
            users_choosed_type[cid] = 5
            cid = message.chat.id
            generated_answer = generate_answer(message, 1, int(5))
            bot.send_chat_action(message.from_user.id, 'typing')
            bot.send_message(message.from_user.id, generated_answer, parse_mode='HTML',
                             reply_markup=pages_keyboard(1, cid))
            database.add_request_to_db(cid, searchText, file_type=5)
            user_step[cid] = 0  # reset the users step back to 0
            database.set_user_step_to_db(cid, 0)
            pass
        elif text == "Видео" + emoji.emoji_codes_dict[":video_camera:"]:
            users_choosed_type[cid] = 6
            cid = message.chat.id
            generated_answer = generate_answer(message, 1, int(6))
            bot.send_chat_action(message.from_user.id, 'typing')
            bot.send_message(message.from_user.id, generated_answer, parse_mode='HTML',
                             reply_markup=pages_keyboard(1, cid))
            database.add_request_to_db(cid, searchText, file_type=6)
            user_step[cid] = 0  # reset the users step back to 0
            database.set_user_step_to_db(cid, 0)
            pass
        elif text == "Книги" + emoji.emoji_codes_dict[":open_book:"]:
            users_choosed_type[cid] = 8
            cid = message.chat.id
            generated_answer = generate_answer(message, 1, int(8))
            bot.send_chat_action(message.from_user.id, 'typing')
            bot.send_message(message.from_user.id, generated_answer, parse_mode='HTML',
                             reply_markup=pages_keyboard(1, cid))
            database.add_request_to_db(cid, searchText, file_type=8)
            user_step[cid] = 0  # reset the users step back to 0
            database.set_user_step_to_db(cid, 0)
            pass
        elif text == "Все":
            users_choosed_type[cid] = 9
            cid = message.chat.id
            generated_answer = generate_answer(message, 1, int(9))
            bot.send_chat_action(message.from_user.id, 'typing')
            bot.send_message(message.from_user.id, generated_answer, parse_mode='HTML',
                             reply_markup=pages_keyboard(1, cid))
            database.add_request_to_db(cid, searchText, file_type=9)
            user_step[cid] = 0  # reset the users step back to 0
            database.set_user_step_to_db(cid, 0)
            pass
        else:
            bot.send_message(cid,
                             emoji.emoji_codes_dict[":no_entry_sign:"] + "Не вводите всякую глупость,если я даю вам "
                                                                         "кнопки!")
            bot.send_message(cid,
                             emoji.emoji_codes_dict[":no_entry_sign:"]
                             + "Нажмите на одну из кнопок.", reply_markup=type_select)
    except Exception as e:
        logging.exception("Exception in step 2 error = %s", e)
        bot.send_message(message.from_user.id, "Сильно много запросов,подожди 1-2 минуты и повтори попытку." +
                         + emoji.emoji_codes_dict[":pensive:"] + "\n")
        user_step[cid] = 0
        database.set_user_step_to_db(cid, 0)


@bot.message_handler(content_types=['text'])
def handle_text(message):
    cid = message.chat.id
    if len(str(message.text)) >= 60:
        bot.send_message(message.from_user.id,
                         emoji.emoji_codes_dict[":no_entry_sign:"] + "Очень длинный поисковый запрос" +
                         emoji.emoji_codes_dict[":no_entry_sign:"])
        logging.info("Search request from [%s] is too long", cid)
        return
    try:
        logging.info(str(datetime.datetime.now()) + ": " + "Search request " + "from " + "[" + str(cid) + "] " + str(
            message.chat.first_name) + " " + str(
            message.chat.last_name) + " searches: " + str(message.text))
    except Exception as e:
        logging.error("Search request from error=%s", e)
        logging.exception("Search request from")
        pass
    if any(word in message.text.lower() for word in forbidden_words):
        bot.send_message(message.from_user.id,
                         emoji.emoji_codes_dict[":no_entry_sign:"] + "Ой,не стоит искать всякую гадость тут." +
                         emoji.emoji_codes_dict[":no_entry_sign:"])
    else:
        for fullBadWord in forbidden_words_full:
            text = str(message.text.lower()).encode("utf-8")
            text2 = str(fullBadWord.lower()).encode("utf-8")
            if text2 == text:
                bot.send_message(message.from_user.id,
                                 emoji.emoji_codes_dict[":no_entry_sign:"] + "Ой,не стоит искать всякую гадость тут." +
                                 emoji.emoji_codes_dict[":no_entry_sign:"])
                return
            pass
        pass
        if not database.is_user_exist(cid):
            database.add_user_to_db(message)
        database.set_user_last_search_request_to_db(message)
        retry = 0
        isGone = True
        while isGone:
            try:
                retry += 1
                if retry > 10:
                    isGone = False
                bot.send_chat_action(message.from_user.id, 'typing')
                cid = message.chat.id

                vk_response = vk_connection.send_api_search_request(message.text, 1000, 1).get("response", 0)
                users_vk_response[cid] = vk_response
                is_search_performed[cid] = True
                logging.info("Got valid response from VK")
                bot.send_chat_action(message.from_user.id, 'typing')  # show the bot "typing" (max. 5 secs)
                time.sleep(0.2)
                count = vk_response.get("count")
                if count == 0:
                    bot.send_message(message.from_user.id,
                                     emoji.emoji_codes_dict[":no_entry_sign:"] + "Прости,но я ничего не нашёл")
                    logging.info("Nothing found")
                    isGone = False
                else:
                    filteredResponse = {'count': 0}
                    items = vk_response.get("items")
                    for item in items:
                        item_new = {'id': item.get("id", 0), 'size': item.get("size", 0),
                                    'title': item.get("title", 0),
                                    'url': item.get("url", 0), 'type': item.get("type", 0),
                                    'ext': item.get("ext", 0)}
                        filteredResponse[filteredResponse.get('count')] = item_new
                        filteredResponse['count'] = filteredResponse.get('count') + 1
                    pass
                    count = int(filteredResponse.get("count"))
                    if count != 0:
                        bot.send_message(message.from_user.id,
                                         "Я нашёл " + str(
                                             count) + " файлов. " + "Ну что, давай отсортируем их?")
                        show_keyboard(message)
                        isGone = False
                    else:
                        bot.send_message(message.from_user.id,
                                         emoji.emoji_codes_dict[
                                             ":no_entry_sign:"] + "Прости,но я ничего не нашёл")
                        isGone = False
                    pass
                pass
            except Exception as e:
                logging.exception("Exception in func handle_text error = %s", e)
                time.sleep(random.randint(1, 3))
                pass
            pass
        pass
    pass


bot.send_message(constants.MY_CID, emoji.emoji_codes_dict[":computer:"] + "The user started the interaction" + "\n" +
                 "Current users in DB: " + str(database.count_all_users()) + "\n")
bot.set_update_listener(listener)  # register listener

__author__ = 'Daniil Nikulin'
__copyright__ = "Copyright 2017,VK File Bot"
__license__ = "Apache License 2.0"
__version__ = "1.0"
__maintainer__ = "Daniil Nikulin"
__email__ = "danil.nikulin@gmail.com"
__status__ = "Production"

from telebot import types
from config import emoji

commands = {  # command description used in the "help" command
    'start': 'Начало работы со мной',
    'help': 'Вся необходимая информация'
}
tips = {  # tips description used in the "tips" command
    'Совет №1': "Если ищешь книгу " + emoji.emoji_codes_dict[
        ":blue_book:"] + ", то часто легче найти в pdf или djvu с помощью "
                         "кнопки" + "<b>" + "\n" + "[ Текст(pdf,doc) ]" + emoji.emoji_codes_dict[
                    ":page_facing_up:"] + "</b>" + " (кнопки появятся внизу вместо клавиатуры)",

    'Совет №2': "Если ты из Украины " + emoji.emoji_codes_dict[":U:"] + emoji.emoji_codes_dict[":A:"] +
                " выбирай способ загрузки " + "<b>" + "Файл" + "</b>" \
                + " и тебе не понадобится скачивать по ссылке на VK (заблокрованый ресурс).",

    'Совет №3': "Музыку трудно найти тут, все борятся с пиратством. Скорее всего ты найдешь "
                "рингтон по своему запросу. Но любимая песня на звонке, разве не подарок? " + emoji.emoji_codes_dict[
                    ":grinning:"],

    'Совет №4': "Гифки ищются легко и непринужденно (особенно на русском), но всё же в Телеграме лучшие гифки тут " + "@gif. ",

    'Совет №5': "Современную музыку " + emoji.emoji_codes_dict[":musical_score:"] + " в " + "<b>" + "mp3" + "</b>" +
                " найти тут сложновато, но почти всегда есть в формате "
                + "<b>" + "flac" + "</b>" + "."
}
types_dict = {  # types description used in the "types" command
    "Все": "Все файлы найденные по запросу",
    emoji.emoji_codes_dict[
        ":page_facing_up:"] + "Текст(pdf,doc)": 'dpf, doc, docx, txt, odt...',

    emoji.emoji_codes_dict[":open_book:"] + "Книги": "epub, fb2...",
    emoji.emoji_codes_dict[":compression :"] + "Архивы": 'zip, rar, 7z...',
    "Gif": 'Анимации: gif',
    emoji.emoji_codes_dict[":frame_photo"] + "Изображения": 'jpg, jpeg, bmp, png, m3d ,tif...',
    emoji.emoji_codes_dict[":musical_note:"] + "Аудио": 'flac, mp3, m4r, mp2, wav',
    emoji.emoji_codes_dict[":video_camera:"] + "Видео": 'mp4, webm, mkv, 3gp',
}


# Define Keyboard
type_select = types.ReplyKeyboardMarkup(one_time_keyboard=True)
type_select.row("Все", "Текст(pdf,doc)" + emoji.emoji_codes_dict[":page_facing_up:"])
type_select.row("Книги" + emoji.emoji_codes_dict[":open_book:"], "Архивы" + emoji.emoji_codes_dict[":compression :"])
type_select.row("Gif", "Изображения" + emoji.emoji_codes_dict[":frame_photo"])
type_select.row("Аудио" + emoji.emoji_codes_dict[":musical_note:"], "Видео" + emoji.emoji_codes_dict[":video_camera:"])
hide_board = types.ReplyKeyboardRemove()  # if sent as reply_markup, will hide the keyboard
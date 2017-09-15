# VK Files Bot
Telegram Bot for searching and downloading files from VK.<br>
Available on Telegram [ [VK Files Bot on Telegram](https://t.me/VKFiles_Bot) ] <br>

This bot will allow you to search and download public files in VK (Vkontakte). You can search and filter files by categorie (Audio, Images, Gifs etc.) and download file from Telegram (**bot sends file right in your chat** or you can just get a link). The project is hosted on Heroku.


## Overview
![alt text](https://raw.githubusercontent.com/ddci/vkfilebot/master/img/overview.jpg "Preview")

* **Moderation system**: just add the root you want to ban to forbidden_roots.txt (block all words with this substring in a message) or to swear_words.txt. <br>
* I use **DB** to store user's steps and chat ids. <br>
### Requirements

#### Runtime
```Python-3.6.1```
#### Instalation using pip:
```Bash
$ pip install pyTelegramBotAPI
$ pip install requests
$ pip install transliterate
$ pip install Flask
$ pip install MarkupSafe
$ pip install transliterate
$ pip install SQLAlchemy
$ pip install Flask-SQLAlchemy
```



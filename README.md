# vkfilebot - VK Files Bot
Telegram Bot for searching and downloading files from VK <br>
Available on Telegram [t.me/VKFiles_Bot](https://t.me/VKFiles_Bot) <br>

Have you ever tried to search some books for studying across the internet? If yes then you know how difficult it can be when you try to find books or files you need.<br> Largest European social networking service VK contains a lot of files (books, articles, guides) that can help you in studying, work etc.
This Bot makes my little dream come true. You just search what you need, and Bot downloads it for you and sends you file.
You do not need to interact with VK servers, and if VK is banned in your country you will still have access to VK's public files


## Requirements
Installation using pip (a Python package manager): <br>

```Bash
$ Pip install pyTelegramBotAPI
$ Pip install requests
$ Pip install transliterate
$ Pip install Flask
$ Pip install MarkupSafe
$ Pip install transliterate
$ Pip install SQLAlchemy
$ Pip install Flask-SQLAlchemy
```
## Runtime
```Python-3.6.1```

## Overview
![alt text](https://raw.githubusercontent.com/ddci/vkfilebot/master/img/overview.jpg "Preview")
Bot has moderation system: just add the word you want to ban to swearWords.txt (block all words with this substring in a message) and fullSwearWords.txt <br>
Bot is connected DB to store user's steps and chat ids <br>


# -*- coding: utf-8 -*
"""
    File name: commands
    Author: Daniil Nikulin
    Date created: 03.07.2017
    Date last modified: 06.07.2017
    Python Version: 3.6.1
"""
import http.client
import json
import time


# Запрос к API VK.
def getApiConnection():
    return http.client.HTTPSConnection("api.vk.com")


# Открытие соединения с VK.
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

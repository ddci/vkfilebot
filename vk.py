# -*- coding: utf-8 -*
__author__ = 'Daniil Nikulin'
__copyright__ = "Copyright 2017,VK File Bot"
__license__ = "Apache License 2.0"
__version__ = "1.0"
__maintainer__ = "Daniil Nikulin"
__email__ = "danil.nikulin@gmail.com"
__status__ = "Production"
import logging
import time
import urllib
from urllib.parse import urlparse
import requests
logging.basicConfig(level=logging.DEBUG)


class VKConnectionAPI(object):
    API_URL = 'https://api.vk.com/method/'
    DEFAULT_API_VERSION = '5.64'

    def __init__(self, access_token):
        self.access_token = access_token

    def _request_api(self, url):
        try:
            url_to_server = self.API_URL + url
            vk_response_json = requests.get(url_to_server).json()
            # Too many requests per second.
            if vk_response_json.get("response", 0) == 0 or vk_response_json.get("response", 0) is None:
                if vk_response_json.get("error", 0).get("error_code", 0) == 6:
                    time.sleep(0.35)
                    return self._request_api(url)
            return vk_response_json
        except Exception as e:
            logging.error("_request_api error=%s", e)
            logging.exception("_request_api")

    def send_api_search_request(self, text, count, offset):
        search_text = urllib.parse.quote(text)
        url = 'docs.search?q=' + search_text + '&count=' + str(count) \
              + '&offset=' + str(offset) + '&access_token=' + str(self.access_token) + '&v=' + self.DEFAULT_API_VERSION
        try:
            return self._request_api(url)
        except Exception as e:
            logging.error("send_api_search_request", e)

import requests
import logging
import time
import typing
from urllib.parse import urlencode

import hmac
import hashlib

import websocket
import json
import threading

from models import  *

logger = logging.getLogger()

class BitmexClient:
    def __init__(self,public_key:str,secret_key:str, testnet:bool):

        if testnet:
            self._base_url = "https://testnet.bitmex.com"
            self._wss_utl = "wss://testnet.bitmex.com/realtime"
        else:
            self._base_url = "https://www.bitmex.com"
            self._wss_utl = "wss://ws.bitmex.com/realtime"
        self._public_key = public_key
        self._secret_key = secret_key

        self._ws = None

        self.contracts = self.get_contracts()
        self.balances = self.get_balances()

        self.prices = dict()

        t = threading.Thread(target=self._start_ws)
        t.start()

        logger.info("Bitmex Client successfully initialized")

    def _generate_signature(self,method:str,endpoint:str,expires:str,data: typing.Dict):
        if len(data)>0:
            message = method + endpoint + "?" + urlencode((data)) + expires
        else:
            message = method + endpoint + expires

    def _make_request(self, method: str, endpoint: str, data: typing.Dict):

        headers = dict()
        expires = str(int(time.time()) + 5)
        headers['api-expires'] = expires
        headers['api-key'] = self._public_key
        headers['api-signature'] = self._generate_signature(method,endpoint,expires,data)


        if method == "GET":
            try:
                response = requests.get(self._base_url + endpoint, params=data, headers = headers)
            except Exception as e:
                logger.error("Connection error while making %s request to %s: %s", method, endpoint, e)
                return None

        elif method == "POST":
            try:
                response = requests.post(self._base_url + endpoint, params=data, headers = headers)
            except Exception as e:
                logger.error("Connection error while making %s request to %s: %s", method, endpoint, e)
                return None

        elif method == "DELETE":
            try:
                response = requests.delete(self._base_url + endpoint, params=data, headers= headers)
            except Exception as e:
                logger.error("Connection error while making %s request to %s: %s", method, endpoint, e)
                return None
        else:
            raise ValueError()

        if response.status_code == 200:
            return response.json()
        else:
            logger.error("Error while making %s request to %s: %s (error code %s)",
                         method, endpoint, response.json(), response.status_code)
            return None








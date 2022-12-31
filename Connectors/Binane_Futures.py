# We will start with the public data means the data which do not require authentication
# 3 functions - one - list of contracts, two - historical data, three - snapshot of bid and ask price

import logging
import typing

import requests
import time

from urllib.parse import urlencode

import hmac
import hashlib

import websocket

import threading

import json
import sys

sys.path.insert(0, "D:\programming\TradingBot")
from models import *

logger = logging.getLogger()


class BinanceFuturesClient:

    def __init__(self, public_key, secret_key, testnest: bool):  # class needs to know with whom we will interact the testnest or the binance
        if testnest:
            self.base_url = "https://testnet.binancefuture.com/"
            self.wss_url = "wss://stream.binancefuture.com/ws"
        else:
            self.base_url = "https://fapi.binance.com"
            self.wss_url = "wss://fstream.binance.com/ws"

        self.public_key = public_key
        self.secret_key = secret_key

        self.headers = {'X-MBX-APIKEY': self.public_key}

        self.prices = dict()

        self.contracts = self.get_contracts()
        self.balances = self.get_balance()

        self.id = 1
        self.ws = None

        t = threading.Thread(target=self.start_ws)  # We will use thread to run because start_ws is infinite loop which is waiting for the messages from server and if we exeute it in main then any code underneath it will not execute
        t.start()

        logger.info("Binance Futures Client successfully initialized")

    def generate_signature(self, data):
        return hmac.new(self.secret_key.encode(), urlencode(data).encode(),
                        hashlib.sha256).hexdigest()  # .encode converts the key into bits and now we need to convert the dict into query string as shown in documentation

    def make_requests(self, method, endpoint, data):  # http arguments (GET,POST,DELETE), endpoint and parameters
        if method == "GET":
            try:
                response = requests.get(self.base_url + endpoint, params=data, headers=self.headers)
            except Exception as e:
                logger.error("Connection error while making %s request to %s: %s", method, endpoint, e)
                return None
        elif method == "POST":
            try:
                response = requests.post(self.base_url + endpoint, params=data, headers=self.headers)
            except Exception as e:
                logger.error("Connection error while making %s request to %s: %s", method, endpoint, e)
                return None
        elif method == "DELETE":
            try:
                response = requests.delete(self.base_url + endpoint, params=data, headers=self.headers)
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

    def get_contracts(self):
        exchange_info = self.make_requests("GET", "/fapi/v1/exchangeInfo", None)
        contracts = dict()
        if exchange_info is not None:
            for contract_data in exchange_info['symbols']:
                contracts[contract_data['pair']] = Contract(contract_data, "binance")
        return contracts

    def get_historical_candles(self, contract: Contract, interval):
        data = dict()
        data['symbol'] = contract.symbol
        data['interval'] = interval
        data['limit'] = 1000

        raw_candles = self.make_requests('GET', '/fapi/v1/klines', data)

        candles = []  # return response is in list

        for c in raw_candles:
            candles.append(Candle(c))  # open time, open, high, low, close, volume
        return candles

    def get_bid_ask(self, contract: Contract):  # symbol = contract name
        data = dict()
        data['symbol'] = contract.symbol
        ob_data = self.make_requests("GET", "/fapi/v1/ticker/bookTicker", data)  # order-book data

        if ob_data is not None:
            if contract.symbol not in self.prices:
                self.prices[contract.symbol] = {'bid': float(ob_data['bidPrice']), 'ask': float(ob_data['askPrice'])}
            else:
                self.prices[contract.symbol]['bid'] = float(ob_data['bidPrice'])
                self.prices[contract.symbol]['ask'] = float(ob_data['askPrice'])
            return self.prices[contract.symbol]

    # Private_endpoints

    # if we explore documentation we will see that depending on the endpoint we might need to add header to our request.
    # We send our API key by passing a header to our request. In python header is a dict to pass as argument in get method
    # Additional parameter to authenticate our request from documentation is a signature. It is a long and complicated string and is generated by hmac sha-256
    # We will input our seret api key and  a string (msg - concatenation of all the parameters we are sending with our request)

    def get_balance(self):
        data = dict()
        data['timestamp'] = int(time.time() * 1000)
        data['signature'] = self.generate_signature(data)

        balances = dict()

        account_data = self.make_requests("GET", "/fapi/v2/account", data)
        if account_data is not None:
            for a in account_data['assets']:
                balances[a['asset']] = Balances(a)
        return balances

    def place_order(self, contract: Contract, side, quantity, order_type, price=None, tif=None):
        data = dict()
        data['symbol'] = contract.symbol
        data['side'] = side
        data['quantity'] = quantity
        data['type'] = order_type

        if price is not None:
            data['price'] = price

        if tif is not None:
            data['timeInForce'] = tif

        data['timestamp'] = int(time.time() * 1000)
        data['signature'] = self.generate_signature(data)

        order_status = self.make_requests("POST", "/fapi/v1/order", data)

        if order_status is not None:
            order_status = OrderStatus(order_status)

        return order_status

    def cancel_order(self, contract: Contract, order_id):
        data = dict()
        data['symbol'] = contract.symbol
        data['orderId'] = order_id

        data['timestamp'] = int(time.time() * 1000)
        data['signature'] = self.generate_signature(data)

        order_status = self.make_requests("DELETE", "/fapi/v1/order", data)

        if order_status is not None:
            order_status = OrderStatus(order_status)

        return order_status

    def get_order_status(self, contract: Contract, order_id):

        data = dict()
        data['timestamp'] = int(time.time() * 1000)
        data['symbol'] = contract.symbol
        data['orderId'] = order_id
        data['signature'] = self.generate_signature(data)

        order_status = self.make_requests("GET", "/fapi/v1/order", data)

        if order_status is not None:
            order_status = OrderStatus(order_status)

        return order_status

    # WebsocketAPI functions

    def start_ws(self):
        self.ws = websocket.WebSocketApp(self.wss_url, on_open=self.on_open, on_close=self.on_close,
                                         on_error=self.on_error, on_message=self.on_message)
        while True:
            try:
                self.ws.run_forever()
            except Exception as e:
                logger.error("Binance error in run_forever() method: %s,e")
            time.sleep(2)

    def on_open(self, ws):
        logger.info("Binance connection opened")

        self.subscribe_channel(list(self.contracts.values()), "bookTicker")

    def on_close(self, ws, *args,**kwargs):
        logger.warning("Binance Websocket connection closed")

    def on_error(self, ws, msg):
        logger.error("Binance connection error: %s", msg)

    def on_message(self, ws, msg):  # This method will convert json str that we have recieved to a json object

        data = json.loads(msg)

        if "e" in data:
            if data['e'] == 'bookTicker':
                symbol = data['s']

                if symbol not in self.prices:
                    self.prices[symbol] = {'bid': float(data['b']), 'ask': float(data['a'])}
                else:
                    self.prices[symbol]['bid'] = float(data['b'])
                    self.prices[symbol]['ask'] = float(data['a'])
                print(self.prices[symbol])

    def subscribe_channel(self, contracts: typing.List[Contract], channel: str):
        data = dict()
        data['method'] = 'SUBSCRIBE'
        data['params'] = []

        for contract in contracts:
            data['params'].append(contract.symbol.lower() + "@" + channel)
        data['id'] = self.id

        try:
            self.ws.send(json.dumps(data))
        except Exception as e:
            logger.error("Websocket error while subscribing to %s %S updates: %s", len(contracts), channel, e)

        self.id += 1

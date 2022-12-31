import logging
import requests
import pprint

#"https://fapi.binance.com" f stands for futures
#"https://testnet.binancefuture.com"
#Both are REST(Representaional State Transfer) APIs and will be used to place,cancel,order status and check balance as it requires to request the server and get the response
#"wss://fstream.binance.com"
#Websocket API will get live market data as a constant flow
#Binance and bitmex APIs return the response in Json format and it is a DS just like dictionary

logger = logging.getLogger()

#ForBinance
def printlistofcontracts():
    response_object = requests.get("https://fapi.binance.com/fapi/v1/exchangeInfo")
    print(response_object.status_code)
    pprint.pprint (response_object.json())

def binancecontracts():
    response_object = requests.get("https://fapi.binance.com/fapi/v1/exchangeInfo")
    contract = []
    for contracts in response_object.json()['symbols']:
        contract.append(contracts['pair'])
    return contract

#ForBitmex
def bitmexcontracts():
    response_object = requests.get("https://www.bitmex.com/api/v1/instrument/active")
    contract = []
    for contracts in response_object.json():
        contract.append(contracts['symbol'])
    return contract
print(printlistofcontracts())


import logging
from connectors.binance import BinanceClient
from connectors.bitmex import BitmexClient
import tkinter as tk
from interface.root_component import Root

logger = logging.getLogger()

logger.setLevel(logging.DEBUG)  

stream_handler = logging.StreamHandler()  
formatter = logging.Formatter('%(asctime)s %(levelname)s :: %(message)s')
stream_handler.setFormatter(formatter)
stream_handler.setLevel(logging.INFO)  

file_handler = logging.FileHandler('info.log')  
file_handler.setFormatter(formatter)
file_handler.setLevel(logging.DEBUG) 

logger.addHandler(stream_handler)
logger.addHandler(file_handler)


if __name__ == '__main__':

    binance = BinanceFuturesClient("2875f8141548255e41f151c0732c6632ac5c8e1ebfd5e1b4f51a4e78600cbb2a", "9601d2ea5ecb2b7b53884f617e82d954468f0b14821b1302e9f67d8d45096436", True)

    bitmex = BitmexClient("", "", True)

    root = tk.Tk()
    root.mainloop()

import tkinter as tk
import logging
from Connectors.Binane_Futures import BinanceFuturesClient
import pprint

logger = logging.getLogger()        #Logger.debug/info/warning/error

logger.setLevel(logging.INFO)

stream_handler = logging.StreamHandler()    #This will display msg in python terminal
formatter = logging.Formatter('%(asctime)s %(levelname)s :: %(message)s')
stream_handler.setFormatter(formatter)
stream_handler.setLevel(logging.INFO)

file_handler = logging.FileHandler('Firstlogger.log') #This will create a log file when we execute the code
file_handler.setFormatter(formatter)
file_handler.setLevel(logging.DEBUG)

logger.addHandler(stream_handler)
logger.addHandler(file_handler)

logger.info('this is logged in all cases')



if __name__ == '__main__':          #Visual interface will only execute in main.py and will not execute if we import this module to other file
    
    binance = BinanceFuturesClient("2875f8141548255e41f151c0732c6632ac5c8e1ebfd5e1b4f51a4e78600cbb2a", "9601d2ea5ecb2b7b53884f617e82d954468f0b14821b1302e9f67d8d45096436", True)

    print(binance.balances["USDT"].wallet_balance)
    #print(binance.place_order(binance.contracts["BTCUSDT"], "BUY",1,"LIMIT",price=10000,tif="GTC").order_id)
    root = tk.Tk()                  #It helps to display the root window and manages all the other components of the tkinter application
    root.mainloop()                 #input loop #GTC - good till cancelled



#Logger will be used to display msg in python terminal for debugging purpose

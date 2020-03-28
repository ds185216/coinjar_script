import json
import requests
import urllib
from urllib.request import Request, urlopen
import time
import datetime
import pandas as pd
import pickle
import schedule
import itertools
from itertools import *

def calc_ema(num, today, yesterday):
	k = 2/(num+1)
	EMA = float(today)*k+float(yesterday)*(1-k)
	return EMA

db_buy = pd.read_pickle('db_buy')
db_sell = pd.read_pickle('db_sell')

ema_range = list(itertools.product(range(2, 15), repeat=2))
currencies = [i for i in db_buy.columns if 'AUD' in i]
final_ema = [0,0]
final_cash = 0
final_cur = ""

for CUR in currencies:
	buy_prices = [y for y in db_buy[CUR]]
	sell_prices = [y for y in db_sell[CUR]]
	for test_EMA in ema_range:
		cash = 1000.00
		BTC = 0
		for i in range(len(buy_prices)):
			today = False
			if i >= test_EMA[1]:
				if calc_ema(test_EMA[1], sell_prices[i], sell_prices[i-(test_EMA[1])]) > float(sell_prices[i]):
					#test sell
					cash = cash + round(BTC * float(sell_prices[i]))
					BTC= 0
					today = True
			if i >= test_EMA[0] and today != True:
				if calc_ema(test_EMA[0], buy_prices[i], buy_prices[i-(test_EMA[0])]) < float(buy_prices[i]):
					#test buy
					BTC = BTC + (round(cash) / float(buy_prices[i]))
					cash = 0
					#cash = cash - round(cash * 1)

		if BTC != 0:
			cash = cash + round(BTC * float(sell_prices[i]))
			BTC= 0
		if cash > final_cash:
			final_cash = cash
			final_ema = test_EMA
			final_cur = CUR

print ('daily',final_cur, final_ema, final_cash)

with open('holder', 'wb') as handle:
	pickle.dump(final_cur, handle)
	pickle.dump(final_ema, handle)


db_buy = pd.read_pickle('db_buy-hourly')
db_sell = pd.read_pickle('db_sell-hourly')

ema_range = list(itertools.product(range(2, 160), repeat=2))
currencies = [i for i in db_buy.columns if 'AUD' in i]
final_ema = [0,0]
final_cash = 0
final_cur = ""

for CUR in currencies:
	buy_prices = [y for y in db_buy[CUR]]
	sell_prices = [y for y in db_sell[CUR]]
	for test_EMA in ema_range:
		cash = 1000.00
		BTC = 0
		for i in range(len(buy_prices)):
			today = False
			if i >= test_EMA[1]:
				if calc_ema(test_EMA[1], sell_prices[i], sell_prices[i-(test_EMA[1])]) > float(sell_prices[i]):
					#test sell
					cash = cash + round(BTC * float(sell_prices[i]))
					BTC= 0
					today = True
			if i >= test_EMA[0] and today != True:
				if calc_ema(test_EMA[0], buy_prices[i], buy_prices[i-(test_EMA[0])]) < float(buy_prices[i]):
					#test buy
					BTC = BTC + (round(cash) / float(buy_prices[i]))
					cash = 0
					#cash = cash - round(cash * 1)

		if BTC != 0:
			cash = cash + round(BTC * float(sell_prices[i]))
			BTC= 0
		if cash > final_cash:
			final_cash = cash
			final_ema = test_EMA
			final_cur = CUR

print ('hourly',final_cur, final_ema, final_cash)

with open('holder-hourly', 'wb') as handle:
	pickle.dump(final_cur, handle)
	pickle.dump(final_ema, handle)
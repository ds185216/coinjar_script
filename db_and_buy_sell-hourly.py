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

def readsettings():
	global refresh, invest, def_percent, token
	with open('cjsettings.txt') as json_file:  
		data = json.load(json_file)[0]
		refresh = data['refresh']
		invest = data['invest']
		def_percent = data['def_percent']
		token = data['token']

def writesettings():
	data = []
	data.append({
		'refresh':refresh,
		'invest':invest,
		'def_percent':def_percent,
		'token':token
		})
	with open('cjsettings.txt', 'w') as outfile:  
		json.dump(data, outfile)

try:
	readsettings()
except:
	writesettings()

if token == "":
	print ("No token found")
	exit()

headers = {'Content-Type': 'application/json; charset=utf-8', 'Authorization': 'Token token=%s' % token}

def buy_sell_product(BUY_SELL, W, X, Y):
	global today
	values = {"product_id": W, "type": "LMT", "side": BUY_SELL, "price": str(X), "size": str(Y), "time_in_force": "GTC"}
	r = requests.post('https://api.exchange.coinjar.com/orders', data=json.dumps(values), headers=headers)
	if r.status_code == 200:
		print("Transaction OK")
		today = True
	else:
		print("Some bogus error", r.reason)
		print(values)

def write_daily(token_entry):
	global headers
	products = json.loads(urlopen(Request('https://api.exchange.coinjar.com/products', headers=headers)).read().decode('utf-8'))
	product_list = [i['id'] for i in products]
	buy_price = []
	sell_price = []
	for i in product_list:
		url = "https://data.exchange.coinjar.com/products/%s/ticker" % i
		b = json.loads(urlopen(Request(url)).read().decode('utf-8'))
		buy_price.append(b['ask'])
		sell_price.append(b['bid'])

	try:
		db_buy = pd.read_pickle('db_buy-hourly')
		db_sell = pd.read_pickle('db_sell-hourly')

		new_row = pd.DataFrame(buy_price).transpose()
		new_row.columns = product_list
		new_row.rename(index={0 : str(datetime.datetime.now())}, inplace=True)
		db_buy = db_buy.append(new_row)

		new_row = pd.DataFrame(sell_price).transpose()
		new_row.columns = product_list
		new_row.rename(index={0 : str(datetime.datetime.now())}, inplace=True)
		db_sell = db_sell.append(new_row)
	except:
		db_buy = pd.DataFrame(buy_price).transpose()
		db_buy.columns = product_list
		db_buy.rename(index={0 : str(datetime.datetime.now())}, inplace=True)
		db_sell = pd.DataFrame(buy_price).transpose()
		db_sell.columns = product_list
		db_sell.rename(index={0 : str(datetime.datetime.now())}, inplace=True)
	print (db_buy)
	db_buy.to_pickle('db_buy-hourly')
	db_sell.to_pickle('db_sell-hourly')

#test to find ema periods and best currency to work with

	ema_range = list(itertools.product(range(2, 360), repeat=2))
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

#_______________________________________________________________________

#Buy_sell part

# work on all currencies with the sell patterns for when final_cur has changed to something else
	with open('holder', 'rb') as handle:
		holder_cur = pickle.load(handle)
		holder_ema = pickle.load(handle)
	buy_prices = [y for y in db_buy[final_cur]]
	sell_prices = [y for y in db_sell[holder_cur]]
	accounts = json.loads(urlopen(Request('https://api.exchange.coinjar.com/accounts', headers=headers)).read().decode('utf-8'))
	today = False
	if len(db_buy) > 360:
		if calc_ema(holder_ema, round(float(sell_prices[-1]), 2), sell_prices[-1-(holder_ema)]) > float(sell_prices[-1]):
			for X in range(len(accounts)):
				if accounts[X]['asset_code'] != 'AUD' and accounts[X]['asset_code'] in holder_cur:
					ASSET = X
			if float(accounts[ASSET]['available']) > 0:
				buy_sell_product("sell", holder_cur, sell_prices[-1], accounts[ASSET]['available'])
				today = True
		if today != True or holder_cur != final_cur:
			if calc_ema(final_ema[0], buy_prices[-1], buy_prices[-1-(final_ema[0])]) < float(buy_prices[-1]):
				if float(accounts[0]['available']) > 0:
					buy_sell_product("buy", final_cur, round(float(buy_prices[-1]), 2), (float(accounts[0]['available'])/float(buy_prices[-1])))
					with open('holder', 'wb') as handle:
						pickle.dump(final_cur, handle)
						pickle.dump(final_ema[1], handle)

#_________________________________________________________________________
schedule.every().hour.at(":00").do(write_daily, token)
while True:
	schedule.run_pending()
	time.sleep(60)

#write_daily(token)

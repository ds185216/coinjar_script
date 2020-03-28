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
	values = {"product_id": W, "type": "LMT", "side": BUY_SELL, "price": str(X), "size": str(Y), "time_in_force": "GTC"}
	r = requests.post('https://api.exchange.coinjar.com/orders', data=json.dumps(values), headers=headers)
	if r.status_code == 200:
		print("Transaction OK")
	else:
		print("Some bogus error", r.reason)
		print(values)

def write_daily(token_entry):
	global headers
	try:
		products = json.loads(urlopen(Request('https://api.exchange.coinjar.com/products', headers=headers)).read().decode('utf-8'))
		product_list = [i['id'] for i in products]
	except:
		db_buy = pd.read_pickle('db_buy')
		product_list = [x for x in db_buy]
	
	retries = 0
	success = False
	while not success:
		try:
			buy_price = []
			sell_price = []
			for i in product_list:
				url = "https://data.exchange.coinjar.com/products/%s/ticker" % i
				b = json.loads(urlopen(Request(url)).read().decode('utf-8'))
				buy_price.append(b['ask'])
				sell_price.append(b['bid'])
			success = True
		except:
			print ('Timeout error, attempt:', retries)
			time.sleep(5)
			retries +=1
			if retries == 30:
				db_buy = pd.read_pickle('db_buy')
				db_sell = pd.read_pickle('db_sell')
				buy_price = [x for x in db_buy.iloc[-1]]
				sell_price = [x for x in db_sell.iloc[-1]]
				success = True
	try:
		db_buy = pd.read_pickle('db_buy')
		db_sell = pd.read_pickle('db_sell')

		new_row = pd.DataFrame(buy_price).transpose()
		new_row.columns = product_list
		new_row.rename(index={0 : str(datetime.date.today())}, inplace=True)
		db_buy = db_buy.append(new_row, sort=True)

		new_row = pd.DataFrame(sell_price).transpose()
		new_row.columns = product_list
		new_row.rename(index={0 : str(datetime.date.today())}, inplace=True)
		db_sell = db_sell.append(new_row, sort=True)
	except:
		db_buy = pd.DataFrame(buy_price).transpose()
		db_buy.columns = product_list
		db_buy.rename(index={0 : str(datetime.date.today())}, inplace=True)
		db_sell = pd.DataFrame(buy_price).transpose()
		db_sell.columns = product_list
		db_sell.rename(index={0 : str(datetime.date.today())}, inplace=True)

	db_buy.to_pickle('db_buy')
	db_sell.to_pickle('db_sell')

#buy sell part
	with open('holder', 'rb') as handle:
		final_cur = pickle.load(handle)
		final_ema = pickle.load(handle)

	print (db_buy[final_cur])

	buy_prices = [y for y in db_buy[final_cur]]
	sell_prices = [y for y in db_sell[holder_cur]]
	accounts = json.loads(urlopen(Request('https://api.exchange.coinjar.com/accounts', headers=headers)).read().decode('utf-8'))
	today = False
	if calc_ema(holder_ema, round(float(sell_prices[-1]), 2), sell_prices[-1-(holder_ema)]) > float(sell_prices[-1]):
		for X in range(len(accounts)):
			if accounts[X]['asset_code'] != 'AUD' and accounts[X]['asset_code'] in holder_cur:
				ASSET = X
		if float(accounts[ASSET]['available']) > 0:
			buy_sell_product("sell", holder_cur, sell_prices[-1], accounts[ASSET]['available'])
			today = True
	if today != True:
		if calc_ema(final_ema[0], buy_prices[-1], buy_prices[-1-(final_ema[0])]) < float(buy_prices[-1]):
			if float(accounts[0]['available']) > 0:
				buy_sell_product("buy", final_cur, round(float(buy_prices[-1]), 2), (float(accounts[0]['available'])/float(buy_prices[-1])))

#_________________________________________________________________________

schedule.every().day.at("00:00").do(write_daily, token)
while True:
	schedule.run_pending()
	time.sleep(60)

#write_daily(token)

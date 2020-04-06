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
import math

def calc_ema(num, today, yesterday):
	k = 2/(num+1)
	EMA = float(today)*k+float(yesterday)*(1-k)
	return EMA

def calc_wma(num, data):
	first_sum = 0
	for i in range(1, num+1):
		first_sum = first_sum + (float(data[-i]) * i)
	return first_sum/sum(range(1, num+1))

def calc_hma(num, _data):
	half_length = int(num/2)
	sqrt_length = int(math.sqrt(num))
	new_list = []
	for i in range(1, sqrt_length+1):
		wma1 = calc_wma(half_length, _data[-(i+half_length):-i])
		wma2 = calc_wma(num, _data[-(i+num):-i])
		new_list.append(2 * wma1 - wma2)
	return calc_wma(sqrt_length, new_list)

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
		print("Transaction OK", BUY_SELL, W, X)
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
		db_buy = pd.read_pickle('db_buy-hourly')
		db_sell = pd.read_pickle('db_sell-hourly')

		new_row = pd.DataFrame(buy_price).transpose()
		new_row.columns = product_list
		new_row.rename(index={0 : str(datetime.datetime.now())}, inplace=True)
		db_buy = db_buy.append(new_row, sort=True)

		new_row = pd.DataFrame(sell_price).transpose()
		new_row.columns = product_list
		new_row.rename(index={0 : str(datetime.datetime.now())}, inplace=True)
		db_sell = db_sell.append(new_row, sort=True)
	except:
		db_buy = pd.DataFrame(buy_price).transpose()
		db_buy.columns = product_list
		db_buy.rename(index={0 : str(datetime.datetime.now())}, inplace=True)
		db_sell = pd.DataFrame(buy_price).transpose()
		db_sell.columns = product_list
		db_sell.rename(index={0 : str(datetime.datetime.now())}, inplace=True)

	db_buy.to_pickle('db_buy-hourly')
	db_sell.to_pickle('db_sell-hourly')

#buy sell part
	with open('moving-averages-hourly', 'rb') as handle:
		final_formula = pickle.load(handle)
		final_cur = pickle.load(handle)
		final_ma = pickle.load(handle)
		reverse = pickle.load(handle)

	buy_prices = [y for y in db_buy[final_cur]]
	sell_prices = [y for y in db_sell[final_cur]]
	accounts = json.loads(urlopen(Request('https://api.exchange.coinjar.com/accounts', headers=headers)).read().decode('utf-8'))
	today = False
	if len(db_buy) > 1488:
		
		if final_formula == 'EMA':
			average = calc_ema(final_ma[1], round(float(sell_prices[-1]), 2), sell_prices[-1-(final_ma[1])])
		elif final_formula == 'HMA':
			average = calc_hma(final_ma[1], sell_prices[-(final_ma[1]+int(math.sqrt(final_ma[1]))):-1])
		elif final_formula == 'WMA':
			average = calc_wma(final_ma[1], sell_prices[-(final_ma[1]):-1]) 
		
		if average > float(sell_prices[-1]) or reverse == True and average < float(sell_prices[-1]):
			for X in range(len(accounts)):
				if accounts[X]['asset_code'] != 'AUD' and accounts[X]['asset_code'] in final_cur:
					ASSET = X
			if float(accounts[ASSET]['available']) > 0:
				buy_sell_product("sell", final_cur, sell_prices[-1], accounts[ASSET]['available'])
				today = True


		if today != True:
			if final_formula == 'EMA':
				average = calc_ema(final_ma[0], buy_prices[-1], buy_prices[-1-(final_ma[0])])
			elif final_formula == 'HMA':
				average = calc_hma(final_ma[0], buy_prices[-(final_ma[0]+int(math.sqrt(final_ma[0]))):-1])
			elif final_formula == 'WMA':
				average = calc_wma(final_ma[0], buy_prices[-(final_ma[0]):-1])

			if average < float(buy_prices[-1]) or reverse == True and average > float(buy_prices[-1]):
				if float(accounts[0]['available']) > 0:
					buy_sell_product("buy", final_cur, round(float(buy_prices[-1]), 2), (float(accounts[0]['available'])/float(buy_prices[-1])))

#_________________________________________________________________________
schedule.every().hour.at(":00").do(write_daily, token)
while True:
	schedule.run_pending()
	time.sleep(60)

#write_daily(token)

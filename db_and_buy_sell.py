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

from averages_list import averages, averages_names, averages_dict

""" To Do list:
find-moving-average:
find ways to speed up processes, multiprocessing???
Find if any value in periods, instead of hourly, such as 24h, and as of certain time 16:00 etc. is of best value

Throw in more formulas

db_buy_sell:
Need to fix where it breaks the buy/sell loop if m-a-h not found
"""

def readsettings():
	global minimum_periods, sell_stop, stop_percent, token
	with open('cjsettings.txt') as json_file:  
		data = json.load(json_file)[0]
		minimum_periods = int(data['minimum_periods'])
		token = data['token']
	if token == "":
		print ('No token found')
		exit()

def writesettings():
	global minimum_periods, sell_stop, stop_percent, token
	minimum_periods = 2016
	token = ""
	data = []
	data.append({
		'minimum_periods' : minimum_periods,
		'token': token
		})
	with open('cjsettings.txt', 'w') as outfile:  
		json.dump(data, outfile)
	print ('Please enter token into cjsettings.txt')
	exit()

try:
	readsettings()
except:
	writesettings()

headers = {'Content-Type': 'application/json; charset=utf-8', 'Authorization': 'Token token=%s' % token}

def buy_sell_product(BUY_SELL, ID, PRICE, SIZE):
	for prod in products:
		if prod['id'] == ID:
			for level in prod['price_levels']:
				if float(level['price_min']) < PRICE and float(level['price_max']) > PRICE:
					if SIZE > (float(level['trade_size'])):
						fixed_size = int(SIZE/float(level['trade_size']))*float(level['trade_size'])
						values = {"product_id": ID, "type": "LMT", "side": BUY_SELL, "price": str(PRICE), "size": str(fixed_size), "time_in_force": "GTC"}
						r = requests.post('https://api.exchange.coinjar.com/orders', data=json.dumps(values), headers=headers)
						if r.status_code == 200:
							print("Transaction OK", BUY_SELL, ID, PRICE)
							if BUY_SELL == 'buy':
								highest_amount = float(PRICE)
								last_buy = float(PRICE)
							elif BUY_SELL == 'sell':
								highest_amount = 0
							with open('Roof', 'wb') as handle:
								pickle.dump(highest_amount, handle)
							with open('Last', 'wb') as handle:
								pickle.dump(PRICE, handle)
						else:
							print("Some bogus error", r.reason)
							print(values)
					else:
						print ('Tried to %s, insufficient funds, minimum amount %s' % (BUY_SELL, level['trade_size']) )


#--------------------------------------

def write_daily(token_entry):
	global headers, products, highest_amount
	try:
		products = json.loads(urlopen(Request('https://api.exchange.coinjar.com/products', headers=headers)).read().decode('utf-8'))
		product_list = [i['id'] for i in products]
	except:
		db_buy = pd.read_pickle('db_buy-5min')
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
				db_buy = pd.read_pickle('db_buy-5min')
				db_sell = pd.read_pickle('db_sell-5min')
				buy_price = [x for x in db_buy.iloc[-1]]
				sell_price = [x for x in db_sell.iloc[-1]]
				success = True
	try:
		db_buy = pd.read_pickle('db_buy-5min')
		db_sell = pd.read_pickle('db_sell-5min')

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

	db_buy.to_pickle('db_buy-5min')
	db_sell.to_pickle('db_sell-5min')

#buy sell part
	try:
		with open('moving-averages-5min', 'rb') as handle:
			final_formula = pickle.load(handle)
			final_cur = pickle.load(handle)
			final_ma = pickle.load(handle)
			reverse = pickle.load(handle)
			floor_difference = pickle.load(handle)
			roof_difference = pickle.load(handle)
			print (final_cur, db_buy[final_cur].tail(1).index[0], db_buy[final_cur][-1])
	except:
		print ('Please run find_moving_averages first!')
		print (db_buy.tail(1))

		#Need to fix this where it breaks the buy/sell loop if m-a-h not found
	try:
		with open('Roof', 'rb') as handle:
			highest_amount = pickle.load(handle)
	except:
		highest_amount = 0

	try:
		with open('Last', 'rb') as handle:
			last_buy = pickle.load(handle)
	except:
		last_buy = 0

	buy_prices = [y for y in db_buy[final_cur]]
	sell_prices = [y for y in db_sell[final_cur]]
	accounts = json.loads(urlopen(Request('https://api.exchange.coinjar.com/accounts', headers=headers)).read().decode('utf-8'))
	today = False
	if len(buy_prices) > minimum_periods:
		#Moving floor stop/ceiling stop
		if float(sell_prices[-1]) > highest_amount:
			highest_amount = float(sell_prices[-1])
			print ('Floor set to ', highest_amount - floor_difference)
			with open('Roof', 'wb') as handle:
				pickle.dump(highest_amount, handle)

		#Sell part
		if float(sell_prices[-1]) < (highest_amount - floor_difference) or float(sell_prices[-1]) >= (last_buy + roof_difference):
			for X in range(len(accounts)):
				if accounts[X]['asset_code'] != 'AUD' and accounts[X]['asset_code'] in final_cur:
					ASSET = X
			if float(accounts[ASSET]['available']) > 0:
				buy_sell_product("sell", final_cur, float(sell_prices[-1]), float(accounts[ASSET]['available']))
				today = True
				
		#Buy part
		if today != True:
			average = averages_dict[final_formula](final_ma, buy_prices[-(final_ma+int(math.sqrt(final_ma))):])
			if average < float(buy_prices[-1]) or reverse == True and average > float(buy_prices[-1]):
				if float(accounts[0]['available']) > 0:
					buy_sell_product("buy", final_cur, round(float(buy_prices[-1]), 2), (float(accounts[0]['available'])/float(buy_prices[-1])))

#_________________________________________________________________________
schedule.every().hour.at(":00").do(write_daily, token)
schedule.every().hour.at(":05").do(write_daily, token)
schedule.every().hour.at(":10").do(write_daily, token)
schedule.every().hour.at(":15").do(write_daily, token)
schedule.every().hour.at(":20").do(write_daily, token)
schedule.every().hour.at(":25").do(write_daily, token)
schedule.every().hour.at(":30").do(write_daily, token)
schedule.every().hour.at(":35").do(write_daily, token)
schedule.every().hour.at(":40").do(write_daily, token)
schedule.every().hour.at(":45").do(write_daily, token)
schedule.every().hour.at(":50").do(write_daily, token)
schedule.every().hour.at(":55").do(write_daily, token)
while True:
	schedule.run_pending()
	time.sleep(30)

#write_daily(token)

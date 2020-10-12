import json
import requests
import urllib
from urllib.request import Request, urlopen
import time
import datetime
import pandas as pd
import pickle
import schedule

main_currency = 'BTCAUD'

def check_products():
	global product_list
	try:
		products = json.loads(urlopen(Request('https://api.exchange.coinjar.com/products')).read().decode('utf-8'))
		product_list = [i['id'] for i in products]
	except:
		try:
			product_list
		except NameError:
			db_buy = pd.read_pickle('database/db_buy')
			product_list = [x for x in db_buy]

def db_entry():
	global db_buy, db_sell
	retries = 1
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
				buy_price = [x for x in db_buy.iloc[-1]]
				sell_price = [x for x in db_sell.iloc[-1]]
				success = True
	new_row = pd.DataFrame(buy_price).transpose()
	new_row.columns = product_list
	new_row.rename(index={0 : str(datetime.datetime.now())}, inplace=True)
	db_buy = db_buy.append(new_row, sort=True)

	new_row = pd.DataFrame(sell_price).transpose()
	new_row.columns = product_list
	new_row.rename(index={0 : str(datetime.datetime.now())}, inplace=True)
	db_sell = db_sell.append(new_row, sort=True)

	print (main_currency, db_buy[main_currency].tail(1).index[0], db_buy[main_currency][-1])
	db_buy.to_pickle('database/db_buy')
	db_sell.to_pickle('database/db_sell')

print ('DB entry started')

check_products()

try:
	db_buy = pd.read_pickle('database/db_buy')
	db_sell = pd.read_pickle('database/db_sell')
except:
	db_buy = db_sell = pd.DataFrame(columns = product_list)

schedule.every().hour.at(":03").do(check_products)
schedule.every().hour.at(":00").do(db_entry)
schedule.every().hour.at(":05").do(db_entry)
schedule.every().hour.at(":10").do(db_entry)
schedule.every().hour.at(":15").do(db_entry)
schedule.every().hour.at(":20").do(db_entry)
schedule.every().hour.at(":25").do(db_entry)
schedule.every().hour.at(":30").do(db_entry)
schedule.every().hour.at(":35").do(db_entry)
schedule.every().hour.at(":40").do(db_entry)
schedule.every().hour.at(":45").do(db_entry)
schedule.every().hour.at(":50").do(db_entry)
schedule.every().hour.at(":55").do(db_entry)
while True:
	schedule.run_pending()
	time.sleep(30)
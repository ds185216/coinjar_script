import json
import time
import datetime
import pandas as pd
import pickle
import itertools
from itertools import *
import math

from averages_list import averages, averages_names, averages_dict

print ("Grab a coffee, this may take a while...")

buy = pd.read_pickle('db_buy-5min')
sell = pd.read_pickle('db_sell-5min')

print ('Database size:', len(buy), 'entries')

if len(buy) > 2688:
	sample_buy = buy.head(2016)
	sample_sell = sell.head(2016)
	test_buy = buy.tail(len(buy)-2016)
	test_sell = buy.tail(len(sell)-2016)
else:
	sample_buy = buy.head(int(len(buy)/2))
	sample_sell = sell.head((int(len(sell)/2)))
	test_buy = buy.tail(int(len(buy)/2))
	test_sell = sell.tail(int(len(sell)/2))

#play with sample sizes, this can help with speeding up the process



def find_averages(db_buy, db_sell):
	global result
	result = []

	currencies = [i for i in db_buy.columns if 'AUD' in i]
	for calc in range(len(averages)):
		for CUR in currencies:
			buy_prices = [y for y in db_buy[CUR]]
			sell_prices = [y for y in db_sell[CUR]]	
			increments = []
			for x in range(1, len(sell_prices)):
				diff = float(sell_prices[x]) - float(sell_prices[x-1])
				if diff < 0:
					diff = abs(diff)
				if diff != 0:
					increments.append(diff)
			inc = min(increments)
			for reverse in [True, False]:
				for test_ma in range(2, 72):
					for diff in range(1, 60):
						cash = 1000.00
						crypto = 0
						highest_amount = 0
						shift = 0
						for i in range(len(buy_prices)):
							today = False
							if float(sell_prices[i]) > highest_amount:
								highest_amount = float(sell_prices[i])
							if crypto > 0:
								if float(sell_prices[i]) < highest_amount - (diff * inc) and cash == 0:
									#test sell
									cash = cash + round(crypto * float(sell_prices[i]))
									crypto= 0
									today = True
									highest_amount = 0
									shift +=1
							if i >= test_ma+int(math.sqrt(test_ma)) and today != True and cash > 0:
								average = averages[calc](test_ma, buy_prices[(i-(test_ma+int(math.sqrt(test_ma)))):i])
								if average < float(buy_prices[i]) or reverse == True and average > float(buy_prices[i]) and crypto == 0:
									#test buy
									crypto = crypto + (round(cash) / float(buy_prices[i]))
									cash = 0
									highest_amount = float(buy_prices[i])
									shift +=1
						if crypto != 0:
							cash = cash + round(crypto * float(sell_prices[i]))
						if cash > 1000 and shift > len(db_buy)/288:
							result.append({'name' : averages_names[calc],
								'test_ma' : test_ma,
								'name' : averages_names[calc],
								'CUR' : CUR,
								'reverse' : reverse,
								'differential' : diff*inc})
	print (len(result), 'profitable formulas found')


def test_averages(db_buy, db_sell, data):
	overall_cash = 0
	for line in data:
		test_ma = line['test_ma']
		MA = line['name']
		CUR = line['CUR']
		reverse = line['reverse']
		diff = line['differential']

		buy_prices = [y for y in db_buy[CUR]]
		sell_prices = [y for y in db_sell[CUR]]
		cash = 1000.00
		crypto = 0
		highest_amount = 0
		for i in range(len(buy_prices)):
			today = False
			if float(sell_prices[i]) > highest_amount:
				highest_amount = float(sell_prices[i])
			if crypto > 0:
				if float(sell_prices[i]) < highest_amount - (diff) and cash == 0:
					#test sell
					cash = cash + round(crypto * float(sell_prices[i]))
					crypto= 0
					today = True
					highest_amount = 0
			if i >= test_ma+int(math.sqrt(test_ma)) and today != True and cash > 0:
				average = averages_dict[MA](test_ma, buy_prices[(i-(test_ma+int(math.sqrt(test_ma)))):i])
				if average < float(buy_prices[i]) or reverse == True and average > float(buy_prices[i]) and crypto == 0:
					#test buy
					crypto = crypto + (round(cash) / float(buy_prices[i]))
					cash = 0
					highest_amount = float(buy_prices[i])
		if crypto != 0:
			cash = cash + round(crypto * float(sell_prices[i]))
		if cash > overall_cash:
			overall_cash = cash
			overall_formula = MA
			overall_cur = CUR
			overall_moving_average = test_ma
			overall_reverse = reverse
			overall_difference = diff
	print (overall_cash, overall_formula, overall_moving_average, overall_cur, overall_reverse, overall_difference)
	if overall_cash > 1000:
		with open('moving-averages-5min', 'wb') as handle:
			pickle.dump(overall_formula, handle)
			pickle.dump(overall_cur, handle)
			pickle.dump(overall_moving_average, handle)
			pickle.dump(overall_reverse, handle)
			pickle.dump(overall_difference, handle)
	else:
		print ('Not profitable, no data written')



find_averages(sample_buy, sample_sell)

if len(result) > 0:
	test_averages(test_buy, test_sell, result)
else:
	print ('No formulas found')
"""
		with open('moving-averages-5min', 'wb') as handle:
			pickle.dump(overall_formula, handle)
			pickle.dump(overall_cur, handle)
			pickle.dump(overall_moving_average, handle)
			pickle.dump(overall_reverse, handle)
			pickle.dump(overall_difference, handle)"""
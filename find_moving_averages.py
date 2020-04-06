import json
import time
import datetime
import pandas as pd
import pickle
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

db_buy = pd.read_pickle('db_buy-hourly')
db_sell = pd.read_pickle('db_sell-hourly')
currencies = [i for i in db_buy.columns if 'AUD' in i]


overall_moving_average = [0,0]
overall_cash = 0
overall_cur = ""
overall_reverse = True


#Exponential Moving Average
ema_range = list(itertools.product(range(2, 168), repeat=2))
final_ema = [0,0]
final_cash = 0
final_cur = ""
for reverse in [True, False]:
	for CUR in currencies:
		buy_prices = [y for y in db_buy[CUR]]
		sell_prices = [y for y in db_sell[CUR]]
		for test_EMA in ema_range:
			cash = 1000.00
			crypto = 0
			for i in range(len(buy_prices)):
				today = False
				if i >= test_EMA[1]:
					average = calc_ema(test_EMA[1], sell_prices[i], sell_prices[i-(test_EMA[1])])
					if average > float(sell_prices[i]) or reverse == True and average < float(sell_prices[i]):
						#test sell
						cash = cash + round(crypto * float(sell_prices[i]))
						crypto= 0
						today = True
				if i >= test_EMA[0] and today != True:
					average = calc_ema(test_EMA[0], buy_prices[i], buy_prices[i-(test_EMA[0])])
					if average < float(buy_prices[i]) or reverse == True and average > float(buy_prices[i]):
						#test buy
						crypto = crypto + (round(cash) / float(buy_prices[i]))
						cash = 0
			if crypto != 0:
				cash = cash + round(crypto * float(sell_prices[i]))
			if cash > final_cash:
				final_cash = cash
				final_ema = test_EMA
				final_cur = CUR
				final_reverse = reverse
print ('EMA',final_cur, final_ema, final_cash-1000)/(len(db_buy), final_reverse)
if final_cash > overall_cash:
	overall_cash = final_cash
	overall_formula = 'EMA'
	overall_cur = final_cur
	overall_moving_average = final_ema
	overall_reverse = final_reverse


#Weighted Moving Average
wma_range = list(itertools.product(range(2, 168), repeat=2))
final_wma = [0,0]
final_cash = 0
final_cur = ""
for reverse in [True, False]:
	for CUR in currencies:
		buy_prices = [y for y in db_buy[CUR]]
		sell_prices = [y for y in db_sell[CUR]]
		for test_wma in wma_range:
			cash = 1000.00
			crypto = 0
			for i in range(len(buy_prices)):
				today = False
				if i >= test_wma[1]:
					average = calc_wma(test_wma[1], sell_prices[i-test_wma[1]:i])
					if average > float(sell_prices[i]) or reverse == True and average < float(sell_prices[i]):
						#test sell
						cash = cash + round(crypto * float(sell_prices[i]))
						crypto= 0
						today = True
				if i >= test_wma[0] and today != True:
					average = calc_wma(test_wma[0], buy_prices[i-test_wma[0]:i])
					if average < float(buy_prices[i]) or reverse == True and average > float(buy_prices[i]):
						#test buy
						crypto = crypto + (round(cash) / float(buy_prices[i]))
						cash = 0
			if crypto != 0:
				cash = cash + round(crypto * float(sell_prices[i]))
			if cash > final_cash:
				final_cash = cash
				final_wma = test_wma
				final_cur = CUR
				final_reverse = reverse
print ('WMA',final_cur, final_wma, final_cash-1000)/(len(db_buy), final_reverse)
if final_cash > overall_cash:
	overall_cash = final_cash
	overall_formula = 'WMA'
	overall_cur = final_cur
	overall_moving_average = final_wma
	overall_reverse = final_reverse


#Hull Moving Average
hma_range = list(itertools.product(range(4, 168), repeat=2))
final_hma = [0,0]
final_cash = 0
final_cur = ""
for reverse in [True, False]:
	for CUR in currencies:
		buy_prices = [y for y in db_buy[CUR]]
		sell_prices = [y for y in db_sell[CUR]]
		for test_hma in hma_range:
			cash = 1000.00
			crypto = 0
			for i in range(len(buy_prices)):
				today = False
				if i >= (test_hma[1]+math.sqrt(test_hma[1])):
					average = calc_hma(test_hma[1], sell_prices[(i-(test_hma[1]+int(math.sqrt(test_hma[1])))):i])
					if average > float(sell_prices[i]) or reverse == True and average < float(sell_prices[i]):
						#test sell
						cash = cash + round(crypto * float(sell_prices[i]))
						crypto= 0
						today = True
				if i >= (test_hma[0]+math.sqrt(test_hma[0])) and today != True:
					average = calc_hma(test_hma[0], buy_prices[(i-(test_hma[0]+int(math.sqrt(test_hma[0])))):i])
					if average < float(buy_prices[i]) or reverse == True and average > float(buy_prices[i]):
						#test buy
						crypto = crypto + (round(cash) / float(buy_prices[i]))
						cash = 0
			if crypto != 0:
				cash = cash + round(crypto * float(sell_prices[i]))
			if cash > final_cash:
				final_cash = cash
				final_hma = test_hma
				final_cur = CUR
				final_reverse = reverse
print ('HMA',final_cur, final_hma, final_cash-1000)/(len(db_buy), final_reverse)
if final_cash > overall_cash:
	overall_cash = final_cash
	overall_formula = 'HMA'
	overall_cur = final_cur
	overall_moving_average = final_hma
	overall_reverse = final_reverse




#write to file
with open('moving-averages-hourly', 'wb') as handle:
	pickle.dump(overall_formula, handle)
	pickle.dump(overall_cur, handle)
	pickle.dump(overall_moving_average, handle)
	pickle.dump(overall_reverse, handle)
import json
import time
import datetime
import pandas as pd
import pickle
import itertools
from itertools import *
import math

print ("This may take a few days....")
print ("I will work on finding ways to make this faster")

#Need to fix highest amount to work only after confirmed buy, if it changes after attempted buy it will mess the highest price to only what its set to

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
		new_list.append(2 * calc_wma(half_length, _data[-(i+half_length):-i]) - calc_wma(num, _data[-(i+num):-i]))
	return calc_wma(sqrt_length, new_list)

def find_averages():
	db_buy = pd.read_pickle('db_buy-hourly')
	db_sell = pd.read_pickle('db_sell-hourly')
	currencies = [i for i in db_buy.columns if 'AUD' in i]

	overall_moving_average = 0
	overall_cash = 0
	overall_cur = ""
	overall_reverse = True
	overall_differential = 0

	#Exponential Moving Average
	final_ema = 0
	final_cash = 0
	final_cur = ""
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
			for test_EMA in range(2, 168):
				for diff in range(1, 50):
					cash = 1000.00
					crypto = 0
					highest_amount = 0
					for i in range(len(buy_prices)):
						today = False
						if float(sell_prices[i]) > highest_amount:
							highest_amount = float(sell_prices[i])
						if crypto > 0:
							if float(sell_prices[i]) < highest_amount - (diff * inc):
								#test sell
								cash = cash + round(crypto * float(sell_prices[i]))
								crypto= 0
								today = True
								highest_amount = 0
						if i >= test_EMA and today != True and cash > 0:
							average = calc_ema(test_EMA, buy_prices[i], buy_prices[i-(test_EMA)])
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
						final_difference = diff * inc
	print ('EMA',final_cur, final_ema, (final_cash-1000)/len(db_buy), final_reverse)
	if final_cash > overall_cash:
		overall_cash = final_cash
		overall_formula = 'EMA'
		overall_cur = final_cur
		overall_moving_average = final_ema
		overall_reverse = final_reverse
		overall_difference = final_difference
		with open('moving-averages-hourly', 'wb') as handle:
			pickle.dump(overall_formula, handle)
			pickle.dump(overall_cur, handle)
			pickle.dump(overall_moving_average, handle)
			pickle.dump(overall_reverse, handle)
			pickle.dump(overall_difference, handle)

	#Weighted Moving Average
	final_wma = 0
	final_cash = 0
	final_cur = ""
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
			for test_wma in range(2, 168):
				for diff in range(1, 50):
					cash = 1000.00
					crypto = 0
					highest_amount = 0
					for i in range(len(buy_prices)):
						today = False
						if float(sell_prices[i]) > highest_amount:
							highest_amount = float(sell_prices[i])
						if crypto > 0:
							if float(sell_prices[i]) < highest_amount - (diff * inc):
								#test sell
								cash = cash + round(crypto * float(sell_prices[i]))
								crypto= 0
								today = True
								highest_amount = 0
						if i >= test_wma and today != True and cash > 0:
							average = calc_wma(test_wma, buy_prices[i-test_wma:i])
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
						final_difference = diff * inc
	print ('WMA',final_cur, final_wma, (final_cash-1000)/len(db_buy), final_reverse)
	if final_cash > overall_cash:
		overall_cash = final_cash
		overall_formula = 'WMA'
		overall_cur = final_cur
		overall_moving_average = final_wma
		overall_reverse = final_reverse
		overall_difference = final_difference
		with open('moving-averages-hourly', 'wb') as handle:
			pickle.dump(overall_formula, handle)
			pickle.dump(overall_cur, handle)
			pickle.dump(overall_moving_average, handle)
			pickle.dump(overall_reverse, handle)
			pickle.dump(overall_difference, handle)

	#Hull Moving Average
	final_hma = 0
	final_cash = 0
	final_cur = ""
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
			for test_hma in range(4, 168):
				for diff in range(1, 50):
					cash = 1000.00
					crypto = 0
					highest_amount = 0
					for i in range(len(buy_prices)):
						today = False
						if float(sell_prices[i]) > highest_amount:
							highest_amount = float(sell_prices[i])
						if crypto > 0:
							if float(sell_prices[i]) < highest_amount - (diff * inc):
								#test sell
								cash = cash + round(crypto * float(sell_prices[i]))
								crypto= 0
								today = True
								highest_amount = 0
						if i >= test_hma and today != True and cash > 0:
							average = calc_hma(test_hma, buy_prices[(i-(test_hma+int(math.sqrt(test_hma)))):i])
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
						final_difference = diff * inc
	print ('HMA',final_cur, final_hma, (final_cash-1000)/len(db_buy), final_reverse)
	if final_cash > overall_cash:
		overall_cash = final_cash
		overall_formula = 'HMA'
		overall_cur = final_cur
		overall_moving_average = final_hma
		overall_reverse = final_reverse
		overall_difference = final_difference
		with open('moving-averages-hourly', 'wb') as handle:
			pickle.dump(overall_formula, handle)
			pickle.dump(overall_cur, handle)
			pickle.dump(overall_moving_average, handle)
			pickle.dump(overall_reverse, handle)
			pickle.dump(overall_difference, handle)
find_averages()
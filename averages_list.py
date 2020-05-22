import math

def calc_ema(num, _data):
	_data = _data[-num:]
	k = 2/(num+1)
	EMA = float(_data[-1])*k+float(_data[0])*(1-k)
	return EMA

def calc_wma(num, _data):
	_data = _data[-num:]
	first_sum = 0
	for i in range(1, num+1):
		first_sum = first_sum + (float(_data[-i]) * i)
	return first_sum/sum(range(1, num+1))

def calc_hma(num, _data):
	half_length = int(num/2)
	sqrt_length = int(math.sqrt(num))
	new_list = []
	for i in range(1, sqrt_length+1):
		new_list.append(2 * calc_wma(half_length, _data[-(i+half_length):-i]) - calc_wma(num, _data[-(i+num):-i]))
	return calc_wma(sqrt_length, new_list)

averages = [calc_ema, calc_wma, calc_hma]
averages_names = ['EMA', 'WMA', 'HMA']
averages_dict = {'EMA' : calc_ema, 'WMA': calc_wma, 'HMA' : calc_hma}
#averages_dict = ['EMA' : calc_ema, 'WMA' : calc_wma, 'HMA' : calc_hma]
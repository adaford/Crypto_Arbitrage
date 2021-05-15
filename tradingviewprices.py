from tradingview_ta import TA_Handler, Interval, Exchange
from collections import Counter
import sys


EC2_mode = True
if len(sys.argv) > 1:
	EC2_mode = False

COIN_LIST_PATH = '/home/ec2-user/script/coin_list.txt' if EC2_mode else 'coin_list.txt'
EXCHANGE_LIST_PATH = '/home/ec2-user/script/exchange_list.txt' if EC2_mode else 'exchange_list.txt'
PRICE_ALERT_PERCENTAGE = .08 if EC2_mode else int(sys.argv[1]) / 100

coins, exchanges, alerted_coins, printout = [], [], [], []


with open(COIN_LIST_PATH) as c:
	coins = c.read().splitlines()
with open(EXCHANGE_LIST_PATH) as e:
	exchanges = e.read().splitlines()

for coin in coins:
	coin_prices = {}
	for exchange in exchanges:
		coin_found = False
		handler = TA_Handler()
		handler.set_symbol_as(coin)
		handler.set_exchange_as_crypto_or_stock(exchange)
		handler.set_screener_as_crypto()
		handler.set_interval_as(Interval.INTERVAL_1_MINUTE)
		try:
			analysis = handler.get_analysis()
			coin_found = True
		except:
			pass

		handler.set_symbol_as(coin + 'T')	
		try:
			analysis = handler.get_analysis()
			coin_found = True
		except:
			pass

		if coin_found:
			coin_prices[(coin,exchange)] = analysis.indicators['open']

	for c,v in coin_prices.items():
		for c2,v2 in coin_prices.items():
			#print(c,c2,v,v2)
			if abs(v-v2) / min(v,v2) > PRICE_ALERT_PERCENTAGE:
				if [c2,c,float(v2),float(v)] not in alerted_coins:
					alerted_coins.append([c,c2,float(v),float(v2)])

#print(analysis.indicators)

for a in alerted_coins:
	printout.append([a[0][0], int(abs(100*(a[3]-a[2])) / min(a[3],a[2])), a[0][1], a[1][1],a[2],a[3]])
printout.sort(key=lambda x: (x[0],x[1]), reverse=True)
c = Counter()
count = 0
for a in printout:
	a[1] = str(a[1]) + '%'
	c[a[0]] += 1
	if c[a[0]] < 3:
		print(a)
		count += 1

if count == 0:
	print([0,0,0,0])

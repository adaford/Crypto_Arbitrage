from tradingview_ta import TA_Handler, Interval, Exchange
from collections import Counter


PRICE_ALERT_PERCENTAGE = .08
coins, exchanges, alerted_coins, printout = [], [], [], []

with open('coin_list.txt') as c:
	coins = c.read().splitlines()
with open('exchange_list.txt') as e:
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
			coin_prices[(coin,exchange)] = analysis.indicators['BB.upper']


	for c,v in coin_prices.items():
		for c2,v2 in coin_prices.items():
			#print(c,c2,v,v2)
			if abs(v-v2) / min(v,v2) > PRICE_ALERT_PERCENTAGE:
				if [c2,c,float(v2),float(v)] not in alerted_coins:
					alerted_coins.append([c,c2,float(v),float(v2)])

for a in alerted_coins:
	printout.append([int(abs(100*(a[3]-a[2])) / min(a[3],a[2])), a[0][0], a[0][1], a[1][1]])
printout.sort(key=lambda x: (x[1],x[0]), reverse=True)
c = Counter()
for a in printout:
	a[0] = str(a[0]) + '%'
	c[a[1]] += 1
	if c[a[1]] < 3:
		print(a)

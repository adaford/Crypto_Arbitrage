from tradingview_ta import TA_Handler, Interval, Exchange
from collections import Counter
import sys


EC2_mode = True
if len(sys.argv) > 1:
	EC2_mode = False

COIN_LIST_PATH = '/home/ec2-user/script/coin_list.txt' if EC2_mode else 'coin_list.txt'
EXCHANGE_LIST_PATH = '/home/ec2-user/script/exchange_list.txt' if EC2_mode else 'exchange_list.txt'
PRICE_ALERT_PERCENTAGE = .08 if EC2_mode else float(sys.argv[1]) / 100

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
		handler.set_symbol_as(coin + "USD")
		handler.set_exchange_as_crypto_or_stock(exchange)
		handler.set_screener_as_crypto()
		handler.set_interval_as(Interval.INTERVAL_1_MINUTE)
		try:
			analysis = handler.get_analysis()
			coin_found = True
		except:
			handler.set_symbol_as(coin + 'USDT')	
			try:
				analysis = handler.get_analysis()
				coin_found = True
			except:
				pass

		if coin_found:
			coin_prices[(coin,exchange)] = float(analysis.indicators['open'])


	for c,v in coin_prices.items():
		for c2,v2 in coin_prices.items():
			#print(c,c2,v,v2)
			if abs(v-v2) / max(v,v2) > PRICE_ALERT_PERCENTAGE:
				if [c2,c,v2,v] not in alerted_coins:
					alerted_coins.append([c,c2,v,v2])



for a in alerted_coins:
	printout.append([a[0][0], str(round(float(abs(100*(a[3]-a[2]))) / max(a[3],a[2]),2))+'%', a[0][1], a[1][1],a[2],a[3]])
printout.sort(key=lambda x: (x[1],x[0]), reverse=True)

if len(printout) > 0:
	for a in printout:
		print(a)
else:
	print([0,0,0,0])

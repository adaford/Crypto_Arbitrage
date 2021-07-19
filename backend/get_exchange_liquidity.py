import requests
import sys
from requests import Request, Session
from requests.exceptions import ConnectionError, Timeout, TooManyRedirects
import json


PERCENT_BUFFER = 1.005  # .5% margin on market_value

def get_kraken_liquidity(coin,overvalued,market_value):
	try:
		resp = requests.get("https://api.kraken.com/0/public/Depth?pair={}USD".format(coin)).json()['result']
		liquidity = 0	

		if overvalued:
			bids = resp[list(resp.keys())[0]]['bids']
			for b in bids:
				if float(b[0]) <= market_value * PERCENT_BUFFER:
					return int(liquidity)
				liquidity += float(b[0]) * float(b[1])
				
		else:
			asks = resp[list(resp.keys())[0]]['asks']
			for a in asks:
				if float(a[0]) * PERCENT_BUFFER >= market_value:
					return int(liquidity)
				liquidity += float(a[0]) * float(a[1])
				
		return int(liquidity)
	except:
		return "Unknown"


def get_coinbasepro_liquidity(coin,overvalued,market_value):
	try:
		resp = requests.get("https://api.pro.coinbase.com/products/{}-USD/book?level=2".format(coin)).json()
		liquidity = 0

		if overvalued:
			bids = resp['bids']
			for b in bids:
				if float(b[0]) <= market_value * PERCENT_BUFFER:
					return int(liquidity)
				liquidity += float(b[0]) * float(b[1])
				
		else:
			asks = resp['asks']
			for a in asks:
				if float(a[0]) * PERCENT_BUFFER >= market_value:
					return int(liquidity)
				liquidity += float(a[0]) * float(a[1])
				
		return int(liquidity)
	except:
		return "Unknown"


def get_binanceUS_liquidity(coin,overvalued,market_value):
	return "Unknown"


def get_kucoin_liquidity(coin,overvalued,market_value):
	try:
		resp = requests.get("https://api.kucoin.com/api/v1/market/orderbook/level2_100?symbol={}-USDT".format(coin)).json()
		liquidity = 0

		if overvalued:
			bids = resp['data']['bids']
			for b in bids:
				if float(b[0]) <= market_value * PERCENT_BUFFER:
					return int(liquidity)
				liquidity += float(b[0]) * float(b[1])
		else:
			asks = resp['data']['asks']
			for a in asks:
				if float(a[0]) * PERCENT_BUFFER >= market_value:
					return int(liquidity)
				liquidity += float(a[0]) * float(a[1])
				
		return int(liquidity)
	except:
		return "Unknown"


def get_gemini_liquidity(coin,overvalued,market_value):
	try:
		resp = requests.get("https://api.gemini.com/v1//book/{}usd".format(coin.lower())).json()
		liquidity = 0
		if overvalued:
			bids = resp['bids']
			for b in bids:
				if float(b['price']) <= market_value * PERCENT_BUFFER:
					return int(liquidity)
				liquidity += float(b['price']) * float(b['amount'])
		else:
			asks = resp['asks']
			#print(asks)
			for a in asks:
				if float(a['price']) * PERCENT_BUFFER >= market_value:
					return int(liquidity)
				liquidity += float(a['price']) * float(a['amount'])

		return int(liquidity)
	except:
		return "Unknown"


def get_bittrex_liquidity(coin,overvalued,market_value):
	try:
		resp = requests.get("https://api.bittrex.com/v3/markets/{}-USD/orderbook".format(coin)).json()
		if resp[list(resp.keys())[0]] == 'MARKET_DOES_NOT_EXIST':
			resp = requests.get("https://api.bittrex.com/v3/markets/{}-USDT/orderbook".format(coin)).json()
		liquidity = 0
		if overvalued:
			bids = resp['bid']
			for b in bids:
				if float(b['rate']) <= market_value * PERCENT_BUFFER:
					return int(liquidity)
				liquidity += float(b['rate']) * float(b['quantity'])
				
		else:
			asks = resp['ask']
			for a in asks:
				if float(a['rate']) * PERCENT_BUFFER >= market_value:
					return int(liquidity)
				liquidity += float(a['rate']) * float(a['quantity'])
		return int(liquidity)
	except:
		return "Unknown"

#print(get_kraken_liquidity("REP",True,1))
#print(get_coinbasepro_liquidity("KNC",True,1.50))
#print(get_binanceUS_liquidity("KNC",True,2.30))
#print(get_kucoin_liquidity("BTC",False,42000))
#print(get_gemini_liquidity("KNC",True,1.50))
#print(get_bittrex_liquidity("MKR",True,1))



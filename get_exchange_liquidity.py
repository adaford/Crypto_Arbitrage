import requests
import sys
from requests import Request, Session
from requests.exceptions import ConnectionError, Timeout, TooManyRedirects
import json


def get_kraken_liquidity(coin,overvalued,market_value):
	try:
		resp = requests.get("https://api.kraken.com/0/public/Depth?pair={}USD".format(coin)).json()
		liquidity = 0
		asks = resp['result']['{}USD'.format(coin)]['asks']
		bids = resp['result']['{}USD'.format(coin)]['bids']
		if overvalued:
			bids = resp['result']['{}USD'.format(coin)]['bids']
			for b in bids:
				liquidity += float(b[0]) * float(b[1])
				if float(b[0]) <= market_value:
					return int(liquidity)
		else:
			asks = resp['result']['{}USD'.format(coin)]['asks']
			for a in asks:
				liquidity += float(a[0]) * float(a[1])
				if float(a[0]) >= market_value:
					return int(liquidity)

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
				liquidity += float(b[0]) * float(b[1])
				if float(b[0]) <= market_value:
					return int(liquidity)
		else:
			asks = resp['asks']
			for a in asks:
				liquidity += float(a[0]) * float(a[1])
				if float(a[0]) >= market_value:
					return int(liquidity)

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
				liquidity += float(b[0]) * float(b[1])
				if float(b[0]) <= market_value:
					return int(liquidity)
		else:
			asks = resp['data']['asks']
			for a in asks:
				liquidity += float(a[0]) * float(a[1])
				if float(a[0]) >= market_value:
					return int(liquidity)

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
				liquidity += float(b['price']) * float(b['amount'])
				if float(b['price']) <= market_value:
					return int(liquidity)
		else:
			asks = resp['asks']
			for a in asks:
				liquidity += float(a['price']) * float(a['amount'])
				if float(a['price']) >= market_value:
					return int(liquidity)

		return int(liquidity)
	except:
		return "Unknown"


def get_bittrex_liquidity(coin,overvalued,market_value):
	try:
		resp = 0
		try:
			resp = requests.get("https://api.bittrex.com/v3/markets/{}-USD/orderbook".format(coin)).json()
		except:
			resp = requests.get("https://api.bittrex.com/v3/markets/{}-USDT/orderbook".format(coin)).json()
		liquidity = 0
		if overvalued:
			bids = resp['bid']
			for b in bids:
				liquidity += float(b['rate']) * float(b['quantity'])
				if float(b['rate']) <= market_value:
					return int(liquidity)
		else:
			asks = resp['ask']
			for a in asks:
				liquidity += float(a['rate']) * float(a['quantity'])
				if float(a['rate']) >= market_value:
					return int(liquidity)

		return int(liquidity)
	except:
		return "Unknown"

#print(get_kraken_liquidity("KNC",True,2.35))
#print(get_coinbasepro_liquidity("KNC",True,2.30))
#print(get_binanceUS_liquidity("KNC",True,2.30))
#print(get_kucoin_liquidity("BTC",False,42000))
#print(get_gemini_liquidity("KNC",True,2.438))
#print(get_bittrex_liquidity("BTC",False,40000))



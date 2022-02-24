import requests
import sys
from requests import Request, Session
from requests.exceptions import ConnectionError, Timeout, TooManyRedirects
import json


PERCENT_BUFFER = 1.01  # 1% margin on market_value

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
		resp = requests.get("https://api.gemini.com/v1/book/{}usd".format(coin.lower())).json()
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


def get_cryptodotcom_liquidity(coin,overvalued,market_value):
	coin = coin + '_USDT'
	try:
		resp = requests.get('https://api.crypto.com/v2/public/get-book?instrument_name={}&depth=150'.format(coin)).json()
	except:
		resp = requests.get('https://api.crypto.com/v2/public/get-book?instrument_name={}&depth=150'.format(coin.replace("USDT","USDC"))).json()
	try:
		resp = resp["result"]["data"][0]
		liquidity = 0
		if overvalued:
			bids = resp['bids']
			for b in bids:
				if float(b[0]) <= market_value * PERCENT_BUFFER:
					return int(liquidity)
				liquidity += float(b[0]) * float(b[1]) * float(b[2])
				
		else:
			asks = resp['asks']
			for a in asks:
				if float(a[0]) * PERCENT_BUFFER >= market_value:
					return int(liquidity)
				liquidity += float(a[0]) * float(a[1]) * float(a[2])
		return int(liquidity)
	except:
		return "Unknown"

"""def get_lbank_liquidity(coin,overvalued,market_value):
	headers = {
	"contentType": "application/x-www-form-urlencoded"
	}
	try:
		resp = requests.get("https://api.lbkex.com/v1/depth.do?symbol=eth-usdt?size=30?merge=0", headers=headers).json()
		print(resp)
		exit(0)
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
"""
def get_gateio_liquidity(coin,overvalued,market_value):
	coin = coin + '_USDT'

	host = "https://api.gateio.ws"
	prefix = "/api/v4"
	headers = {'Accept': 'application/json', 'Content-Type': 'application/json'}
	url = '/spot/order_book'
	query_param = 'currency_pair={}&limit=100'.format(coin)

	resp = requests.request('GET', host + prefix + url + "?" + query_param, headers=headers).json()

	try:
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


def get_ftx_liquidity(coin,overvalued,market_value):
	try:
		resp = requests.get('https://ftx.com/api/markets/{}/orderbook?depth=100'.format(coin+'/USD')).json()['result']
	except:
		try:
			resp = requests.get('https://ftx.com/api/markets/{}/orderbook?depth=100'.format(coin+'/USDT')).json()['result']
		except:
			return "Unknown"

	try:
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


#print(get_kraken_liquidity("REP",True,1))
#print(get_coinbasepro_liquidity("KNC",True,1.50))
#print(get_binanceUS_liquidity("KNC",True,2.30))
#print(get_kucoin_liquidity("BZRX",True,.2436))
#print(get_gemini_liquidity("NMR",True,30.5))
#print(get_bittrex_liquidity("MKR",True,1))
#print(get_cryptodotcom_liquidity("BTC", False, 70000))
#get_lbank_liquidity('BTC', False, 70000)
#print(get_gateio_liquidity('POLY',False,.8))
#print(get_ftx_liquidity("BTC",True,33000))
import requests
import math
import time
import json
import base64
import hmac
import hashlib
import sys
import SMS
import annoying_coins
import traceback
from threading import Thread



class ExchangeRequest:
	percent_buffer = 1.01


	@classmethod
	def get_exchange(cls):
		return cls.__name__.split("Request")[0]


	@classmethod
	def get_coin_price(cls,coin):
		for i in range(3):
			try:
				return cls.get_request_coin_price(coin)
			except:
				pass
		return -1


	def get_coin_prices(coins):
		return coins


	@classmethod
	def get_all_prices(cls):
		try:
			all_coins = cls.get_coin_list()
			coins = cls.remove_unwanted_coins(all_coins)
			return cls.get_coin_prices(coins)
		except BaseException as err:
			print(err)
			print(traceback.format_exc())
			print("cannot find coinlist on {}".format(cls.get_exchange()))
			return 0
		

	@classmethod
	def process_range(cls, id_range, store=None):
	    """process a number of ids, storing the results in a dict"""
	    if store is None:
	        store = {}
	    for id in id_range:
	    	coin = cls.normalize_coin(id)
	    	store[coin] = cls.get_coin_price(id)
	    return store


	@classmethod
	def threaded_process_range(cls, nthreads, id_range):
	    """process the id range in a specified number of threads"""
	    store = {}
	    threads = []
	    # create the threads
	    for i in range(nthreads):
	        ids = id_range[i::nthreads]
	        t = Thread(target=cls.process_range, args=(ids,store))
	        threads.append(t)

	    # start the threads
	    [ t.start() for t in threads ]
	    # wait for the threads to finish
	    [ t.join() for t in threads ]
	    return store


	@classmethod
	def get_coin_liquidity(cls, coin, is_overvalued, market_value):
		liquidity = 0
		try:
			resp = cls.get_orderbook(coin)
			if is_overvalued:
				bids = cls.return_orders(resp, is_overvalued)
				for b in bids:
					if cls.return_price(b) <= market_value * cls.percent_buffer:
						return int(liquidity)
					liquidity += cls.return_liqudity(b)
			else:
				asks = cls.return_orders(resp, is_overvalued)
				for a in asks:
					if cls.return_price(a) * cls.percent_buffer >= market_value:
						return int(liquidity)
					liquidity += cls.return_liqudity(a)

			return int(liquidity)
		except BaseException as err:
			#print(err)
			#print(traceback.format_exc())
			print("cannot find {} liqudity on {}".format(cls.get_exchange(),coin))
			return "Unknown"
  	

	def return_orders(resp, is_overvalued):
		if is_overvalued:
			return resp['bids']
		else:
			return resp['asks']


	def return_price(order):
		return float(order[0])


	def return_liqudity(order):
		return float(order[0]) * float(order[1])


class GeminiRequest(ExchangeRequest):
	def get_request_coin_price(coin):
		return float(requests.get('https://api.gemini.com/v1/pubticker/{}'.format(coin)).json()['last'])


	def get_coin_list():
		return requests.get('https://api.gemini.com/v1/symbols').json()


	def remove_unwanted_coins(all_coins):
		return [coin for coin in all_coins if "usd" in coin]


	def normalize_coin(coin):
		return coin.split("usd")[0].upper()


	@classmethod
	def get_coin_prices(cls,coins):
		return cls.threaded_process_range(5,coins)


	def get_orderbook(coin):
		return requests.get("https://api.gemini.com/v1/book/{}usd".format(coin.lower())).json()


	def return_price(order):
		return float(order['price'])


	def return_liqudity(order):
		return float(order['price']) * float(order['amount'])


class GateioRequest(ExchangeRequest):
	def get_coin_list():
		headers = {'Accept': 'application/json', 'Content-Type': 'application/json'}
		return requests.request('GET', "https://api.gateio.ws/api/v4/spot/tickers", headers=headers).json()


	def remove_unwanted_coins(all_coins):
		inactive_coins = annoying_coins.annoying_coins_gateio
		headers = {'Accept': 'application/json', 'Content-Type': 'application/json'}
		resp = requests.request('GET', "https://api.gateio.ws/api/v4/spot/currencies", headers=headers).json()
		for coin in resp:
			if True in coin.values():
				inactive_coins.add(coin["currency"])
		for coin in all_coins:
			if not coin['lowest_ask']:
				inactive_coins.add(coin['currency_pair'].split('_')[0]) 
		return {coin['currency_pair'].split('_')[0]:float(coin['lowest_ask']) for coin in all_coins if 'USD' in coin['currency_pair'] and coin['currency_pair'].split('_')[0] not in inactive_coins}


	def get_orderbook(coin):
		headers = {'Accept': 'application/json', 'Content-Type': 'application/json'}
		return requests.request('GET', "https://api.gateio.ws/api/v4/spot/order_book?currency_pair={}&limit=100".format(coin + '_USDT'), headers=headers).json()


class CoinbaseproRequest(ExchangeRequest):
	def get_request_coin_price(coin):
		if "-USD" not in coin:
			coin = coin + "-USD"
		return float(requests.get("https://api.pro.coinbase.com/products/{}/ticker".format(coin)).json()['price'])


	def get_coin_list():
		return requests.get("https://api.pro.coinbase.com/products").json()


	def remove_unwanted_coins(all_coins):
		inactive_coins = annoying_coins.annoying_coins_coinbasepro
		resp = requests.get("https://api.pro.coinbase.com/currencies").json()
		for coin in resp:
			if coin['status'] != 'online':
				inactive_coins.add(coin['id'])
		return [k['id'] for k in all_coins if "USD" in k['id'] and "EUR" not in k['id'] and "GBP" not in k['id'] and k['id'].split('-',1)[0] not in inactive_coins]


	def normalize_coin(coin):
		return coin.split('-')[0].upper()


	@classmethod
	def get_coin_prices(cls,coins):
		return cls.threaded_process_range(2,coins)


	def get_orderbook(coin):
		return requests.get("https://api.pro.coinbase.com/products/{}-USD/book?level=2".format(coin)).json()


class KucoinRequest(ExchangeRequest):
	def get_coin_list():
		return requests.get('https://api.kucoin.com/api/v1/market/allTickers').json()['data']['ticker']


	def remove_unwanted_coins(all_coins):
		inactive_coins = annoying_coins.annoying_coins_kucoin
		resp = requests.get('https://api.kucoin.com/api/v1/currencies').json()['data']
		for coin in resp:
			if not(coin["isWithdrawEnabled"] & coin["isDepositEnabled"]):
				inactive_coins.add(coin["currency"])
		return {coin['symbol'].replace("-USDT",""):float(coin['last']) for coin in all_coins if "USDT" in coin['symbol'] and "3S" not in coin['symbol'] and '3L' not in coin['symbol'] and coin['symbol'].replace("-USDT","") not in inactive_coins}


	def get_orderbook(coin):
		return requests.get("https://api.kucoin.com/api/v1/market/orderbook/level2_100?symbol={}-USDT".format(coin)).json()
  	

	def return_orders(resp, is_overvalued):
		if is_overvalued:
			return resp['data']['bids']
		else:
			return resp['data']['asks']


	@staticmethod
	def is_leverage_available(coin):
		resp = requests.get('https://api.kucoin.com/api/v1/symbols').json()['data']
		for r in resp:
			if r['symbol'].split('-')[0] == coin and r['symbol'].split('-')[1] == "USDT":
				return r['isMarginEnabled']


class KrakenRequest(ExchangeRequest):
	def get_request_coin_price(coin):
		"""if '_' not in coin:
			coin = coin + '_USDT'"""
		resp = requests.get('https://api.kraken.com/0/public/Ticker?pair={}USD'.format(coin)).json()['result']
		return float(resp[list(resp.keys())[0]]['b'][0])


	def get_coin_list():
		return requests.get('https://api.kraken.com/0/public/Assets').json()['result']


	def remove_unwanted_coins(all_coins):
		return [coin for (coin,val) in all_coins.items() if '.' not in coin and 'USD' not in coin and coin not in annoying_coins.not_us_coins_kraken]


	def normalize_coin(coin):
		return coin


	@classmethod
	def get_coin_prices(cls,coins):
		return cls.threaded_process_range(5,coins)


	def get_orderbook(coin):
		return requests.get("https://api.kraken.com/0/public/Depth?pair={}USD".format(coin)).json()['result']
  	

	def return_orders(resp, is_overvalued):
		if is_overvalued:
			return resp[list(resp.keys())[0]]['bids']
		else:
			return resp[list(resp.keys())[0]]['asks']


class MexcRequest(ExchangeRequest):
	def get_request_coin_price(coin):
		if '_' not in coin:
			coin = coin + '_USDT'
		return float(requests.get("https://www.mexc.com/open/api/v2/market/ticker?symbol={}".format(coin)).json()['data'][0]['last'])


	def get_coin_list():
		return requests.get("https://www.mexc.com/open/api/v2/market/symbols").json()['data']


	def remove_unwanted_coins(all_coins):
		leveraged_symbols = {'2S','3S','4S','2L','3L','4L','5S','5L'}
		return [coin['symbol'] for coin in all_coins if coin['state'] == 'ENABLED' and "USD" in coin['symbol'] and coin['symbol'].split('_')[0][-2:] not in leveraged_symbols and coin['symbol'].split('_')[0] not in annoying_coins.annoying_coins_mexc]


	def normalize_coin(coin):
		return coin.split('_')[0].upper()


	@classmethod
	def get_coin_prices(cls,coins):
		return cls.threaded_process_range(8,coins)


	def get_orderbook(coin):
		return requests.get("https://www.mexc.com/open/api/v2/market/depth?symbol={}_USDT&depth=2000".format(coin)).json()['data']


	def return_price(order):
		return float(order['price'])


	def return_liqudity(order):
		return float(order['price']) * float(order['quantity'])


#print(MexcRequest.get_coin_price("TOKEN_USDT"))
#print(MexcRequest.get_all_prices())
#print(CoinbaseproRequest.get_coin_price("ETH-USD"))
#x = GeminiRequest.get_all_prices()
#for a in x:
	#if x[a] == -1:
		#print(a)
		#print(CoinbaseproRequest.get_coin_price(a))
#print(MexcRequest.get_coin_liquidity("BTC", True, 46000))
#print(GeminiRequest.get_all_prices())
#print(GateioRequest.get_all_prices())
#print(GateioRequest.get_coin_liquidity("BTC",1,40000))
#print(KucoinRequest.get_all_prices())
#print(KrakenRequest.get_all_prices()["JASMY"])
#print(GeminiRequest.get_all_prices())

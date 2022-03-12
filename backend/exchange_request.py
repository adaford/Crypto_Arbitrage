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



class ExchangeRequest:
	percent_buffer = 1.01

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
		except:
			return "Unknown"


	def get_orderbook(coin):
		raise NotImplementedError('')
  	

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
	@staticmethod
	def get_coin_price(coin_pair):
		return float(requests.get('https://api.gemini.com/v1/pubticker/{}'.format(coin_pair)).json()['last'])


	@staticmethod
	def get_all_prices():
		ret = {}
		try:
			coins = requests.get('https://api.gemini.com/v1/symbols').json()
		except:
			print("cant get gemini coins")
			return ret
		for c in coins:
			if "usd" in c:
				try:
					ret[c.replace("usd","").upper()] = float(requests.get('https://api.gemini.com/v1/pubticker/{}'.format(c)).json()['last'])
				except:
					pass
		return ret


	def get_orderbook(coin):
		return requests.get("https://api.gemini.com/v1/book/{}usd".format(coin.lower())).json()


	def return_price(order):
		return float(order['price'])


	def return_liqudity(order):
		return float(order['price']) * float(order['amount'])


class GateioRequest(ExchangeRequest):
	@staticmethod
	def get_coin_price(coin_pair):
		coin_gateio = coin_pair[0:-3].upper() + '_' + coin_pair[-3:].upper() + 'T'
		headers = {'Accept': 'application/json', 'Content-Type': 'application/json'}
		return float(requests.get("https://api.gateio.ws/api/v4/spot/tickers?currency_pair={}".format(coin_gateio),headers=headers).json()[0]['last'])


	@staticmethod
	def get_all_prices():
		ret = {}
		inactive_coins = {}
		
		host = "https://api.gateio.ws"
		prefix = "/api/v4"
		url_prices  = "/spot/tickers"
		url_statuses = "/spot/currencies"
		headers = {'Accept': 'application/json', 'Content-Type': 'application/json'}
		query_param = ''

		try:
			resp = requests.request('GET', host + prefix + url_prices, headers=headers).json()
			resp2 = requests.request('GET', host + prefix + url_statuses, headers=headers).json()
		except:
			return ret
		
		for coin in resp2:
			inactive_coins[coin["currency"]] = True in coin.values()

		for coin in resp:
			try:
				if 'USD' in coin['currency_pair']:
					if inactive_coins[coin['currency_pair'].split('_')[0]]:
						continue
					ret[coin['currency_pair'].split('_')[0]] = float(coin['last'])
			except:
				pass

		return ret


	def get_orderbook(coin):
		host = "https://api.gateio.ws"
		prefix = "/api/v4"
		headers = {'Accept': 'application/json', 'Content-Type': 'application/json'}
		url = '/spot/order_book'
		query_param = 'currency_pair={}&limit=100'.format(coin + '_USDT')
		return requests.request('GET', host + prefix + url + "?" + query_param, headers=headers).json()


class CoinbaseproRequest(ExchangeRequest):
	@staticmethod
	def get_coin_price(coin_pair):
		coin_coinbase = coin_pair[0:-3].upper() + '-' + coin_pair[-3:].upper()
		return float(requests.get("https://api.pro.coinbase.com/products/{}/ticker".format(coin_coinbase)).json()['price'])


	@staticmethod
	def get_all_prices():
		inactive_coins = annoying_coins.annoying_coins_coinbasepro
		resp = requests.get('https://api.exchange.coinbase.com/currencies').json()
		for coin in resp:
			if coin['status'] != 'online':
				inactive_coins.add(coin['id'])
		ret = {}
		try:
			resp = requests.get('https://api.pro.coinbase.com/products').json()
		except:
			print("coinbase prices unavailable")
			return ret
		coins = [k['id'] for k in resp if "USD" in k['id'] and "EUR" not in k['id'] and "GBP" not in k['id'] and k['id'].split('-',1)[0] not in inactive_coins]
		for c in coins:
			try:
				resp = requests.get('https://api.pro.coinbase.com/products/{}/ticker'.format(c))
				ret[c.split('-',1)[0]] = float(resp.json()['price'])
			except:
				pass
		return ret


	def get_orderbook(coin):
		return requests.get("https://api.pro.coinbase.com/products/{}-USD/book?level=2".format(coin)).json()


class KucoinRequest(ExchangeRequest):
	@staticmethod
	def get_coin_price(coin_pair):
		coin_pair = coin_pair.split("usd")[0].upper() + "-USDT"
		return float(requests.get("https://api.kucoin.com/api/v1/market/orderbook/level1?symbol={}".format(coin_pair)).json()['data']['price'])


	@staticmethod
	def get_all_prices():
		#uses strictly usdt
		ret = {}
		inactive_coins = {}
		try:
			resp = requests.get('https://api.kucoin.com/api/v1/market/allTickers').json()['data']['ticker']
			resp2 = requests.get('https://api.kucoin.com/api/v1/currencies').json()['data']
		except:
			print("cant get kucoin prices")
			return ret
		for coin in resp2:
			inactive_coins[coin["currency"]] = not(coin["isWithdrawEnabled"] & coin["isDepositEnabled"])
		for d in resp:
			try:
				if "USDT" in d['symbol'] and "3S" not in d['symbol'] and '3L' not in d['symbol'] and not inactive_coins[d['symbol'].replace("-USDT","")]:
					ret[d['symbol'].replace("-USDT","")] = float(d['buy'])
			except:
				pass
		for coin in annoying_coins.annoying_coins_kucoin:
			try:
				del ret[coin]
			except:
				pass
		return ret


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
	@staticmethod
	def get_coin_price(coin_pair):
		coin_pair = coin_pair.split("usd")[0].upper()
		resp = requests.get('https://api.kraken.com/0/public/Ticker?pair={}USD'.format(coin_pair)).json()
		try:
			resp = resp['result']
			return float(resp[list(resp.keys())[0]]['a'][0])
		except:
			return -1


	@staticmethod
	def get_all_prices():
		ret = {}
		try:
			resp = requests.get('https://api.kraken.com/0/public/Assets').json()['result']
		except:
			print("Kraken prices unavailable")
			return ret
		coins = [key for key, val in resp.items() if ('.' not in key and 'USD' not in key and key not in annoying_coins.not_us_coins_kraken)]
		for c in coins:
			try:
				resp = requests.get('https://api.kraken.com/0/public/Ticker?pair={}USD'.format(c)).json()
				ret[c] = float(resp['result'][list(resp.keys())[0]]['a'][0])
			except:
				pass
		try:
			ret["BTC"] = ret["XBT"]
			ret["DOGE"] = ret["XDG"]
		except:
			pass
		return ret


	def get_orderbook(coin):
		return requests.get("https://api.kraken.com/0/public/Depth?pair={}USD".format(coin)).json()['result']
  	

	def return_orders(resp, is_overvalued):
		if is_overvalued:
			return resp[list(resp.keys())[0]]['bids']
		else:
			return resp[list(resp.keys())[0]]['asks']


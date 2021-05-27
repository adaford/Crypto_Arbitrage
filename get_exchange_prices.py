import requests
import sys
from requests import Request, Session
from requests.exceptions import ConnectionError, Timeout, TooManyRedirects
import json


def get_prices_coinmarketcap():
	url = 'https://pro-api.coinmarketcap.com/v1/cryptocurrency/listings/latest'
	parameters = {
		'start':'1',
		'limit':'150',
		'convert':'USD'
	}
	headers = {
		'Accepts': 'application/json',
		'X-CMC_PRO_API_KEY': 'c848953f-8966-44eb-88f8-c221206ba216',
	}

	session = Session()
	session.headers.update(headers)
	ret = {}
	try:
		response = session.get(url, params=parameters)
		data = json.loads(response.text)["data"]
		for i in range(0,131):
			ret[data[i]["symbol"]] = float(data[i]["quote"]["USD"]["price"])
		return ret
	except (ConnectionError, Timeout, TooManyRedirects) as e:
		print(e)

	

#slow
def get_kraken_prices(kraken_coins):
	ret = {}
	for c in kraken_coins:
		resp = requests.get('https://api.kraken.com/0/public/Ticker?pair={}USD'.format(c))

		try:
			ret[c] = float(resp.json()['result']['X{}ZUSD'.format(c)]['a'][0])
		except:
			try:
				ret[c] = float(resp.json()['result']['{}USD'.format(c)]['a'][0])
			except:
				pass

	ret["BTC"] = ret["XBT"]
	ret["DOGE"] = ret["XDG"]
	return ret


def get_coinbasepro_prices(coins):
	ret = {}
	for c in coins:
		resp = requests.get('https://api.pro.coinbase.com/products/{}/ticker'.format(c+"-USD"))

		try:
			ret[c] = float(resp.json()['price'])
		except:
			pass

	return ret


def get_binanceUS_prices(coins):
	ret = {}
	resp = requests.get('https://api.binance.us/api/v3/ticker/bookTicker').json()
	for pair in resp:
		if pair['symbol'].replace("USD","") in coins:
			ret[pair['symbol'].replace("USD","")] = float(pair['bidPrice'])
		elif pair['symbol'].replace("USDT","") in coins:
			ret[pair['symbol'].replace("USDT","")] = float(pair['bidPrice'])
		elif pair['symbol'].replace("BUSD","") in coins:
			ret[pair['symbol'].replace("BUSD","")] = float(pair['bidPrice'])

	del ret['XRP']
	del ret['NANO']
	return ret


def get_kucoin_prices(coins):
	#uses strictly usdt
	ret = {}
	resp = requests.get('https://api.kucoin.com/api/v1/market/allTickers').json()['data']['ticker']
	for d in resp:
		if d['symbol'].replace("-USDT","") in coins:
			ret[d['symbol'].replace("-USDT","")] = float(d['buy'])

	return ret


def get_gemini_prices(coins):
	ret = {}

	resp = requests.get('https://api.gemini.com/v1/pricefeed').json()
	for c in resp:
		coin = c['pair']
		if coin[-3:] == "USD":
			ret[coin.replace("USD","")] = float(c['price'])

	return ret


def get_bittrex_prices(coins):
	ret = {}
	resp = requests.get('https://api.bittrex.com/v3/markets/tickers').json()
	for c in resp:
		coin = c['symbol']
		if coin[-3:] == "USD":
			ret[coin.replace("-USD","")] = float(c['lastTradeRate'])
		elif coin[-4:] == "USDT":
			ret[coin.replace("-USDT","")] = float(c['lastTradeRate'])

	del ret["CRV"]
	del ret["RENBTC"]
	del ret["KLAY"]
	del ret["WBTC"]
	del ret["REV"]
	del ret["SNX"]
	del ret["CRO"]
	del ret["AVAX"]
	del ret["USDN"]
	del ret["RSR"]

	return ret

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
def get_kraken_prices():
	ret = {}
	try:
		resp = requests.get('https://api.kraken.com/0/public/Assets').json()['result']
	except:
		print("Kraken prices unavailable")
		return ret
	not_us_coins = {'ANKR','BNT','EWT','FLOW','GHST','GRT','LPT','MINA','MKR','RARI','REN','SAND','SOL','SRM','SUSHI','XRP','ZRX'}
	coins = [val['altname'] for key, val in resp.items() if ('.' not in key and 'USD' not in key and key not in not_us_coins)]
	for c in coins:
		try:
			resp = requests.get('https://api.kraken.com/0/public/Ticker?pair={}USD'.format(c))
		except:
			continue

		try:
			ret[c] = float(resp.json()['result']['X{}ZUSD'.format(c)]['a'][0])
		except:
			try:
				ret[c] = float(resp.json()['result']['{}USD'.format(c)]['a'][0])
			except:
				pass

	try:
		ret["BTC"] = ret["XBT"]
		ret["DOGE"] = ret["XDG"]
	except:
		pass

	return ret


def get_coinbasepro_prices():
	ret = {}
	try:
		resp = requests.get('https://api.pro.coinbase.com/products').json()
	except:
		print("coinbase prices unavailable")
		return ret

	coins = [k['id'] for k in resp if "USD" in k['id']]
	
	for c in coins:
		try:
			resp = requests.get('https://api.pro.coinbase.com/products/{}/ticker'.format(c))
			ret[c.split('-',1)[0]] = float(resp.json()['price'])
		except:
			pass

	return ret


#could be fixed
def get_binanceUS_prices(binanceUS_coins):
	ret = {}
	try:
		resp = requests.get('https://api.binance.us/api/v3/ticker/bookTicker').json()
	except:
		print("error getting binanceUS response")
		return ret

	for pair in resp:
		if pair['symbol'].replace("USD","") in binanceUS_coins:
			ret[pair['symbol'].replace("USD","")] = float(pair['bidPrice'])
		elif pair['symbol'].replace("USDT","") in binanceUS_coins:
			ret[pair['symbol'].replace("USDT","")] = float(pair['bidPrice'])
		elif pair['symbol'].replace("BUSD","") in binanceUS_coins:
			ret[pair['symbol'].replace("BUSD","")] = float(pair['bidPrice'])

	#del ret["XLM"]
	#del ret["HNT"]

	return ret


def get_kucoin_prices(coins):
	#uses strictly usdt
	ret = {}
	try:
		resp = requests.get('https://api.kucoin.com/api/v1/market/allTickers').json()['data']['ticker']
	except:
		print("cant get kucoin prices")
		return ret

	for d in resp:
		if d['symbol'].replace("-USDT","") in coins:
			try:
				ret[d['symbol'].replace("-USDT","")] = float(d['buy'])
			except:
				print(d['symbol'] + " not working")

	return ret


def get_gemini_prices():
	ret = {}
	try:
		coins = requests.get('https://api.gemini.com/v1/symbols').json()
	except:
		print("cant get gemini coins")
		return ret
	for c in coins:
		if "usd" in c:
			ret[c.replace("usd","").upper()] = float(requests.get('https://api.gemini.com/v1/pubticker/{}'.format(c)).json()['last'])

	return ret


def get_bittrex_prices():
	ret = {}
	resp = requests.get('https://api.bittrex.com/v3/markets/tickers').json()
	for c in resp:
		coin = c['symbol']
		if coin[-3:] == "USD":
			ret[coin.replace("-USD","")] = float(c['lastTradeRate'])
		elif coin[-4:] == "USDT":
			ret[coin.replace("-USDT","")] = float(c['lastTradeRate'])

	try:
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
		del ret["1INCH"]
		del ret["CKB"]
		del ret["KSM"]
		del ret["QTUM"]
		del ret["LUNA"]
		del ret["AMP"]
		del ret["XDC"]
	except:
		pass

	return ret
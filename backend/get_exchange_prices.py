import requests
import sys
from requests import Request, Session
from requests.exceptions import ConnectionError, Timeout, TooManyRedirects
import json
import random


#4 accounts cause theyre *free*
def get_prices_coinmarketcap():
	url = 'https://pro-api.coinmarketcap.com/v1/cryptocurrency/listings/latest'
	parameters = {
		'start':'1',
		'limit':'200',
		'convert':'USD'
	}
	headers = {
		'Accepts': 'application/json',
		'X-CMC_PRO_API_KEY': 'c848953f-8966-44eb-88f8-c221206ba216',
	}

	parameters2 = {
		'start':'201',
		'limit':'200',
		'convert':'USD'
	}	
	headers2 = {
		'Accepts': 'application/json',
		'X-CMC_PRO_API_KEY': 'e2ad1ceb-83ff-4d2d-b1b0-cdb194286d51',
	}
	parameters3 = {
		'start':'1',
		'limit':'200',
		'convert':'USD'
	}	
	headers3 = {
		'Accepts': 'application/json',
		'X-CMC_PRO_API_KEY': '01459736-f9fa-4d5c-aa0a-840bcc5a9aa9',
	}
	parameters4 = {
		'start':'201',
		'limit':'200',
		'convert':'USD'
	}	
	headers4 = {
		'Accepts': 'application/json',
		'X-CMC_PRO_API_KEY': '6370fef4-d029-4edb-9b7d-7f4e04e2330e',
	}

	session = Session()
	
	ret = {}
	try:
		x = random.randint(0,1)
		if x == 0:
			session.headers.update(headers)
			response = session.get(url, params=parameters)
			data = json.loads(response.text)["data"]
			for i in range(200):
				ret[data[i]["symbol"]] = float(data[i]["quote"]["USD"]["price"])

			session.headers.update(headers2)
			response = session.get(url, params=parameters2)
			data = json.loads(response.text)["data"]
			for i in range(200):
				ret[data[i]["symbol"]] = float(data[i]["quote"]["USD"]["price"])

		elif x == 1:
			session.headers.update(headers3)
			response = session.get(url, params=parameters3)
			data = json.loads(response.text)["data"]
			for i in range(200):
				ret[data[i]["symbol"]] = float(data[i]["quote"]["USD"]["price"])

			session.headers.update(headers4)
			response = session.get(url, params=parameters4)
			data = json.loads(response.text)["data"]
			for i in range(200):
				ret[data[i]["symbol"]] = float(data[i]["quote"]["USD"]["price"])

		annoying_coins = ["KEEP","GLMR","BZRX","OMI","HXRO","DG","LSK","SOUL","CORE","DESO","SOLO","AMPL","PRO","NCT","BTT","DAR","LCX","ICX","PYR","REEF","KIN","TIME","WEMIX","REP","IOTX","VLX","TTT","ORBS","CEEK","COTI","SAFEMOON","ORC","YOOSHI","ELF","KDA","QUACK"]
		for coin in annoying_coins:
			if coin in ret.keys():
				del ret[coin]

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
	not_us_coins = {'1INCH','ACA','AKT','ANKR','ASTR','BADGER','BAND','BNC','BNT','CQT','CTSI','EWT','FIDA','GHST','GLMR','GRT','INJ','KAR','KILT','KINT','LPT','LRC','MINA','MIR','MNGO','MOVR','OGN','OXY','PERP','PHA','RARI','RAY','REN','SDN','SRM','SUSHI','WBTC','XRP','ZRX'}
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


#slow
def get_coinbasepro_prices():
	annoying_coins = ["SOLO","ZRX","SOUL","ALGO","IOTX","GTC","REP"]
	inactive_coins = set(annoying_coins)

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

#fast
def get_binanceUS_prices(binanceUS_coins):
	ret = {}
	try:
		resp = requests.get('https://api.binance.us/api/v3/ticker/bookTicker').json()
	except:
		print("error getting binanceUS response")
		return ret

	for pair in resp:
		if pair['symbol'].replace("USD","") in binanceUS_coins:
			ret[pair['symbol'].replace("USD","")] = ((float(pair['askPrice']) + float(pair['bidPrice'])))/2
		elif pair['symbol'].replace("USDT","") in binanceUS_coins:
			ret[pair['symbol'].replace("USDT","")] = ((float(pair['askPrice']) + float(pair['bidPrice'])))/2
		elif pair['symbol'].replace("BUSD","") in binanceUS_coins:
			ret[pair['symbol'].replace("BUSD","")] = ((float(pair['askPrice']) + float(pair['bidPrice'])))/2

	return ret


#fast
def get_kucoin_prices():
	#uses strictly usdt
	ret = {}
	inactive_coins = []
	potentially_inactive_coins = {}
	try:
		resp = requests.get('https://api.kucoin.com/api/v1/market/allTickers').json()['data']['ticker']
		resp2 = requests.get('https://api.kucoin.com/api/v1/currencies').json()['data']
	except:
		print("cant get kucoin prices")
		return ret

	for coin in resp2:
		potentially_inactive_coins[coin["currency"]] = coin["isWithdrawEnabled"] & coin["isDepositEnabled"]

	for d in resp:
		try:
			if "USDT" in d['symbol'] and "3S" not in d['symbol'] and '3L' not in d['symbol'] and potentially_inactive_coins[d['symbol'].replace("-USDT","")]:
				ret[d['symbol'].replace("-USDT","")] = float(d['buy'])
		except:
			pass
			#print(d['symbol'] + " not working")

	annoying_coins = ["SUSD","GTC","STC","TIME","BCHA","BUY","GRIN","QI","NANO","BZRX","PDEX"]
	for coin in annoying_coins:
		try:
			del ret[coin]
		except:
			pass

	return ret


#slow but has small list of coins
def get_gemini_prices():
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


#fast
def get_bittrex_prices():
	ret = {}
	resp = requests.get('https://api.bittrex.com/v3/markets/tickers').json()
	for c in resp:
		coin = c['symbol']
		if coin[-3:] == "USD":
			ret[coin.replace("-USD","")] = float(c['lastTradeRate'])
		elif coin[-4:] == "USDT":
			ret[coin.replace("-USDT","")] = float(c['lastTradeRate'])

	not_us_coins = ["SYS","ZEN","HIVE","FIL","AMP","AVAX","CRV","CRTS","RENBTC","KLAY","WBTC","REV","SNX","CRO","USDN","RSR","1INCH","CKB","KSM","QTUM","LUNA","XDC","SAND","QNT","MED","VLX"]

	for coin in not_us_coins:
		try:
			del ret[coin]
		except:
			pass

	return ret


#slow
def get_cryptodotcom_prices(coinmarketcap_list):
	ret = {}
	coins = []
	coin_dict = requests.get('https://api.crypto.com/v2/public/get-instruments').json()["result"]["instruments"]
	for c in coin_dict:
		if "USD" in c["instrument_name"] and c["instrument_name"].replace("_USDT","").replace("_USDC","").replace("_USD","") in coinmarketcap_list:
			coins.append(c["instrument_name"])

	for c in coins:
		try:
			ret[c.replace("_USDT","").replace("_USDC","").replace("_USD","")] = float(requests.get('https://api.crypto.com/v2/public/get-book?instrument_name={}&depth=1'.format(c)).json()["result"]["data"][0]["bids"][0][0])
		except:
			pass
	return ret


#fast
def get_lbank_prices():
	ret = {}
	headers = {"contentType": "application/x-www-form-urlencoded"}
	resp = requests.get('https://api.lbkex.com/v1/ticker.do?symbol=all', headers=headers).json()
	
	for r in resp:
		if "usd" in r['symbol']:
			ret[r['symbol'].replace("_usdt","").replace("_usd","").upper()] = float(r['ticker']['latest'])

	return ret


#fast
def get_gateio_prices():
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


def get_ftx_prices():
	ret = {}

	url =  'https://ftx.com/api/markets'
	try:
		response = requests.get(url).json()['result']
	except:
		return ret

	for coinpair in response:
		if "USD" in coinpair['name'] and "BULL" not in coinpair['name'] and "BEAR" not in coinpair['name'] and "HALF" not in coinpair['name'] and "HEDGE" not in coinpair['name']:
			coin = coinpair['name'].split('/')[0]
			ret[coin] = coinpair['last']

	return ret


def get_kucoin_leverage(coin):
	resp = requests.get('https://api.kucoin.com/api/v1/symbols').json()['data']
	for r in resp:
		if r['symbol'].split('-')[0] == coin and r['symbol'].split('-')[1] == "USDT":
			return r['isMarginEnabled']


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
		'X-CMC_PRO_API_KEY': api_key_1,
	}

	parameters2 = {
		'start':'150',
		'limit':'300',
		'convert':'USD'
	}	
	headers2 = {
		'Accepts': 'application/json',
		'X-CMC_PRO_API_KEY': api_key_2,
	}

	session = Session()
	session.headers.update(headers)
	ret = {}
	try:
		response = session.get(url, params=parameters)
		data = json.loads(response.text)["data"]
		for i in range(0,149):
			ret[data[i]["symbol"]] = float(data[i]["quote"]["USD"]["price"])

		session = Session()
		session.headers.update(headers2)
		response = session.get(url, params=parameters2)
		data = json.loads(response.text)["data"]
		for i in range(0,149):
			ret[data[i]["symbol"]] = float(data[i]["quote"]["USD"]["price"])

		annoying_coins = ["IOTX","VLX","TTT","ORBS","CEEK","COTI","SAFEMOON","ORC","YOOSHI"]
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
	not_us_coins = {'1INCH','ANKR','AXS','BNT','CTSI','EWT','GHST','GRT','LPT','MINA','MKR','MOVR','RARI','REN','SAND','SOL','SRM','SUSHI','XRP','ZRX'}
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

	try:
		ret["CELO"] = ret["CGLD"]
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


#fast
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

	not_us_coins = ["ZEN","HIVE","FIL","AMP","AVAX","CRV","RENBTC","KLAY","WBTC","REV","SNX","CRO","USDN","RSR","1INCH","CKB","KSM","QTUM","LUNA","XDC","SAND","QNT","MED","VLX"]

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

	host = "https://api.gateio.ws"
	prefix = "/api/v4"
	headers = {'Accept': 'application/json', 'Content-Type': 'application/json'}

	url = '/spot/tickers'
	query_param = ''
	resp = requests.request('GET', host + prefix + url, headers=headers).json()
	for coin in resp:
		if 'USD' in coin['currency_pair']:
			ret[coin['currency_pair'].split('_')[0]] = float(coin['last'])

	return ret

#print(get_cryptodotcom_prices())
#get_lbank_prices()
#print(get_coinbasepro_prices())
#print(get_gemini_prices())
#get_gateio_prices()
#print(get_prices_coinmarketcap())
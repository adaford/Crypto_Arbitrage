import requests
import math
import time
import json
import base64
import hmac
import hashlib
import sys
from random import randint
#import cbpro
import SMS
import api_keys


class ExchangeTrade:
	def __init__(self, coinpair, arbitraged_exchange, fill_above, limit_above, num_limit_orders, is_extra_aggressive):
		self.coinpair = coinpair 			#"btcusd"
		self.arbitraged_exchange = arbitraged_exchange
		self.fill_above = fill_above
		self.limit_above = limit_above
		self.num_limit_orders = num_limit_orders
		self.is_extra_aggressive = is_extra_aggressive
		self.quote_increment = None
		self.min_order_size = None
		self.quote_increment_round = None
		self.coin_status = None
		self.my_coin_quantity = None
		self.coinpair_orderbook = None
		self.coin_price = None
		self.sms = True
		self.sms2 = True
		self.is_stablecoin = True if fill_above <= 1.02 else False
		self.my_orderbook = []
		self.my_orderbook_prices = []
		self.exchanges = {'gemini':GeminiTrade,'coinbasepro':CoinbaseproTrade,'kucoin':KucoinTrade,"gateio":GateioTrade,"kraken":KrakenTrade}
		self.get_coinpair_details()


	def get_coinpair_details(self):
		pass


	def request_api(self):
		pass


	def get_my_orderbook(self):
		pass


	def get_exchange(self):
		return self.__class__.__name__.split("Trade")[0].lower()


	def get_coin_price_arbitraged_exchange(self):
		self.coin_price = getattr(self.exchanges[self.arbitraged_exchange],"get_coin_price")(self.coinpair)


	def get_my_orders(self):
		my_orderbook = self.get_my_orderbook()
		if my_orderbook == 0 or type(my_orderbook) != list:
			print("cant find {} orderbook on {}".format(self.coinpair, self.get_exchange()))
			return 0
		self.my_orderbook = [o for o in my_orderbook if o['symbol'] == self.coinpair and o['side'] == 'sell']
		self.my_orderbook.sort(key=lambda x : float(x['price']))
		self.my_orderbook_prices = [o['price'] for o in self.my_orderbook]
		return 1


	#Fills bids above EXCHANGE coin_price * FILL_ORDER_PERCENT
	def fill_bids(self):
		for order in self.coinpair_orderbook['bids']:
			if float(order['price']) >= self.coin_price * self.fill_above:
				if float(order['amount']) > self.min_order_size + self.quote_increment:
					if self.my_coin_quantity < float(order['amount']):
						if len(self.my_orderbook):
							print("cancelling orders for {}, current quantity = {}".format(self.coinpair,self.my_coin_quantity))
							self.cancel_orders()
							time.sleep(.5)
							print("new coin quantity = " + self.my_coin_quantity)

						if self.my_coin_quantity < round(self.min_order_size + self.quote_increment, self.quote_increment_round):
							if self.sms2:
								SMS.send("{} arbitrage available on {} but you have 0 left".format(self.coinpair,self.get_exchange()))
								self.sms2 = False
								print("out of coin {}".format(self.coinpair))
							return
					
					sell_quantity = min(round(float(order['amount'])-self.quote_increment,self.quote_increment_round),self.my_coin_quantity)
					if sell_quantity == 0:
						print(self.coinpair_orderbook['bids'], self.coin_price)
						continue

					print("sending request to sell {} {} on {} at price {}".format(sell_quantity,self.coinpair,self.get_exchange(),order['price']))
					try:
						sell_order = self.sell_coins(sell_quantity,order['price'])
						self.my_coin_quantity -= float(sell_order['executed_amount'])
					except:
						print(sell_order)
			else:
				break


	#return up to LIMIT_ORDER new orders that undercut existing whale asks by smallest price difference possible
	def find_limit_order_values(self):
		count, last_order_price, total = 0,0,0
		new_orders = []
		for o in self.coinpair_orderbook['asks']:
			if o['price'] not in self.my_orderbook_prices:
				total += float(o['amount']) * float(o['price'])
			else:
				continue

			if float(o['price']) <= self.limit_above * self.coin_price or (last_order_price and (float(o['price'])) <= last_order_price * 1.005):
				continue

			if (float(o['amount']) >= 150/self.coin_price or (self.is_stablecoin and float(o['amount']) >= 50)) or (total >= 200/self.coin_price and float(o['amount']) >= 20/self.coin_price):
				new_orders.append(round(float(o['price'])-self.quote_increment, self.quote_increment_round))
				total = 0
				count += 1
				if count >= self.num_limit_orders:
					break

		if len(new_orders) == 0:
			new_orders.append(round(float(self.coinpair_orderbook['asks'][-1]['price']) - self.quote_increment, self.quote_increment_round))

		return new_orders


	#creates LIMIT_ORDERS number of new limit orders           #BUG - if out of coins and existing order in then it wont have coins to create first order
	def replace_current_orders(self,new_orders):
		if not self.is_stablecoin:
			lowerbound, upperbound = int(4200/self.coin_price), int(5900/self.coin_price)
		else:
			lowerbound, upperbound = int(9300/self.coin_price), int(13200/self.coin_price)

		self.cancel_orders(new_orders)

		if self.my_coin_quantity == 0:
			return

		for i in range(len(new_orders)):
			if new_orders[i] not in [float(x) for x in self.my_orderbook_prices]:
				sell_quantity = randint(lowerbound,upperbound)
				sell_order = self.sell_coins(min(sell_quantity,self.my_coin_quantity),new_orders[i])
				print(sell_order)
				self.my_coin_quantity = round(self.my_coin_quantity - min(sell_quantity,self.my_coin_quantity), self.quote_increment_round) 
		
		if self.is_extra_aggressive:
			sell_quantity = randint(lowerbound,upperbound)
			time.sleep(.1)
			self.sell_coins(min(sell_quantity,self.my_coin_quantity),new_orders[0] - 2*self.quote_increment)


	def correct_price(self):
		if self.coinpair_orderbook['asks'][0]['price'] in self.my_orderbook_prices:
			if float(requests.get('https://api.gemini.com/v1/pubticker/{}'.format(trade.coinpair)).json()['last']) >= self.coin_price * self.fill_bids:
				self.sell_coins(.1,.99)


class GeminiTrade(ExchangeTrade):
	def __init__(self, coinpair, arbitraged_exchange, fill_above, limit_above, num_limit_orders, is_extra_aggressive):
		super().__init__(coinpair, arbitraged_exchange, fill_above, limit_above, num_limit_orders, is_extra_aggressive)


	def get_coinpair_details(self):
		try:
			coin_details = requests.get("https://api.gemini.com/v1/symbols/details/{}".format(self.coinpair)).json()
			self.quote_increment = float(coin_details['quote_increment'])
			self.min_order_size =  float(coin_details['min_order_size'])
			self.quote_increment_round = round(math.log(1/self.quote_increment,10))
			self.coin_status = coin_details['status']
		except:
			print("cannot get {} status on {}".format(self.coinpair,self.get_exchange()))


	def get_coinpair_orderbook(self):
		try:
			self.coinpair_orderbook = requests.get("https://api.gemini.com/v1/book/{}".format(self.coinpair)).json()
		except:
			print("cant find {} orderbook on gemini".format(self.coinpair))

	
	def get_coin_quantity(self):
		my_coin_quantities = self.request_api('balances',0,0)
		if type(my_coin_quantities) is not list:
			print("can't find coin quantity {}".format(self.coinpair))
			self.my_coin_quantity = 0
			return 0

		for coin_quantity in my_coin_quantities:
			if coin_quantity['currency'] == self.coinpair.replace("usd", "").upper():
				self.my_coin_quantity = max(round(float(coin_quantity['available']) - self.quote_increment, self.quote_increment_round),0)
				return 1

		print("can't find coin quantity {}".format(self.coinpair))
		self.my_coin_quantity = 0
		return 0	


	def get_my_orderbook(self):
		return self.request_api('orders',0,0)	


	def cancel_orders(self, dont_cancel=[]):
		for i in range(len(self.my_orderbook)):
			if float(self.my_orderbook_prices[i]) not in dont_cancel:
				self.request_api('order/cancel',self.my_orderbook[i]['order_id'],0)
				self.my_coin_quantity += float(self.my_orderbook[i]['remaining_amount'])

		self.my_coin_quantity = round(self.my_coin_quantity,self.quote_increment_round)


	def buy_coins(self,quantity,price):
		self.request_api('order/new',0,[quantity,price])


	def sell_coins(self,quantity,price):
		self.request_api('order/new',0,[-quantity,price])


	def transfer_coins(self,quantity,address):
		pass


	def request_api(self, url_prefix, order_id, order):
		url = "https://api.gemini.com/v1/" + url_prefix
		gemini_api_key = api_keys.gemini_api_key
		gemini_api_secret = api_keys.gemini_api_secret.encode()
		payload_nonce =  str(time.time()*100000)
		payload =  {"request": "/v1/{}".format(url_prefix), "nonce": payload_nonce, "account" : ['primary']}
		if order_id:
			payload['order_id'] = order_id
		elif order:
			ordertype = 'buy' if float(order[0]) > 0 else 'sell'
			order[0] = str(round(abs(float(order[0])),self.quote_increment_round))
			if float(order[0]) == 0:
				return -1
			payload['symbol'], payload['side'], payload['type'] = self.coinpair, ordertype, 'exchange limit'
			payload['amount'], payload['price'] = order[0], order[1]
			if float(payload['price']) <= float(self.coinpair_orderbook['bids'][0]['price']) and ordertype == 'sell':
				payload['options'] = ["immediate-or-cancel"]
				print("sending request to {} {} {} at price {}".format(ordertype,order[0],self.coinpair,order[1]))

		encoded_payload = json.dumps(payload).encode()
		b64 = base64.b64encode(encoded_payload)
		signature = hmac.new(gemini_api_secret, b64, hashlib.sha384).hexdigest()

		headers = {
		    'Content-Type': "text/plain",
		    'Content-Length': "0",
		    'X-GEMINI-APIKEY': api_keys.gemini_api_key,
		    'X-GEMINI-PAYLOAD': b64,
		    'X-GEMINI-SIGNATURE': signature,
		    'Cache-Control': "no-cache"
		    }

		try:
			resp = requests.post(url, headers=headers).json()
		except:
			print("bad response on url: {} with payload {}".format(url,payload))
			return 0

		if 'options' in payload and 'executed_amount' in resp:
			if float(resp['executed_amount']) == 0:
				print("Gemini stopped " + ordertype)
				time.sleep(30)
			else:
				print("{} {} {} at price {} at time {}".format(ordertype,resp['executed_amount'],self.coinpair.replace("usd","").upper(),order[1],time.strftime("%H:%M:%S", time.localtime())))

		if 'options' in payload and 'executed_amount' in resp and float(resp['executed_amount']) >= 50/self.coin_price and self.sms:
			SMS.send("{} {} {} at price {}".format(ordertype,resp['executed_amount'], self.coinpair.replace("usd","").upper(), resp['price']))
			self.sms = False

		return resp


	@staticmethod
	def get_coin_price(coinpair):
		return float(requests.get('https://api.gemini.com/v1/pubticker/{}'.format(coinpair)).json()['last'])


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


	@classmethod
	def get_coin_liquidity(cls, coin, is_overvalued, market_value):
		liquidity = 0
		try:
			resp = requests.get("https://api.gemini.com/v1/book/{}usd".format(coin.lower())).json()
			if is_overvalued:
				bids = resp['bids']
				for b in bids:
					if float(b['price']) <= market_value * cls.percent_buffer:
						return int(liquidity)
					liquidity += float(b['price']) * float(b['amount'])
			else:
				asks = resp['asks']
				for a in asks:
					if float(a['price']) * cls.percent_buffer >= market_value:
						return int(liquidity)
					liquidity += float(a['price']) * float(a['amount'])

			return int(liquidity)
		except:
			return "Unknown"


class GateioTrade(ExchangeTrade):
	def __init__(self, coinpair, arbitraged_exchange, fill_above, limit_above, num_limit_orders, is_extra_aggressive):
		super().__init__(coinpair, arbitraged_exchange, fill_above, limit_above, num_limit_orders, is_extra_aggressive)


	@staticmethod
	def get_coin_price(coinpair):
		coin_gateio = coinpair[0:-3].upper() + '_' + coinpair[-3:].upper() + 'T'
		headers = {'Accept': 'application/json', 'Content-Type': 'application/json'}
		return float(requests.get("https://api.gateio.ws/api/v4/spot/tickers?currency_pair={}".format(coin_gateio),headers=headers).json()[0]['last'])


class CoinbaseproTrade(ExchangeTrade):
	def __init__(self, coinpair, arbitraged_exchange, fill_above, limit_above, num_limit_orders, is_extra_aggressive):
		super().__init__(coinpair, arbitraged_exchange, fill_above, limit_above, num_limit_orders, is_extra_aggressive)


	@staticmethod
	def get_coin_price(coinpair):
		coin_coinbase = coinpair[0:-3].upper() + '-' + coinpair[-3:].upper()
		return float(requests.get("https://api.pro.coinbase.com/products/{}/ticker".format(coin_coinbase)).json()['price'])


class KucoinTrade(ExchangeTrade):
	def __init__(self, coinpair, arbitraged_exchange, fill_above, limit_above, num_limit_orders, is_extra_aggressive):
		super().__init__(coinpair, arbitraged_exchange, fill_above, limit_above, num_limit_orders, is_extra_aggressive)


	@staticmethod
	def get_coin_price(coinpair):
		coinpair = coinpair.split("usd")[0].upper() + "-USDT"
		return float(requests.get("https://api.kucoin.com/api/v1/market/orderbook/level1?symbol={}".format(coinpair)).json()['data']['price'])


class KrakenTrade(ExchangeTrade):
	def __init__(self, coinpair, arbitraged_exchange, fill_above, limit_above, num_limit_orders, is_extra_aggressive):
		super().__init__(coinpair, arbitraged_exchange, fill_above, limit_above, num_limit_orders, is_extra_aggressive)


	@staticmethod
	def get_coin_price(coinpair):
		coinpair = coinpair.split("usd")[0].upper()
		resp = requests.get('https://api.kraken.com/0/public/Ticker?pair={}USD'.format(coinpair)).json()
		try:
			resp = resp['result']
			return float(resp[list(resp.keys())[0]]['a'][0])
		except:
			return -1


"""a = Gemini()
b = Gateio()
c = Kucoin()
d = Coinbasepro()
e = Kraken()

print(a.get_coin_price("btcusd"))
print(b.get_coin_price("btcusd"))
print(c.get_coin_price("btcusd"))
print(d.get_coin_price("btcusd"))
print(e.get_coin_price("btcusd"))"""
#a = KucoinTrade("btcusd","gateio")
#print(a.get_coin_price_arbitraged_exchange())
#a.get_coin_price_arbitraged_exchange()
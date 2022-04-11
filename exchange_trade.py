import requests
import math
import time
import json
import base64
import hmac
import hashlib
import sys
import traceback
import re
from random import uniform
import cbpro
import SMS
import api_keys


#Effectively abstract
class ExchangeTrade:
	def __init__(self, coinpair, arbitraged_exchange, fill_above, limit_above, num_limit_orders, is_extra_aggressive):
		self.coinpair = coinpair 			#"btcusd"
		self.arbitraged_exchange = arbitraged_exchange
		self.fill_above = fill_above
		self.limit_above = limit_above
		self.num_limit_orders = num_limit_orders
		self.is_extra_aggressive = is_extra_aggressive
		self.quote_increment_price = None
		self.quote_increment_quantity = None
		self.min_order_size = None
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


	def get_exchange(self):
		return self.__class__.__name__.split("Trade")[0].lower()


	def round_coin_quantity(self,quantity=None):
		if not quantity:
			self.my_coin_quantity = round(self.my_coin_quantity,round(math.log(1/self.quote_increment_quantity,10)))
		else:
			return round(quantity,round(math.log(1/self.quote_increment_quantity,10)))


	def round_coin_price(self,price):
		return round(price,round(math.log(1/self.quote_increment_price,10)))


	def get_coin_price_arbitraged_exchange(self):
		self.coin_price = getattr(self.exchanges[self.arbitraged_exchange],"get_coin_price")(self.coinpair)


	def return_order_price(self,order):
		exchange_dict = {'gemini':'price','coinbasepro':0}
		return float(order[exchange_dict[self.get_exchange()]])


	def return_order_quantity(self,order):
		exchange_dict = {'gemini':'amount','coinbasepro':1} 
		return float(order[exchange_dict[self.get_exchange()]])


	"""def return_sold_quantity(self,sell_order):
		exchange_dict = {'gemini':'amount','coinbasepro':1}"""


	#Fills bids above EXCHANGE coin_price * FILL_ORDER_PERCENT
	def fill_bids(self):
		for order in self.coinpair_orderbook['bids']:
			price,amount = self.return_order_price(order),self.return_order_quantity(order)
			if price >= self.coin_price * self.fill_above:
				if amount > self.min_order_size + self.quote_increment_quantity:
					if self.my_coin_quantity < amount:
						if len(self.my_orderbook):
							print("cancelling orders for {} on exchange {}, current quantity = {}".format(self.coinpair,self.get_exchange(),self.my_coin_quantity))
							self.cancel_orders()
							time.sleep(.5)

						if self.my_coin_quantity < self.min_order_size + self.quote_increment_quantity:
							if self.sms2:
								SMS.send("{} arbitrage available on {} but you have 0 left".format(self.coinpair,self.get_exchange()))
								self.sms2 = False
								print("out of coin {} on exchange {}".format(self.coinpair,self.get_exchange()))
							return
					
					sell_quantity = min(self.round_coin_quantity(amount-self.quote_increment_quantity),self.my_coin_quantity)
					if sell_quantity == 0:
						print("sell quantity == 0")
						print(amount-self.quote_increment_quantity, self.min_order_size + self.quote_increment_quantity)
						continue

					print("sending request to sell {} {} on {} at price {}".format(sell_quantity,self.coinpair,self.get_exchange(),price))
					try:
						sell_order = self.sell_coins(sell_quantity,price)
						if sell_order == 'gemini blocked':
							time.sleep(30)
							return
						#self.my_coin_quantity -= float(sell_order['executed_amount'])
						#self.round_coin_quantity()
						print("sold {} {} on {} at price {}".format(sell_order['executed_amount'],self.coinpair.replace("usd","").upper(),self.get_exchange(), sell_order['price']))
						if self.sms and sell_quantity > 50/self.coin_price:
							SMS.send("sold {} {} on {} at price {}".format(sell_order['executed_amount'],self.coinpair.replace("usd","").upper(),self.get_exchange(), sell_order['price']))
							self.sms = False
					except:
						print(sell_quantity,sell_order)
			else:
				break


	#return up to LIMIT_ORDER new orders that undercut existing whale asks by smallest price difference possible
	def find_limit_order_values(self):
		count, last_order_price, total = 0,0,0
		new_orders = []
		for order in self.coinpair_orderbook['asks']:
			price,amount = self.return_order_price(order),self.return_order_quantity(order)
			if str(price) not in self.my_orderbook_prices:
				total += amount * price
			else:
				continue

			if price <= self.limit_above * self.coin_price or (last_order_price and price <= last_order_price * 1.005):
				continue

			if (amount >= 150/self.coin_price or (self.is_stablecoin and amount >= 50)) or (total >= 200/self.coin_price and amount >= 20/self.coin_price):
				new_orders.append(self.round_coin_price(price-self.quote_increment_price))
				total = 0
				count += 1
				if count >= self.num_limit_orders:
					break

		if len(new_orders) == 0:
			new_orders.append(self.round_coin_price(self.limit_above * self.coin_price))

		return new_orders


	#creates LIMIT_ORDERS number of new limit orders
	def replace_current_orders(self,new_orders):
		if not self.is_stablecoin:
			lowerbound, upperbound = 4200/self.coin_price, 5900/self.coin_price
		else:
			lowerbound, upperbound = 9300/self.coin_price, 13200/self.coin_price

		self.cancel_orders(new_orders)

		if self.my_coin_quantity == 0:
			return

		for i in range(len(new_orders)):
			if new_orders[i] not in [float(x) for x in self.my_orderbook_prices]:
				sell_quantity = self.round_coin_quantity(min(uniform(lowerbound,upperbound),self.my_coin_quantity))
				self.sell_coins(sell_quantity,new_orders[i])
				#self.my_coin_quantity -= sell_quantity
				#self.round_coin_quantity()
		
		if self.is_extra_aggressive and self.my_coin_quantity >= 2*self.min_order_size:
			sell_quantity = self.round_coin_quantity(min(uniform(lowerbound,upperbound),self.my_coin_quantity))
			time.sleep(.1)
			self.sell_coins(sell_quantity, self.round_coin_price(new_orders[0] - 2*self.quote_increment_price))
			#self.my_coin_quantity -= sell_quantity
			#self.round_coin_quantity(


class GeminiTrade(ExchangeTrade):
	def __init__(self, coinpair, arbitraged_exchange, fill_above, limit_above, num_limit_orders, is_extra_aggressive):
		super().__init__(coinpair, arbitraged_exchange, fill_above, limit_above, num_limit_orders, is_extra_aggressive)
		

	def get_coinpair_details(self):
		try:
			coin_details = requests.get("https://api.gemini.com/v1/symbols/details/{}".format(self.coinpair)).json()
			self.quote_increment_price = float(coin_details['quote_increment'])
			self.quote_increment_quantity = float(coin_details['tick_size'])
			self.min_order_size =  float(coin_details['min_order_size'])
			if coin_details['status'] == 'closed':
				print("broken coin {} on gemini ---- exiting".format(self.coinpair))
				exit(0)
		except:
			print("cannot get status for coin {} on exchange {} ---- exiting".format(self.coinpair,self.get_exchange()))
			exit(0)


	def get_coinpair_orderbook(self):
		try:
			self.coinpair_orderbook = requests.get("https://api.gemini.com/v1/book/{}".format(self.coinpair)).json()
		except:
			print("cant find {} orderbook on gemini".format(self.coinpair))

	
	def get_coin_quantity(self):
		try:
			my_coin_quantities = self.request_api('balances',0,0)
			for coin_quantity in my_coin_quantities:
				if coin_quantity['currency'] == self.coinpair.replace("usd", "").upper():
					self.my_coin_quantity = float(coin_quantity['available']) - self.quote_increment_quantity
					self.round_coin_quantity()
					return 1
			self.my_coin_quantity = 0
			return 1
		except:
			print("can't find coin quantity {} on {}".format(self.coinpair,self.get_exchange()))
			self.my_coin_quantity = 0
			return 0	


	def get_my_orders(self):
		try:
			my_orderbook = self.request_api('orders',0,0)			
			self.my_orderbook = [o for o in my_orderbook if o['symbol'] == self.coinpair and o['side'] == 'sell']
			self.my_orderbook.sort(key=lambda x : float(x['price']))
			self.my_orderbook_prices = [o['price'] for o in self.my_orderbook]
		except:
			print("cant find {} orderbook on {}".format(self.coinpair, self.get_exchange()))
			return 0
		return 1	


	def cancel_orders(self, dont_cancel=[]):
		for i in range(len(self.my_orderbook)):
			if float(self.my_orderbook_prices[i]) not in dont_cancel:
				self.request_api('order/cancel',self.my_orderbook[i]['order_id'],0)
				self.my_coin_quantity += float(self.my_orderbook[i]['remaining_amount'])

		self.round_coin_quantity()


	def buy_coins(self,quantity,price):
		return self.request_api('order/new',0,[quantity,price])


	def sell_coins(self,quantity,price):
		req = self.request_api('order/new',0,[-quantity,price])
		self.my_coin_quantity -= quantity
		self.round_coin_quantity()
		return req


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
			order[0] = str(abs(float(order[0])))
			if float(order[0]) == 0:
				return -1
			payload['symbol'], payload['side'], payload['type'] = self.coinpair, ordertype, 'exchange limit'
			payload['amount'], payload['price'] = order[0], order[1]
			if float(payload['price']) <= float(self.coinpair_orderbook['bids'][0]['price']) and ordertype == 'sell':
				payload['options'] = ["immediate-or-cancel"]
				
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
				return 'gemini blocked'

		return resp


	def correct_price(self):
		if self.coinpair_orderbook['asks'][0]['price'] in self.my_orderbook_prices:
			if float(requests.get('https://api.gemini.com/v1/pubticker/{}'.format(trade.coinpair)).json()['last']) >= self.coin_price * self.fill_bids:
				self.sell_coins(.1,.99)


	@staticmethod
	def get_coin_price(coinpair):
		return float(requests.get('https://api.gemini.com/v1/pubticker/{}'.format(coinpair)).json()['last'])


class GateioTrade(ExchangeTrade):
	def __init__(self, coinpair, arbitraged_exchange, fill_above, limit_above, num_limit_orders, is_extra_aggressive):
		super().__init__(coinpair, arbitraged_exchange, fill_above, limit_above, num_limit_orders, is_extra_aggressive)


	@staticmethod
	def get_coin_price(coinpair):
		coin_gateio = coinpair[0:-3].upper() + '_' + coinpair[-3:].upper() + 'T'
		headers = {'Accept': 'application/json', 'Content-Type': 'application/json'}
		req = requests.get("https://api.gateio.ws/api/v4/spot/tickers?currency_pair={}".format(coin_gateio),headers=headers).json()[0]
		return float(req['lowest_ask'])


	def gen_sign(method, url, query_string=None, payload_string=None):
	    key = api_keys.gateio_key       
	    secret = api_keys.gateio_secret
	    t = time.time()
	    m = hashlib.sha512()
	    m.update((payload_string or "").encode('utf-8'))
	    hashed_payload = m.hexdigest()
	    s = '%s\n%s\n%s\n%s\n%s' % (method, url, query_string or "", hashed_payload, t)
	    sign = hmac.new(secret.encode('utf-8'), s.encode('utf-8'), hashlib.sha512).hexdigest()
	    return {'KEY': key, 'Timestamp': str(t), 'SIGN': sign}


	@classmethod
	def transfer_coins(cls, coin, quantity, address):
		host = "https://api.gateio.ws"
		prefix = "/api/v4"
		headers = {'Accept': 'application/json', 'Content-Type': 'application/json'}
		url = '/withdrawals'
		query_param = ''
		body = '{"currency":"'+coin+'","address":"'+address+'","amount":"'+quantity+'","memo":"","chain":"ETH"}'
		# for `gen_sign` implementation, refer to section `Authentication` above
		sign_headers = cls.gen_sign('POST', prefix + url, query_param, body)
		headers.update(sign_headers)
		r = requests.request('POST', host + prefix + url, headers=headers, data=body)
		print(r.json())


class CoinbaseproTrade(ExchangeTrade):
	def __init__(self, coinpair, arbitraged_exchange, fill_above, limit_above, num_limit_orders, is_extra_aggressive):
		super().__init__(coinpair, arbitraged_exchange, fill_above, limit_above, num_limit_orders, is_extra_aggressive)
		self.public_client = cbpro.PublicClient()
		self.auth_client = cbpro.AuthenticatedClient(api_keys.coinbasepro_key,api_keys.coinbasepro_secret,api_keys.coinbasepro_passphrase)
		self.account = self.get_account()


	def formatted_coinpair(self):
		return self.coinpair[0:-3].upper() + '-' + self.coinpair[-3:].upper()


	def get_coinpair_status(self):
		url = "https://api.exchange.coinbase.com/currencies/{}".format(self.formatted_coinpair().split("-")[0])
		coin_status = requests.request("GET", url, headers={"Accept": "application/json"}).json()
		if coin_status['status'] != 'online':
			print("broken coin {} on coinbasepro ---- exiting".format(self.coinpair))
			exit(0)


	def get_coinpair_details(self):
		try:
			url = "https://api.exchange.coinbase.com/products/{}".format(self.formatted_coinpair())
			coin_details = requests.request("GET", url, headers={"Accept": "application/json"}).json()
			self.quote_increment_price = float(coin_details["quote_increment"])
			self.quote_increment_quantity = float(coin_details['base_increment'])
			self.min_order_size =  float(coin_details['base_min_size'])
			self.get_coinpair_status()
			
		except:
			print("cannot get status for coin {} on exchange {} ---- exiting".format(self.coinpair,self.get_exchange()))
			exit(0)


	def get_account(self):
		try:
			accounts = self.auth_client.get_accounts()
			for account in accounts:
				if account['currency'] == self.formatted_coinpair().split('-')[0]:
					return account['id']
		except:
			pass
		print("cant find account on coinbasepro")
		return None


	def get_coin_quantity(self):
		try:
			self.my_coin_quantity = float(self.auth_client.get_account(self.account)['available']) - self.quote_increment_quantity
			self.round_coin_quantity()
			return 1
		except:
			print("can't find coin quantity {} on {}".format(self.coinpair,self.get_exchange()))
			self.my_coin_quantity = 0
			return 0
		

	def get_my_orders(self):
		try:
			my_orderbook = list(self.auth_client.get_orders(product_id=self.formatted_coinpair()))
			self.my_orderbook = [o for o in my_orderbook if o['side'] == 'sell']
			self.my_orderbook.sort(key=lambda x : float(x['price']))
			self.my_orderbook_prices = [o['price'] for o in self.my_orderbook]
			return 1
		except:
			print("cant find {} orderbook on {}".format(self.coinpair, self.get_exchange()))
			return 0


	def cancel_orders(self, dont_cancel=[]):
		for i in range(len(self.my_orderbook)):
			if float(self.my_orderbook_prices[i]) not in dont_cancel:
				self.auth_client.cancel_order(self.my_orderbook[i]['id'])
				self.my_coin_quantity += float(self.my_orderbook[i]['size']) - float(self.my_orderbook[i]['filled_size'])
		self.round_coin_quantity()


	def get_coinpair_orderbook(self):
		try:
			self.coinpair_orderbook = self.public_client.get_product_order_book(self.formatted_coinpair(),level=3)
		except:
			print("couldnt get coinbasepro orderbook for coin {}".format(self.coinpair))


	def buy_coins(self,quantity,price):
		return self.auth_client.buy(price=price, size=quantity, order_type='limit', product_id=self.formatted_coinpair())


	def sell_coins(self,quantity,price):
		sell_order = self.auth_client.sell(price=price, size=quantity, order_type='limit', product_id=self.formatted_coinpair())
		if 'size' in sell_order.keys():
			sell_order['executed_amount'] = sell_order['size']
			self.my_coin_quantity -= quantity
			self.round_coin_quantity()
		else:
			self.get_coin_quantity()
		return sell_order


	def transfer_coins(self,quantity,address):
		pass


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
#print(GateioTrade.transfer_coins("CRPT","100","0x0408a02D87BD35C8ceE60E8c8429Dd5FaD5ff62"))

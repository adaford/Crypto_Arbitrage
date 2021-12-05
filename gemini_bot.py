import sys
import requests
import json
import base64
import hmac
import hashlib
import datetime, time
from random import randint
import math
import SMS



FILL_ORDER_PERCENT = float(sys.argv[1])  #5% for filling an existing bid
PERCENT_GAIN_LIMIT_ORDER = float(sys.argv[2])  #7% minimum gain for limit orders
COIN_PAIR = sys.argv[3]                        #coin to be sold
EXCHANGE = sys.argv[4]         				   #exchange to compare gemini price of coin to
LIMIT_ORDERS = int(sys.argv[5])

def send_request_gemini(req,order_id,sell_quantity):
	global sms
	global time_counter
	url = "https://api.gemini.com/v1/{}".format(req)
	gemini_api_key = your_api_key
	gemini_api_secret = your_secret_api.encode()

	t = datetime.datetime.now()
	time_counter += 1
	payload_nonce =  str(int(time.mktime(t.timetuple())*100000 + time_counter))
	
	payload =  {"request": "/v1/{}".format(req), "nonce": payload_nonce, "account" : ['primary']}

	if order_id:
		payload['order_id'] = order_id
	elif sell_quantity:
		payload['symbol'], payload['side'], payload['type'], payload['options'] = COIN_PAIR, 'sell', 'exchange limit', ["maker-or-cancel"]
		payload['amount'], payload['price'] = sell_quantity[0], sell_quantity[1]
		if float(payload['price']) < float(public_coinpair_orderbook_gemini['asks'][0]['price']):
			payload['options'] = ["immediate-or-cancel"]
			print("sold {} at {} at time {}".format(sell_quantity[0],sell_quantity[1],time.strftime("%H:%M:%S", time.localtime())))

	encoded_payload = json.dumps(payload).encode()
	b64 = base64.b64encode(encoded_payload)
	signature = hmac.new(gemini_api_secret, b64, hashlib.sha384).hexdigest()

	request_headers = {
	    'Content-Type': "text/plain",
	    'Content-Length': "0",
	    'X-GEMINI-APIKEY': gemini_api_key,
	    'X-GEMINI-PAYLOAD': b64,
	    'X-GEMINI-SIGNATURE': signature,
	    'Cache-Control': "no-cache"
	    }

	try:
		response = requests.post(url, headers=request_headers)
	except:
		print("bad response")
		print(response.json())

	my_trades = response.json()

	if sell_quantity and payload['options'] == ["immediate-or-cancel"] and sms:
		SMS.send("sold {} {} at price {}".format(my_trades['executed_amount'], COIN_PAIR.replace("usd","").upper(), my_trades['price']))
		sms = False

	return my_trades


def get_coinpair_orderbook_gemini():
	try:
		coinpair_orderbook = requests.get("https://api.gemini.com/v1/book/{}".format(COIN_PAIR)).json()
	except:
		coinpair_orderbook = 0

	if not coinpair_orderbook:
		print("cant find {} orderbook on gemini".format(COIN_PAIR))
		exit(0)

	return coinpair_orderbook


def get_coinpair_price():
	if EXCHANGE == "coinbase":
		coin_coinbase = COIN_PAIR[0:-3].upper() + '-' + COIN_PAIR[-3:].upper()
		try:
			coin_price_coinbase = requests.get("https://api.pro.coinbase.com/products/{}/ticker".format(coin_coinbase)).json()['price']
		except:
			coin_price_coinbase = 0

		if not coin_price_coinbase:
			print("cant find {} price on coinbase".format(COIN_PAIR))
			exit(0)

		return float(coin_price_coinbase)

	if EXCHANGE == "gateio":
		coin_gateio = COIN_PAIR[0:-3].upper() + '_' + COIN_PAIR[-3:].upper() + 'T'
		try:
			headers = {'Accept': 'application/json', 'Content-Type': 'application/json'}
			coin_price_gateio = requests.get("https://api.gateio.ws/api/v4/spot/tickers?currency_pair={}".format(coin_gateio),headers=headers).json()[0]['last']
		except:
			coin_price_gateio = 0

		if not coin_price_gateio:
			print("cant find {} price on gateio".format(COIN_PAIR))
			exit(0)

		return float(coin_price_gateio)


#replaces lowest 2 orders and keeps top 3 if they are same price as existing in my_order_book
def replace_current_orders(new_orders):
	lowerbound, upperbound = int(1600/coin_price), int(3500/coin_price)
	#print(lowerbound, upperbound)
	for i in range(len(new_orders)):
		if str(new_orders[i]) in my_order_prices:
			continue
		if my_order_prices.count(str(new_orders[i])) < 2:
			sell_quantity = randint(lowerbound,upperbound)
			send_request_gemini('order/new',0,[str(min(sell_quantity,my_coin_quantity)),new_orders[i]])
		if i < len(my_order_book):
			send_request_gemini('order/cancel',my_order_book[i]['order_id'],0)


#return up to 3 new orders that undercut
def penny_pinch():
	#print("start penny pinch")
	count, last_order_price, total, my_total = 0,0,0,0
	new_orders = []

	for o in public_coinpair_orderbook_gemini['asks']:
		total += float(o['amount'])

		if float(o['price']) <= PERCENT_GAIN_LIMIT_ORDER * coin_price or (last_order_price and (float(o['price'])) <= last_order_price * 1.005):
			continue

		if o['price'] in my_order_prices:
			my_total += float(o['amount'])
			continue

		if float(o['amount']) >= 500/coin_price or (total - my_total >= 500/coin_price and count==0):
			if count >= 3:
				break
			last_order_price = float(o['price'])
			new_orders.append(last_order_price-decimal_increment)
			count += 1

	return new_orders


def fill_high_order():
	global sms
	global my_coin_quantity
	for order in public_coinpair_orderbook_gemini['bids']:
		if float(order['price']) >= coin_price * FILL_ORDER_PERCENT:
			if float(order['amount']) > .1:
				if my_coin_quantity < float(order['amount']):
					if len(my_order_book):
						print("cancelling orders for {}".format(COIN_PAIR))
						for i in len(my_order_book):
							send_request_gemini('order/cancel',my_order_book[i]['order_id'],0)
						time.sleep(.25)
						my_coin_quantity = get_coin_quantity()
					elif sms:
						SMS.send(COIN_PAIR + " arbitrage available on Gemini but you have 0 left")
						sms = False
						return
				print("sending request to fill at price {}".format(order['price']))
				send_request_gemini('order/new',0,[min(round(float(order['amount'])-decimal_increment,decimal_increment_round),my_coin_quantity),order['price']])
				
		else:
			break


def get_coin_quantity():
	my_coin_quantities = send_request_gemini('balances',0,0)
	for q in my_coin_quantities:
		if q['currency'] == COIN_PAIR.replace("usd", "").upper():
			return round(float(q['available']),decimal_increment_round)
	print("can't find coin quantity")


def get_coin_decimal_increment():
	return float(requests.get("https://api.gemini.com/v1/symbols/details/{}".format(COIN_PAIR)).json()['quote_increment'])


if __name__ == "__main__":
	count,time_counter = 0,0
	sms = True
	decimal_increment = get_coin_decimal_increment()
	decimal_increment_round = round(math.log(1/decimal_increment,10))

	while 1:
		try:
			my_coin_quantity = get_coin_quantity()
			public_coinpair_orderbook_gemini = get_coinpair_orderbook_gemini()
			coin_price = get_coinpair_price()

			fill_high_order()

			if LIMIT_ORDERS:
				my_order_book = send_request_gemini('orders',0,0)
				my_order_book = [o for o in my_order_book if o['symbol'] == COIN_PAIR]
				my_order_book.sort(key=lambda x : x['price'])
				my_order_prices = [o['price'] for o in my_order_book]

				replace_current_orders(penny_pinch())

			time.sleep(1)
			count += 1
			if count % 400 == 0:
				print("count: {} still running".format(count))
				sms = True
			#break

		except:
			print("{} bugged out somewhere timecounter: {}".format(COIN_PAIR, time.asctime(time.localtime())))
			#exit(0)

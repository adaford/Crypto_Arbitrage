"""                         **********BOT FOR TRADING KNC ON GEMINI **************
	Goes through the asks orderbook and undercuts each whale sell by a fraction of a penny and replaces all current sell order.
	Also will fill any order 10% above market value that is in the bids """

import requests
import json
import base64
import hmac
import hashlib
import datetime, time
from random import randint
import math


time_counter = 0

PERCENT_GAIN_LIMIT_ORDER = 1.07  #7% minimum gain for limit orders
FILL_ORDER_PERCENT = 1.05  #5% for filling an existing bid

def send_request_gemini(req,order_id,sell_quantity):
	url = "https://api.gemini.com/v1/{}".format(req)
	gemini_api_key = 'yours'
	gemini_api_secret = 'yours'.encode()

	t = datetime.datetime.now()
	global time_counter
	payload_nonce =  str(int(time.mktime(t.timetuple())*1000 + time_counter))
	time_counter += 1

	payload =  {"request": "/v1/{}".format(req), "nonce": payload_nonce, "account" : ['primary']}

	if order_id:
		payload['order_id'] = order_id
	elif sell_quantity:
		payload['symbol'], payload['side'], payload['type'], payload['options'] = 'kncusd', 'sell', 'exchange limit', ["maker-or-cancel"]
		payload['amount'], payload['price'] = sell_quantity[0], sell_quantity[1]
		if float(payload['price']) < float(public_knc_orderbook['asks'][0]['price'])-.0001:
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

	response = requests.post(url, headers=request_headers)
	my_trades = response.json()

	if sell_quantity:
		 #print("sell order for {} knc placed at price {}".format(sell_quantity[0],sell_quantity[1]))
		 return (my_trades)
	if order_id:
		 #print("sell order {} cancelled".format(order_id))
		 return my_trades

	return my_trades


def get_knc_orderbook_gemini():
	try:
		knc_orderbook = requests.get("https://api.gemini.com/v1/book/kncusd").json()
	except:
		knc_orderbook = 0

	if not knc_orderbook:
		print("cant find knc orders")
		exit(0)


	return knc_orderbook

def get_knc_price_coinbase():
	try:
		knc_price = requests.get("https://api.pro.coinbase.com/products/KNC-USD/ticker").json()['price']
	except:
		knc_price = 0

	if not knc_price:
		print("cant find knc price coinbase")
		exit(0)

	return float(knc_price)


#replaces lowest 2 orders and keeps top 3 if they are same price as existing in my_order_book
def replace_current_orders(new_orders):
	for i in range(len(new_orders)):
		if i > 0 and str(new_orders[i]) in my_order_prices:
			continue
		if my_order_prices.count(str(new_orders[i])) < 2:
			send_request_gemini('order/new',0,[str(randint(1200,2200)),new_orders[i]])
		send_request_gemini('order/cancel',my_order_book[i]['order_id'],0)


#return up to 5 new orders that undercut
def penny_pinch():
	#print("start penny pinch")
	count, last_order_price, total, my_total = 0,0,0,0
	new_orders = []

	for o in public_knc_orderbook['asks']:
		total += float(o['amount'])

		if float(o['price']) <= PERCENT_GAIN_LIMIT_ORDER * knc_price_coinbase or (last_order_price and (float(o['price'])) <= last_order_price * 1.005):
			continue

		if o['price'] in my_order_prices:
			my_total += float(o['amount'])
			continue

		if float(o['amount']) >= 300 or (total - my_total >= 500 and count==0):
			if count >= 5:
				break
			last_order_price = float(o['price'])
			new_orders.append(round(last_order_price - .0001,5))
			count += 1

	return new_orders


def fill_high_order():
	for order in public_knc_orderbook['bids']:
		if float(order['price']) >= knc_price_coinbase * FILL_ORDER_PERCENT:
			print("sending request to fill at price {}".format(order['price']))
			send_request_gemini('order/new',0,[math.floor(float(order['amount'])),order['price']])
		else:
			break


if __name__ == "__main__":
	while 1:
		try:
			public_knc_orderbook = get_knc_orderbook_gemini()
			knc_price_coinbase = get_knc_price_coinbase()

			fill_high_order()

			my_order_book = send_request_gemini('orders',0,0)
			my_order_book = [o for o in my_order_book if o['symbol'] == 'kncusd']
			my_order_book.sort(key=lambda x : x['price'])
			my_order_prices = [o['price'] for o in my_order_book]

			replace_current_orders(penny_pinch())

			time.sleep(1)
			if time_counter % 1000 == 0:
				print("time counter: {} still running".format(time_counter))
			#break
		except:
			print("bugged out somewhere")
			#exit(0)

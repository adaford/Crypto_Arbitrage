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
import traceback


def send_request_gemini(req,order_id,sell_quantity):
	global sms
	url = "https://api.gemini.com/v1/{}".format(req)
	gemini_api_key = 'yourapikey'
	gemini_api_secret = 'yourapisecret'.encode()

	payload_nonce =  str(time.time()*100000)
	
	payload =  {"request": "/v1/{}".format(req), "nonce": payload_nonce, "account" : ['primary']}
	if order_id:
		payload['order_id'] = order_id
	elif sell_quantity:
		sell_quantity[0] = str(round(float(sell_quantity[0]),decimal_increment_round))
		if float(sell_quantity[0]) == 0:
			return
		payload['symbol'], payload['side'], payload['type'] = COIN_PAIR, 'sell', 'exchange limit'
		payload['amount'], payload['price'] = sell_quantity[0], sell_quantity[1]
		if float(payload['price']) <= float(public_coinpair_orderbook_gemini['bids'][0]['price']):
			payload['options'] = ["immediate-or-cancel"]
			print("sold {} {} at price {} at time {}".format(sell_quantity[0],COIN_PAIR.replace("usd","").upper(),sell_quantity[1],time.strftime("%H:%M:%S", time.localtime())))

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
		my_trades = response.json()

	except:
		print("bad response on url: {} with payload {}".format(url,payload))
		return 0

	if 'options' in payload and 'executed_amount' in my_trades and float(my_trades['executed_amount']) == 0:
		print("Gemini stopped sell")
		time.sleep(30)

	if sell_quantity and 'options' in payload.keys() and 'executed_amount' in my_trades and float(my_trades['executed_amount']) >= 50/coin_price and sms and not (STABLECOIN and my_trades['executed_amount']) == '0.1':
		SMS.send("sold {} {} at price {}".format(my_trades['executed_amount'], COIN_PAIR.replace("usd","").upper(), my_trades['price']))
		sms = False

	return my_trades


#Return my coin quantity
def get_coin_quantity():
	my_coin_quantities = send_request_gemini('balances',0,0)
	if not my_coin_quantities or type(my_coin_quantities) is not list:
		print("can't find coin quantity {}".format(COIN_PAIR))
		return -1

	for q in my_coin_quantities:
		if q['currency'] == COIN_PAIR.replace("usd", "").upper():
			return max(round(float(q['available']) - decimal_increment, decimal_increment_round),0)

	print("can't find coin quantity {}".format(COIN_PAIR))
	return -1


def get_coinpair_orderbook_gemini():
	try:
		coinpair_orderbook = requests.get("https://api.gemini.com/v1/book/{}".format(COIN_PAIR)).json()
	except:
		coinpair_orderbook = 0
		print("cant find {} orderbook on gemini".format(COIN_PAIR))

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

		return float(coin_price_gateio)


def cancel_orders(new_orders):
	global my_coin_quantity
	for i in range(len(my_order_book)):
		if float(my_order_prices[i]) not in new_orders:
			send_request_gemini('order/cancel',my_order_book[i]['order_id'],0)
			my_coin_quantity += float(my_order_book[i]['remaining_amount'])

	my_coin_quantity = round(my_coin_quantity,decimal_increment_round)


def get_my_orders():
	global my_order_book
	global my_order_prices
	my_order_book = send_request_gemini('orders',0,0)
	if my_order_book == 0 or type(my_order_book) != list:
		print("cant find {} orderbook".format(COIN_PAIR))
		return -1
	my_order_book = [o for o in my_order_book if o['symbol'] == COIN_PAIR and o['side'] == 'sell']
	my_order_book.sort(key=lambda x : float(x['price']))
	my_order_prices = [o['price'] for o in my_order_book]
	return 1


#creates LIMIT_ORDERS number of new limit orders           #BUG - if out of coins and existing order in then it wont have coins to create first order
def replace_current_orders(new_orders):
	global my_coin_quantity
	if not STABLECOIN:
		lowerbound, upperbound = int(4200/coin_price), int(5900/coin_price)
	else:
		lowerbound, upperbound = int(9300/coin_price), int(13200/coin_price)


	cancel_orders(new_orders)

	if my_coin_quantity == 0:
		return

	for i in range(len(new_orders)):
		if new_orders[i] not in [float(x) for x in my_order_prices]:
			sell_quantity = randint(lowerbound,upperbound)
			send_request_gemini('order/new',0,[str(min(sell_quantity,my_coin_quantity)),new_orders[i]])
			my_coin_quantity = round(my_coin_quantity - min(sell_quantity,my_coin_quantity), decimal_increment_round) 
	
	if EXTRA_ORDER:
		sell_quantity = randint(lowerbound,upperbound)
		time.sleep(.1)
		send_request_gemini('order/new',0,[str(min(sell_quantity,my_coin_quantity)),new_orders[i]-2*decimal_increment])


#return up to LIMIT_ORDER new orders that undercut existing whale asks by smallest price difference possible
def penny_pinch():
	count, last_order_price, total = 0,0,0
	new_orders = []
	for o in public_coinpair_orderbook_gemini['asks']:
		if o['price'] not in my_order_prices:
			total += float(o['amount']) * float(o['price'])
		else:
			continue

		if float(o['price']) <= PERCENT_GAIN_LIMIT_ORDER * coin_price or (last_order_price and (float(o['price'])) <= last_order_price * 1.005):
			continue

		if (float(o['amount']) >= 150/coin_price or (STABLECOIN and float(o['amount']) >= 50)) or (total >= 200/coin_price and float(o['amount']) >= 20/coin_price):
			new_orders.append(round(float(o['price'])-decimal_increment, decimal_increment_round))
			total = 0
			count += 1
			if count >= LIMIT_ORDERS:
				break

	if len(new_orders) == 0:
		new_orders.append(round(float(public_coinpair_orderbook_gemini['asks'][-1]['price']) - decimal_increment, decimal_increment_round))

	return new_orders


#Fills bids above EXCHANGE coin_price * FILL_ORDER_PERCENT
def fill_high_orders():
	global sms2
	global my_coin_quantity

	for order in public_coinpair_orderbook_gemini['bids']:
		if float(order['price']) >= coin_price * FILL_ORDER_PERCENT:
			if float(order['amount']) > min_order_size + decimal_increment:
				if my_coin_quantity < float(order['amount']):
					if len(my_order_book):
						print("cancelling orders for {} quantity = {}".format(COIN_PAIR,str(my_coin_quantity)))
						cancel_orders([])
						time.sleep(.5)
						#my_coin_quantity = get_coin_quantity()
						print("new coin quantity = " + str(my_coin_quantity))

					if my_coin_quantity < round(min_order_size + decimal_increment, decimal_increment_round):
						if sms2:
							SMS.send(COIN_PAIR + " arbitrage available on Gemini but you have 0 left")
							sms2 = False
							print("out of coin {}".format(COIN_PAIR))
						return
				
				print("sending request to fill {} at price {} with coin_quantity: {}".format(min(round(float(order['amount'])-decimal_increment,decimal_increment_round),my_coin_quantity), order['price'], my_coin_quantity))
				my_coin_quantity -= float(send_request_gemini('order/new',0,[min(round(float(order['amount'])-decimal_increment,decimal_increment_round),my_coin_quantity),order['price']])['executed_amount'])

		else:
			break


if __name__ == "__main__":
	FILL_ORDER_PERCENT = float(sys.argv[1])  	   #percent to fill bids at (1.05 = 5% above market value)
	PERCENT_GAIN_LIMIT_ORDER = float(sys.argv[2])  #percent to put limit orders in at
	COIN_PAIR = sys.argv[3]                        #coin to be sold
	EXCHANGE = sys.argv[4]         				   #exchange to compare gemini price of coin to
	LIMIT_ORDERS = int(sys.argv[5])				   #number of limit orders to put in
	EXTRA_ORDER = int(sys.argv[6])

	STABLECOIN = True if FILL_ORDER_PERCENT <= 1.02 else False

	my_order_book, my_order_prices = [], []
	get_my_orders()
	sms,sms2 = True,True
	coin_details = requests.get("https://api.gemini.com/v1/symbols/details/{}".format(COIN_PAIR)).json()
	if coin_details['status'] == 'closed':
		print("coin status down, exiting")
		exit(0)
	decimal_increment, min_order_size = float(coin_details['quote_increment']), float(coin_details['min_order_size'])
	decimal_increment_round = round(math.log(1/decimal_increment,10))

	count = 0
	while 1:
		try:
			my_coin_quantity = get_coin_quantity()
			public_coinpair_orderbook_gemini = get_coinpair_orderbook_gemini()
			coin_price = get_coinpair_price()

			if my_coin_quantity < 0 or not public_coinpair_orderbook_gemini or not coin_price:
				continue

			if LIMIT_ORDERS:
				if get_my_orders() == -1:
					continue

			fill_high_orders()

			if LIMIT_ORDERS:
				replace_current_orders(penny_pinch())

				#Fool Buyers
				if STABLECOIN:
					if public_coinpair_orderbook_gemini['asks'][0]['price'] in my_order_prices:
						last_price = float(requests.get('https://api.gemini.com/v1/pubticker/{}'.format(COIN_PAIR)).json()['last'])
						if last_price >= coin_price * FILL_ORDER_PERCENT:
							send_request_gemini('order/new',0,[.1,.99])

			time.sleep(1)
			count += 1
			if count % 1000 == 0:
				print("count: {} still running {}".format(count,COIN_PAIR))
				sms = True
				sms2 = True
			#break

		except BaseException as err:
			print("{} bugged out, time: {}".format(COIN_PAIR, time.asctime(time.localtime())))
			print(f"Unexpected {err}, {type(err)}")
			print(traceback.format_exc())
			print(public_coinpair_orderbook_gemini)
			#exit(0)

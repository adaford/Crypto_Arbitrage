from collections import Counter
import sys
import json
import math
from collections import Counter
import exchange_request

class ArbitrageHunt:
	count = 0
	EC2_mode = True if len(sys.argv) <= 2 else False
	GATEIO_PATH = '/home/ec2-user/script/outputs/gateio_prices.log' if EC2_mode else 'gateio_prices.txt'
	WEBPAGE_OUTPUT_PATH = '/home/ec2-user/script/flaskproject/output_webpage.log' if EC2_mode else 'webpageoutput.log'
	OUTPUT_PATH = '/home/ec2-user/script/outputs/output_' if EC2_mode else 'output_'
	exchange_list = {"kucoin":getattr(exchange_request, "KucoinRequest"),"kraken":getattr(exchange_request, "KrakenRequest"),
	"coinbasepro":getattr(exchange_request, "CoinbaseproRequest"),"gemini":getattr(exchange_request, "GeminiRequest"),"gateio":getattr(exchange_request, "GateioRequest")}


	@classmethod
	def get_liquidity(cls, coin, exchange, is_overvalued, market_value):
		return getattr(cls.exchange_list[exchange.lower()],"get_coin_liquidity")(coin, is_overvalued, market_value)


	@classmethod
	def get_prices(cls, exchange):
		return getattr(cls.exchange_list[exchange.lower()],"get_all_prices")()


	@staticmethod
	def is_leverage_available(coin):
		return exchange_request.KucoinRequest.is_leverage_available(coin)


	@staticmethod
	def add_percentage_sign(coin_list):
		for a in coin_list:
			a[2] = str(a[2]) + '%'
		return coin_list


	@staticmethod
	def remove_coins_on_duplicate_exchanges(coin_list):
		c = Counter()
		to_be_removed = {}
		for coin in coin_list:
			c[coin[0]] += 1

		for coin in c.most_common():
			if coin[1] > 1:
				to_be_removed.add(coin[0])

		return [a for a in coin_list if a[0] not in to_be_removed]


	@staticmethod
	def round_decimal(number):
		return round(number,max(round(math.log(10/number,10)) + 2,2))


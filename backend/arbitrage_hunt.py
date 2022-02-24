from collections import Counter
import sys
import json
import get_exchange_prices
import get_exchange_liquidity
import math
from collections import Counter

class ArbitrageHunt:

	count = 0
	EC2_mode = True if len(sys.argv) <= 2 else False
	GATEIO_PATH = '/home/ec2-user/script/outputs/gateio_prices.log' if EC2_mode else 'gateio_prices.log'
	WEBPAGE_OUTPUT_PATH = '/home/ec2-user/script/flaskproject/output_webpage.log' if EC2_mode else 'webpageoutput.log'
	OUTPUT_PATH = '/home/ec2-user/script/outputs/output_' if EC2_mode else 'output_'
	exchange_list = ["kucoin","kraken","coinbasepro","gemini"]


	def get_liquidity(self,coin,exchange,overvalued,market_value):
		exchange = exchange.upper()
		if exchange == "KRAKEN":
			return get_exchange_liquidity.get_kraken_liquidity(coin,overvalued,market_value)
		elif exchange == "COINBASEPRO":
			return get_exchange_liquidity.get_coinbasepro_liquidity(coin,overvalued,market_value)
		elif exchange == "KUCOIN":
			return get_exchange_liquidity.get_kucoin_liquidity(coin,overvalued,market_value)
		elif exchange == "GEMINI":
			return get_exchange_liquidity.get_gemini_liquidity(coin,overvalued,market_value)
		elif exchange == "GATEIO":
			return get_exchange_liquidity.get_gateio_liquidity(coin,overvalued,market_value)
		"""elif exchange == "FTX":
			return get_exchange_liquidity.get_ftx_liquidity(coin,overvalued,market_value)
		elif exchange == "BITTREX":
			return get_exchange_liquidity.get_bittrex_liquidity(coin,overvalued,market_value)
		elif exchange == "CRYPTO.COM":
			return get_exchange_liquidity.get_cryptodotcom_liquidity(coin,overvalued,market_value)
		elif exchange == "LBANK":
			return get_exchange_liquidity.get_lbank_liquidity(coin,overvalued,market_value)
		elif exchange == "BINANCEUS":
			return get_exchange_liquidity.get_binanceUS_liquidity(coin,overvalued,market_value)"""


	def get_prices(self,exchange):
		exchange = exchange.upper()
		if exchange == "KRAKEN":
			return get_exchange_prices.get_kraken_prices()
		elif exchange == "COINBASEPRO":
			return get_exchange_prices.get_coinbasepro_prices()
		elif exchange == "KUCOIN":
			return get_exchange_prices.get_kucoin_prices()
		elif exchange == "GEMINI":
			return get_exchange_prices.get_gemini_prices()
		elif exchange == "GATEIO":
			return get_exchange_prices.get_gateio_prices()


	def add_percentage_sign(self,coin_list):
		for a in coin_list:
			a[2] = str(a[2]) + '%'
		return coin_list


	def remove_coins_on_duplicate_exchanges(self,coin_list):
		c = Counter()
		to_be_removed = []
		for coin in coin_list:
			c[coin[0]] += 1

		for coin in c.most_common():
			if coin[1] > 1:
				to_be_removed.append(coin[0])

		return [a for a in coin_list if a[0] not in to_be_removed]


	def round_decimal(self,number):
		return round(number,max(round(math.log(10/number,10)) + 2,2))

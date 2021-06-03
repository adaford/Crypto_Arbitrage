from collections import Counter
import sys
import json
import get_exchange_prices
import get_exchange_liquidity


def get_liquidity(coin,exchange,overvalued,market_value):
	if exchange == "KRAKEN":
		return get_exchange_liquidity.get_kraken_liquidity(coin,overvalued,market_value)
	elif exchange == "COINBASEPRO":
		return get_exchange_liquidity.get_coinbasepro_liquidity(coin,overvalued,market_value)
	elif exchange == "BINANCEUS":
		return get_exchange_liquidity.get_binanceUS_liquidity(coin,overvalued,market_value)
	elif exchange == "KUCOIN":
		return get_exchange_liquidity.get_kucoin_liquidity(coin,overvalued,market_value)
	elif exchange == "GEMINI":
		return get_exchange_liquidity.get_gemini_liquidity(coin,overvalued,market_value)
	elif exchange == "BITTREX":
		return get_exchange_liquidity.get_bittrex_liquidity(coin,overvalued,market_value)


def main():
	EC2_mode = True if len(sys.argv) == 1 else False

	COIN_LIST_PATH = '/home/ec2-user/script/coin_list.txt' if EC2_mode else 'coin_list.txt'
	KRAKEN_COIN_LIST_PATH = '/home/ec2-user/script/kraken_coin_list.txt' if EC2_mode else 'kraken_coin_list.txt'
	COINBASEPRO_COIN_LIST_PATH = '/home/ec2-user/script/coinbasepro_coin_list.txt' if EC2_mode else 'coinbasepro_coin_list.txt'
	BINANCEUS_COIN_LIST_PATH =  '/home/ec2-user/script/binanceUS_coin_list.txt' if EC2_mode else 'binanceUS_coin_list.txt'

	PRICE_ALERT_PERCENTAGE = .08 if EC2_mode else float(sys.argv[1]) / 100



	coins, kraken_coins, coinbasepro_coins, binanceUS_coins, alerted_coins = [], [], [], [], []

	with open(COIN_LIST_PATH) as c:
		coins = c.read().splitlines()
	with open(KRAKEN_COIN_LIST_PATH) as c:
		kraken_coins = c.read().splitlines()
	with open(COINBASEPRO_COIN_LIST_PATH) as c:
		coinbasepro_coins = c.read().splitlines()
	with open(BINANCEUS_COIN_LIST_PATH) as c:
		binanceUS_coins = c.read().splitlines()

	for i in range(5):
		try: 
			coinmarketcap_prices = get_exchange_prices.get_prices_coinmarketcap()
			break
		except:
			if i == 4:
				with open('output.log', 'w') as f:
					json.dump([0,0,0,0,0],f)
					print([0,0,0,0,0])
				exit(0)
	kraken_prices = get_exchange_prices.get_kraken_prices(kraken_coins)
	coinbasepro_prices = get_exchange_prices.get_coinbasepro_prices(coinbasepro_coins)
	binanceUS_prices = get_exchange_prices.get_binanceUS_prices(binanceUS_coins)
	kucoin_prices = get_exchange_prices.get_kucoin_prices(coins)
	gemini_prices = get_exchange_prices.get_gemini_prices(coins)
	bittrex_prices = get_exchange_prices.get_bittrex_prices(coins)


	coin_prices = {}
	for coin in coins:
		if coin not in coinmarketcap_prices.keys():
			continue
		if coin in kraken_prices:
			coin_prices[(coin,"KRAKEN")] = kraken_prices[coin]
		if coin in coinbasepro_prices:
			coin_prices[(coin,"COINBASEPRO")] = coinbasepro_prices[coin]
		if coin in binanceUS_prices:
			coin_prices[(coin,"BINANCEUS")] = binanceUS_prices[coin]
		if coin in kucoin_prices:
			coin_prices[(coin,"KUCOIN")] = kucoin_prices[coin]
		if coin in gemini_prices:
			coin_prices[(coin,"GEMINI")] = gemini_prices[coin]
		if coin in bittrex_prices:
			coin_prices[(coin,"BITTREX")] = bittrex_prices[coin]
		

	for c,v in coin_prices.items():
		coin,exchange = c[0],c[1]

		percent_difference = (coinmarketcap_prices[coin] - v) / coinmarketcap_prices[coin] if coinmarketcap_prices[coin] >= v else (coinmarketcap_prices[coin] - v) / v

		if abs(percent_difference) > PRICE_ALERT_PERCENTAGE:
			liquidity = get_liquidity(coin,exchange,percent_difference<0,coinmarketcap_prices[coin])
			alerted_coins.append([coin,exchange,round(-100*percent_difference,2),
				"CoinMarketCap_price: {}".format(round(coinmarketcap_prices[coin],3)),
					"{}_price: {}".format(exchange,round(v,3)), 
					"liquidity: ${}".format(liquidity)])


	alerted_coins.sort(key=lambda x: abs(x[2]), reverse=True)
	for a in alerted_coins:
		a[2] = str(a[2]) + '%'

	with open('output.log', 'w') as f:
		if len(alerted_coins) > 0:
			json.dump(alerted_coins,f)
			for a in alerted_coins:
				print(a)
		else:
			json.dump([0,0,0,0,0],f)
			print([0,0,0,0,0])

main()
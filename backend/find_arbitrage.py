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


def remove_solo_coins(alerted_coin_list):
	only_on_one_exchange = []
	for a in alerted_coin_list:
		a[2] = str(a[2]) + '%'
		c=0
		if a[0] in kraken_prices:
			c+=1
		if a[0] in coinbasepro_prices:
			c+=1
		if a[0] in binanceUS_prices:
			c+=1
		if a[0] in kucoin_prices:
			c+=1
		if a[0] in gemini_prices:
			c+=1
		if a[0] in bittrex_prices:
			c+=1
		if c < 2:
			only_on_one_exchange.append(a)

	for a in only_on_one_exchange:
		alerted_coin_list.remove(a)

	return alerted_coin_list


if __name__ == "__main__":
	EC2_mode = True if len(sys.argv) == 1 else False

	WEBPAGE_OUTPUT_PATH = '/home/ec2-user/script/flaskproject/output_webpage.log' if EC2_mode else 'output.log'
	OUTPUT_PATH = '/home/ec2-user/script/output.log' if EC2_mode else 'output.log'
	BINANCEUS_COIN_LIST_PATH =  '/home/ec2-user/script/binanceUS_coin_list.txt' if EC2_mode else 'binanceUS_coin_list.txt'

	PRICE_ALERT_PERCENTAGE = .1 if EC2_mode else float(sys.argv[1]) / 100

	binanceUS_coins, alerted_coins, alerted_coins_website = [], [], []

	with open(BINANCEUS_COIN_LIST_PATH) as c:
		binanceUS_coins = c.read().splitlines()

	for i in range(5):
		try: 
			coinmarketcap_prices = {k:v for k,v in get_exchange_prices.get_prices_coinmarketcap().items() if 'USD' not in k}
			break
		except:
			if i == 4:
				with open(OUTPUT_PATH, 'w') as f:
					json.dump([[0,0,0,0,0]],f)
					print([0,0,0,0,0])
				exit(0)
	
	coins = [k for k,v in coinmarketcap_prices.items()]

	kraken_prices = get_exchange_prices.get_kraken_prices()
	coinbasepro_prices = get_exchange_prices.get_coinbasepro_prices()
	binanceUS_prices = get_exchange_prices.get_binanceUS_prices(binanceUS_coins)
	kucoin_prices = get_exchange_prices.get_kucoin_prices(coins)
	gemini_prices = get_exchange_prices.get_gemini_prices()
	bittrex_prices = get_exchange_prices.get_bittrex_prices()

	coin_prices = {}
	for coin in coins:
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
		if coinmarketcap_prices[coin] <= 0 or v <= 0:
			print("error for coin {} on {} CoinMarketCap_price: {}".format(coin,exchange,coinmarketcap_prices[coin]))
			continue

		percent_difference = (coinmarketcap_prices[coin] - v) / v if coinmarketcap_prices[coin] >= v else (coinmarketcap_prices[coin] - v) / coinmarketcap_prices[coin]

		if abs(percent_difference) > PRICE_ALERT_PERCENTAGE:
			liquidity = get_liquidity(coin,exchange,percent_difference<0,coinmarketcap_prices[coin])
			if type(liquidity) == str or liquidity < 5000:
				alerted_coins.append([coin,exchange,round(-100*percent_difference,2),
					"CoinMarketCap_price: {}".format(round(coinmarketcap_prices[coin],4)),
						"{}_price: {}".format(exchange,round(v,4)), 
						"liquidity: ${}".format(liquidity)])

		if abs(percent_difference) > .002:
			liquidity = get_liquidity(coin,exchange,percent_difference<0,coinmarketcap_prices[coin])
			if type(liquidity) != str and liquidity == 0:
				continue
			alerted_coins_website.append([coin,exchange,round(-100*percent_difference,2),round(coinmarketcap_prices[coin],4),round(v,4),liquidity])
	
	alerted_coins.sort(key=lambda x: abs(x[2]), reverse=True)
	alerted_coins_website.sort(key=lambda x: abs(x[2]), reverse=True)

	alerted_coins = remove_solo_coins(alerted_coins)
	alerted_coins_website = remove_solo_coins(alerted_coins_website)

	with open(OUTPUT_PATH, 'w') as f:
		if len(alerted_coins) > 0:
			json.dump(alerted_coins,f)
			for a in alerted_coins:
				print(a)
		else:
			json.dump([[0,0,0,0,0]],f)
			print([0,0,0,0,0])

	with open(WEBPAGE_OUTPUT_PATH, 'w') as f:
		if len(alerted_coins_website) > 0:
			json.dump(alerted_coins_website,f)
		else:
			json.dump([[0,0,0,0,0]],f)

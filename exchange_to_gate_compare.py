import traceback
import time
import os
import json
import math
import sys
import SMS
from arbitrage_hunt import ArbitrageHunt as ah


def main():
	exchange = sys.argv[1]
	sms = set()
	PRICE_ALERT_PERCENTAGE = .07 if ah.EC2_mode else float(sys.argv[2]) / 100
	liquidity_limits = 200 if exchange == 'gemini' else 8000
	stablecoins = {'USDT','USDC','UST','DAI','BUSD','GUSD','TUSD','MIM'}
	while 1:
		try:
			alerted_coins, web_coins = [], []
			with open(ah.GATEIO_PATH,'r') as file:
				try:
					gateio_prices = json.loads(file.read())
				except:
					print("cant read gateio file on {}".format(exchange))
					continue
			exchange_prices = ah.get_prices(exchange)

			if type(gateio_prices) != dict or type(exchange_prices) != dict:
				print("{} prices not a dict".format(exchange))
				continue

			for coin in exchange_prices:
				if coin not in gateio_prices.keys():
					continue		
				gateio_price, exchange_price = gateio_prices[coin], exchange_prices[coin]
				if gateio_price <= 0 or exchange_price <= 0:
					#print("error for coin {} on {} Gateio_price: {}".format(coin,exchange_,gateio_price))
					continue

				percent_difference = (gateio_price - exchange_price) / exchange_price if gateio_price >= exchange_price else (gateio_price - exchange_price) / gateio_price
				
				if abs(percent_difference) > .03 or (coin in stablecoins and abs(percent_difference) > .01):
					
					liquidity_exchange = ah.get_liquidity(coin,exchange,percent_difference<0,gateio_price)
					if not liquidity_exchange:
						continue
					liquidity_gate = ah.get_liquidity(coin,"GATEIO",percent_difference>0,exchange_price)
					if not liquidity_gate:
						continue

					exchangeL = exchange.upper()+'+Lev' if exchange == 'kucoin' and ah.is_leverage_available(coin) else exchange.upper()
					
					web_coins.append([coin,exchangeL,round(-100*percent_difference,2),
						"Gateio_price: {}".format(ah.round_decimal(gateio_price)),
							"{}_price: {}".format(exchange,ah.round_decimal(exchange_price)), 
							"liquidity_exchange: ${}".format(liquidity_exchange),
							"liquidity_gate: ${}".format(liquidity_gate)])

					if abs(percent_difference) > PRICE_ALERT_PERCENTAGE or (coin in stablecoins and abs(percent_difference) > .01):
						if (type(liquidity_exchange) != str and liquidity_exchange < liquidity_limits) or (type(liquidity_gate) != str and liquidity_gate < liquidity_limits):
							continue

						alerted_coins.append([coin,exchangeL.upper(),round(-100*percent_difference,2),
							"Gateio_price: {}".format(ah.round_decimal(gateio_price)),
								"{}_price: {}".format(exchange,ah.round_decimal(exchange_price)), 
								"liquidity_exchange: ${}".format(liquidity_exchange),
								"liquidity_gate: ${}".format(liquidity_gate)])
			
			
			alerted_coins.sort(key=lambda x: abs(x[2]), reverse=True)
			web_coins.sort(key=lambda x: abs(x[2]), reverse=True)

			alerted_coins = ah.add_percentage_sign(alerted_coins)
			web_coins = ah.add_percentage_sign(web_coins)
			text_payload = []
			for alerted_coin in alerted_coins:
				if alerted_coin[0] not in sms:
					coin,exchange_price,gateio_price,percent_difference,liquidity_exchange,liquidity_gate = alerted_coin[0],alerted_coin[4],alerted_coin[3],alerted_coin[2],alerted_coin[5],alerted_coin[6]
					text_payload.append(["Coin: {}, {}, {} |||| {} {} {}".format(coin,exchange_price,gateio_price,percent_difference,liquidity_exchange,liquidity_gate)])
					sms.add(coin)
			if text_payload:
				SMS.send(str(text_payload))
				print(text_payload)

			with open(ah.OUTPUT_PATH+exchange+'.log','w') as file:
				if web_coins:
					file.write('[')
					for coin in web_coins:
						json.dump(coin,file)
						file.write(',')
					file.seek(file.tell() - 1, os.SEEK_SET)
					file.write('')
					file.write(']')
				else:
					file.truncate()

			
			if ah.count % 100 == 0:
				sms = set()
				print("{} finder still running count: {}".format(exchange,ah.count))

			ah.count += 1
			time.sleep(30)
			if exchange == 'coinbasepro':
				time.sleep(15)
			
		except BaseException as err:
			print("{} finder bugged out, time: {}".format(exchange,time.asctime(time.localtime())))
			print(f"Unexpected {err}, {type(err)}")
			print(traceback.format_exc())
			#exit(0)

if __name__ == "__main__":
	main()
	


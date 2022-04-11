import sys
import datetime, time
import traceback
import exchange_trade



def main():
	coinpair = sys.argv[1].lower()              #coin to be sold
	selling_exchange = sys.argv[2].lower()		#exchange where transaction are taking place
	arbitraged_exchange = sys.argv[3].lower()   #exchange to compare price of coin to
	fill_above = float(sys.argv[4])  	   		#percent to fill bids at (1.05 = 5% above market value)
	limit_above = float(sys.argv[5])       		#percent to put limit orders in at
	num_limit_orders = int(sys.argv[6])	   		#number of limit orders to put in
	is_extra_aggressive = bool(int(sys.argv[7])) 		#use to add extra limit order in if other fast bot present
	print("{} bot on {} starting".format(coinpair,selling_exchange))
	exchanges = {"gemini":"GeminiTrade","coinbasepro":"CoinbaseproTrade",'kucoin':"KucoinTrade","gateio":"GateioTrade","kraken":"KrakenTrade"}
	bot_class_name = getattr(exchange_trade,exchanges[selling_exchange])
	bot = bot_class_name(coinpair,arbitraged_exchange,fill_above,limit_above,num_limit_orders,is_extra_aggressive)

	bot.get_my_orders()

	count = 0
	while 1:
		try:
			if bot.num_limit_orders and not bot.get_my_orders():
				continue
			bot.get_coin_quantity()
			bot.get_coin_price_arbitraged_exchange()
			bot.get_coinpair_orderbook()

			if bot.my_coin_quantity < 0 or not bot.coinpair_orderbook or not bot.coin_price:
				continue

			bot.fill_bids()

			if bot.num_limit_orders:
				bot.replace_current_orders(bot.find_limit_order_values())

				#Fool Buyers
				if bot.is_stablecoin and selling_exchange == 'gemini':
					bot.correct_price()

			time.sleep(1)
			count += 1
			if count % 5000 == 0:
				print("count: {} still running {} on {}".format(count,coinpair,selling_exchange))
				bot.sms = True
				bot.sms2 = True
			break

		except BaseException as err:
			print("{} on {} bugged out, time: {}".format(coinpair,selling_exchange,time.asctime(time.localtime())))
			print(f"Unexpected {err}, {type(err)}")
			print(traceback.format_exc())
			exit(0)


if __name__ == "__main__":
	main()
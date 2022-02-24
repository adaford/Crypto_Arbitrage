import traceback
import time
import json
import arbitrage_hunt


def main():
	ah = arbitrage_hunt.ArbitrageHunt()
	while 1:
		try:
			gateio_prices = ah.get_prices("GATEIO")
			if type(gateio_prices) == dict:
				with open(ah.GATEIO_PATH,'w') as file:
					file.write(json.dumps(gateio_prices))

			if not ah.count % 1000:
				print("gateio update still running, count = {}".format(ah.count))

			ah.count += 1
			time.sleep(10)
			
		except BaseException as err:
			print("gateio update bugged out, time: {}".format(time.asctime(time.localtime())))
			print(f"Unexpected {err}, {type(err)}")
			print(traceback.format_exc())
			exit(0)


if __name__ == "__main__":
	main()


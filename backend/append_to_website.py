import json
import time
import os
import ast
from arbitrage_hunt import ArbitrageHunt as ah


def main():
	while 1:
		try:		
			output_webpage = []
			for exchange in ah.exchange_list:
				if exchange == "gateio":
					continue
				with open(ah.OUTPUT_PATH+exchange+'.log') as file:
					read_file = file.read()
					if not read_file:
						continue
					output_txt = ast.literal_eval(read_file)
					for li in output_txt:
						output_webpage.append(li)

			output_webpage.sort(key=lambda x: abs(float(x[2][:-1])), reverse=True)
			with open(ah.WEBPAGE_OUTPUT_PATH,'w') as file:
				json.dump(output_webpage,file)

			if not ah.count % 1000:
				print("append_to_website still running, count = {}".format(ah.count))
			ah.count += 1
			time.sleep(5)

		except BaseException as err:
			print("append_to_website bugged out, time: {}".format(time.asctime(time.localtime())))
			print(f"Unexpected {err}, {type(err)}")
			print(traceback.format_exc())
			#exit(0)

if __name__ == "__main__":
	main()
from requests import Request, Session
from requests.exceptions import ConnectionError, Timeout, TooManyRedirects
import json
from collections import defaultdict

url = 'https://pro-api.coinmarketcap.com/v1/cryptocurrency/listings/latest'
parameters = {
  'start':'1',
  'limit':'50',
  'convert':'USD'
}
headers = {
  'Accepts': 'application/json',
  'X-CMC_PRO_API_KEY': 'c848953f-8966-44eb-88f8-c221206ba216',
}

session = Session()
session.headers.update(headers)

def get_prices_coinmarketcap():
	ret = {}
	try:
		response = session.get(url, params=parameters)
		data = json.loads(response.text)["data"]
		for i in range(0,50):
			ret[data[i]["symbol"]] = data[i]["quote"]["USD"]["price"]
		return ret
	except (ConnectionError, Timeout, TooManyRedirects) as e:
		print(e)

# CoinMarketCap compare

WEBSITE: http://cryptoarbitrage.byethost6.com/

$python find_arbitrage.py <PRICE_ALERT_PERCENTAGE> -------> Searches several US exchanges for any coins with a <PRICE_ALERT_PERCENTAGE> price differential from coinmarketcap value

Pulls coin data for top 300 coins from CoinMarketCap and compares values with exchanges Kraken, BinanceUS, Kucoin, Gemini, Bittrex, and CoinbasePro

$python find_arbitrage.py 6 -------> Looks for a >6% price differential between any of exchanges listed above and CoinMarketCap

Be alerted to fat fingered whale market orders as soon as they happen!

******************************************************************************************************************************************************************

$python gemini_bot.py 1.05 1.07 kncusd coinbase 1 ------> runs a continuous trading bot for knc on gemini filling bids at >5% above coinbase price and undercutting large asks at >7% above coinbase price.

----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------



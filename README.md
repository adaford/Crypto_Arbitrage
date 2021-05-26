# CoinMarketCap.com compare --------------- This one works much better

$python find_arbitrage.py <PRICE_ALERT_PERCENTAGE> -------> Searches several US exchanges for any coins with a <PRICE_ALERT_PERCENTAGE> price differential from coinmarketcap value

Pulls coin data for top 130+ coins from CoinMarketCap and compares values with exchanges Kraken, BinanceUS, Kucoin, Gemini, Bittrex, and CoinbasePro

$python find_arbitrage.py 6 -------> Looks for a >6% price differential between any of exchanges listed above and CoinMarketCap

Be alerted to fat fingered whale market orders as soon as they happen!

----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------
# Crypto_Arbitrage

pip install tradingview-ta

python tradingviewprices.py <PRICE_ALERT_PERCENTAGE>

set PRICE_ALERT_PERCENTAGE to desired differential 

compares cryptocurrency prices for individual coins across several exchanges and looks for coins with large differences in price indicating an arbitrage opportunity.

$python tradingviewprices.py 6  ----------> searches exchanges in exchange_list.txt for any coins with a 6% or greater price differential between any two exchanges.

This one isn't very good because it pulls data from tradingview which is limited and also mixes foreign versions of the exchange

---------------------------------------------------------------------------------------------------------------------------------------------------------------------



from django.utils import timezone
from tradingview_ta import TA_Handler, Interval, Exchange
from django.shortcuts import render

def scanner(request, interval=''):
    # Set the list of tickers you want to scan
    tickers = [
        'NDX', 'AAPL', 'GOOG', 'AMZN', 'TSLA', 'EURUSD', 'USDGBP', 'USDAUD', 'USDNZD', 'EURJPY', 'GBPJPY', 'EURGBP',
        'GOLD', 'OIL', 'BTCUSD',
        ]

    # Initialize an empty list to store the results for each ticker
    results = []

    # Loop through each ticker and retrieve the real-time data using tradingview_ta
    for ticker in tickers:
        if ticker in ['EURUSD', 'USDGBP', 'USDAUD', 'USDNZD', 'EURJPY', 'GBPJPY', 'EURGBP']:
        # Get the real-time data for the forex ticker using tradingview_ta
            handler = TA_Handler(
                symbol=ticker,
                screener="forex",
                exchange="FX_IDC",
                interval=interval
            )
        elif ticker in ['GOLD', 'OIL']:
            # Get the real-time data for the commodity ticker using tradingview_ta
            handler = TA_Handler(
                symbol=ticker,
                screener="america",
                exchange="NYMEX",
                interval=interval
            )
        elif ticker == 'BTCUSD':
            # Get the real-time data for Bitcoin ticker using tradingview_ta
            handler = TA_Handler(
                symbol=ticker,
                screener="crypto",
                exchange="BITSTAMP",
                interval=interval
            )
        else:
            # Get the real-time data for the stock ticker using tradingview_ta
            handler = TA_Handler(
                symbol=ticker,
                screener="america",
                exchange="NASDAQ",
                interval=interval
            )

        # Calculate the Chandelier Exit using the tradingview_ta library
        # Determine the predicted market signal based on the Chandelier Exit value
        # Calculate the price returns and margin

        analysis_summary = handler.get_analysis().summary
        oscillators = handler.get_analysis().oscillators
        moving_averages = handler.get_analysis().moving_averages
        indicators = handler.get_analysis().indicators

        # Store the results for the ticker in a dictionary
        result = {
            'ticker': ticker,
            'analysis_summary': analysis_summary,
            'oscillators': oscillators,
            'moving_averages': moving_averages,
            'indicators': indicators,
        }

        # Add the result to the list of results
        results.append(result)

    # Render the scanner.html template and pass the results to the template
    return results

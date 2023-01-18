from django_celery_beat.models import PeriodicTask, CrontabSchedule
from django.utils import timezone
from tradingview_ta import TA_Handler, Interval, Exchange
from django.shortcuts import render

def scanner(request):
    # Connect to fxcmpy API

# Set the list of tickers you want to scan
    tickers = ['NDX', 'AAPL', 'GOOG', 'AMZN']

    # Initialize an empty list to store the results for each ticker
    results = []

    # Loop through each ticker and retrieve the real-time data using tradingview_ta
    for ticker in tickers:
        # Get the real-time data for the ticker using tradingview_ta
        handler = TA_Handler(
            symbol=ticker,
            screener="america",
            exchange="NASDAQ",
            interval=Interval.INTERVAL_5_MINUTES
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
            'indicators': indicators
        }

        # Add the result to the list of results
        results.append(result)

    # Render the scanner.html template and pass the results to the template
    print(results)
    return results


def schedule_predictions():
    # Create a crontab schedule for every hour
    schedule, created = CrontabSchedule.objects.get_or_create(
        minute='0',
        hour='*',
        day_of_week='*',
        day_of_month='*',
        month_of_year='*',
        timezone=timezone.utc,
    )
    # Create a periodic task to call the automate_predictions function
    task, created = PeriodicTask.objects.get_or_create(
        crontab=schedule,
        name='Automate predictions',
        task='myapp.utils.automate_predictions',
    )

# Run the scheduling function on startup
schedule_predictions()
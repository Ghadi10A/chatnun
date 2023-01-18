import time
import os
import pickle
import json
import requests
import yfinance as yf
import pandas as pd
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import accuracy_score
from sklearn.model_selection import train_test_split
from django.core.mail import send_mail
from .models import Prediction
import psycopg2
from bokeh.plotting import figure, output_file
from bokeh.embed import components
from apscheduler.schedulers.background import BackgroundScheduler

#celery -A myapp worker -l info

def automate_predictions():
    while True:
        for instrument in Prediction.INSTRUMENTS:
            close_price, vwap, signal, accuracy = predict_signal(instrument)
            prediction = Prediction(instrument=instrument, close_price=close_price, vwap=vwap, signal=signal, accuracy=accuracy)
            prediction.save()
            subject = f'Prediction for {instrument}'
            message = f'Close price: {close_price}\nVWAP: {vwap}\nMarket signal: {signal}'
            send_mail(subject, message, 'ghadiamine4@gmail.com', ['ghadiamine4@gmail.com'])
        time.sleep(3600)  # Wait one hour before making predictions again

def calculate_vwap(ticker):
    # Retrieve financial data for the instrument using yfinance
    data = yf.Ticker(ticker).history(period="max")
    # Use pandas to calculate the VWAP
    data = pd.DataFrame(data)
    data['vwap'] = (data['Volume'] * data['Close']).cumsum() / data['Volume'].cumsum()
    return data['vwap'][-1]

def predict_signal(ticker):
    conn = psycopg2.connect(host="localhost", user="postgres", password="Aminn2023", dbname="predictMarkets")
    cursor = conn.cursor()
    cursor.execute("CREATE TABLE models (id SERIAL PRIMARY KEY, model BYTEA)")
    model_file = f"{ticker}.model.pkl"
    if os.path.exists(model_file):
        # Load the trained model from the pickle file
        with open(model_file, 'rb') as f:
            clf = pickle.load(f)
    else:
        # Retrieve financial data for the instrument using yfinance
        data = yf.Ticker(ticker).history(period="max")
        # Use pandas to preprocess the data
        data = pd.DataFrame(data)
        data['target'] = data['Close'].shift(-1) > data['Close']
        data.dropna(inplace=True)
        # Split the data into training and testing sets
        X = data[['Open', 'High', 'Low', 'Close', 'Volume']]
        y = data['target']
        X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.1, random_state=42)
        # Train a Random Forest classifier on the training data
        clf = RandomForestClassifier()
        clf.fit(X_train, y_train)
        # Save the trained model to a pickle file
        with open(model_file, 'wb') as f:
            pickle.dump(clf, f)
            cursor.execute("INSERT INTO models (model) VALUES (%s)", (psycopg2.Binary(f),))
            conn.commit()
            conn.close()
    # Use the trained model to make predictions on the latest data
    data = yf.Ticker(ticker).history(period="max")
    X_latest = data[['Open', 'High', 'Low', 'Close', 'Volume']]
    y_pred = clf.predict(X_latest)
    accuracy = clf.score(X_latest, y_pred)
    last_diff = data['Close'][-1] - data['Close'][-2]
    last_diff_percent = last_diff / data['Close'][-2] * 100
    # Determine the predicted market signal based on the model's predictions
    if y_pred[0]:
        signal = 'buy'
    else:
        signal = 'sell'
    return data['Close'][-1], signal, accuracy, last_diff, last_diff_percent

def get_historical_data(ticker):
    stock = yf.Ticker(ticker)
    data = stock.history(period='1y')
    data = data[['Open', 'High', 'Low', 'Close', 'Volume']]
    data['date'] = data.index
    data = data.to_dict(orient='records')
    return data

def get_news_articles(ticker):
    # Set the API key and base URL
    articles = []
    api_key = '1f8833f2bc03499f9d5a2f3544bd9cde'
    base_url = 'https://newsapi.org/v2/everything?'
    
    # Set the query parameters for the request
    params = {
        "q": ticker,
        "apiKey": api_key
    }
    
    # Send the request and retrieve the response
    response = requests.get(base_url, params=params)
    data = response.json()
    for article in data["articles"]:
        article_info = {
            "title": article["title"],
            "author": article["author"],
            "publish_date": article["publishedAt"],
            "description": article["description"],
            "image": article["urlToImage"],
            "url": article["url"]
        }
        articles.append(article_info)
    return articles
    
def register_job(id, func, trigger, **kwargs):
    scheduler = BackgroundScheduler()
    scheduler.add_job(func=func, id=id, trigger=trigger, **kwargs)

# def get_chart_data(ticker):
#     # Retrieve financial data for the instrument using yfinance
#     data = yf.Ticker(ticker).history(period="max")
    
#     # Use pandas to calculate the difference between the current close price and the previous close price
#     data['diff'] = data['Close'] - data['Close'].shift(1)
#     data['diff_pct'] = data['diff'] / data['Close'].shift(1)
    
#     # Create the Bokeh plot
#     plot = figure(x_axis_type="datetime", title=f"{ticker} Stock Prices")
#     plot.line(data.index, data['Close'], line_width=2, legend_label="Close Price")
#     plot.line(data.index, data['diff'], line_width=2, color='red', legend_label="Difference")
#     plot.line(data.index, data['diff_pct'], line_width=2, color='green', legend_label="Difference %")
    
#     # Embed the plot in HTML
#     script, div = components(plot)
    
#     return script, div, data['diff'][-1], data['diff_pct'][-1]


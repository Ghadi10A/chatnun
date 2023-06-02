import time
import os
import pickle
import json
import requests
import yfinance as yf
import pandas as pd
import numpy as np
import joblib
from django.conf import settings
from sklearn.impute import SimpleImputer
from sklearn.preprocessing import MinMaxScaler
from sklearn.ensemble import GradientBoostingClassifier
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import accuracy_score
from sklearn.metrics import precision_score
from sklearn.model_selection import train_test_split, cross_val_score
from sklearn.preprocessing import StandardScaler
from django.core.mail import send_mail
from .models import Prediction
import psycopg2
from bokeh.plotting import figure, output_file
from bokeh.embed import components
from apscheduler.schedulers.background import BackgroundScheduler


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

def train_model(ticker):
    # Load historical data
    data = yf.Ticker(ticker).history(period="max")

    # Add features to the dataset
    data['Close_diff'] = data['Close'].diff()
    data['Close_diff_pct'] = data['Close_diff'] / data['Close'].shift(1)
    data['Volume_diff'] = data['Volume'].diff()
    data['Volume_diff_pct'] = data['Volume_diff'] / data['Volume'].shift(1)

    # Create target variable
    data['Target'] = (data['Close_diff'] > 0).astype(int)

    # Split the data into training and testing sets
    X = data[['Open', 'High', 'Low', 'Close', 'Volume', 'Close_diff', 'Close_diff_pct', 'Volume_diff', 'Volume_diff_pct']].iloc[1:]
    y = data['Target'].iloc[1:]
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)

    # Train a Random Forest Classifier on the training data
    clf = RandomForestClassifier(n_estimators=100, random_state=42)
    clf.fit(X_train, y_train)

    # Save the trained model to a file
    model_file = os.path.join(settings.BASE_DIR, 'myapp', 'models', f'predict_model.pkl')
    with open(model_file, 'wb') as f:
        pickle.dump(clf, f)

def predict_signal(ticker):
    # Load the saved model from a file
    model_file = os.path.join(settings.BASE_DIR, 'myapp', 'models', f'predict_model.pkl')
    with open(model_file, 'rb') as f:
        model = pickle.load(f)

    # Get the latest data
    data = yf.Ticker(ticker).history(period="1d")

    # Add features to the latest data
    last_close = data['Close'].iloc[0]
    data['Close_diff'] = last_close - data['Close'].shift(1)
    data['Close_diff_pct'] = data['Close_diff'] / data['Close'].shift(1)
    data['Volume_diff'] = data['Volume'].diff()
    data['Volume_diff_pct'] = data['Volume_diff'] / data['Volume'].shift(1)

    # Use the trained model to make predictions on the latest data
    X_latest = data[['Open', 'High', 'Low', 'Close', 'Volume', 'Close_diff', 'Close_diff_pct', 'Volume_diff', 'Volume_diff_pct']]
    y_pred = model.predict(X_latest)
    accuracy = model.score(X_latest, y_pred)

    # Determine the predicted market signal based on the model's predictions
    if y_pred[0]:
        signal = 'buy'
    else:
        signal = 'sell'

    # Calculate the difference and percentage difference between the last two closing prices
    last_diff = last_close - data['Close'].shift(1).iloc[-1]
    last_diff_percent = last_diff / data['Close'].shift(1).iloc[-1] * 100

    # Format the last_diff value as a string with a '+' or '-' sign
    if last_diff > 0:
        last_diff_str = "+{:.2f}".format(last_diff)
    else:
        last_diff_str = "{:.2f}".format(last_diff)

    # Return the predicted market signal, accuracy, last_diff value, and last_diff_percent
    return signal, accuracy, last_diff_str, last_diff_percent
# def train_and_save_model():
#     # Load the stock data
#     stock_data = yf.Ticker('AAPL').history(period='max')

#     # Calculate the VWAP
#     stock_data['VWAP'] = (stock_data['Volume'] * (stock_data['High'] + stock_data['Low']) / 2).cumsum() / stock_data['Volume'].cumsum()

#     # Select the features and labels
#     X = stock_data[['Open', 'High', 'Low', 'Close', 'Volume', 'VWAP']]
#     y = stock_data['Close']

#     # Split the data into training and testing sets
#     X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)

#     # Train the model
#     model = RandomForestClassifier()
#     model.fit(X_train, y_train)

#     # Save the model
#     with open('model.pkl', 'wb') as f:
#         pickle.dump(model, f)
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

def get_news_articles_yahoo(ticker):
    articles = []
    api_key = '9c9a27dc62mshf06f89e609daf51p1aaea8jsnfe9fee2c882f' # Replace with your own API key
    base_url = 'https://yahoo-finance15.p.rapidapi.com/api/yahoo/ne/news'
    
    headers = {
        "x-rapidapi-key": api_key,
        "x-rapidapi-host": "yahoo-finance15.p.rapidapi.com"
    }

    params = {
        "symbols": ticker,
        "region": "US",
        "count": 50 # Retrieve up to 50 news articles
    }
    
    response = requests.get(base_url, headers=headers, params=params)
    data = response.json()
    
    if isinstance(data, list):
        # If data is a list, assume it's the top-level object and get the 'items' array
        data = data[0].get('items', [])
    
    for article in data:
        article_info = {
            "title": article["title"],
            "author": article.get("authors", ""),
            "publish_date": article.get("publishDate", ""),
            "description": article.get("summary", ""),
            "image": article.get("thumbnail", ""),
            "url": article.get("url", "")
        }
        articles.append(article_info)
        
    return articles




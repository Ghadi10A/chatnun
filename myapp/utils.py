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


def train_and_save_model(ticker):
    data = yf.Ticker(ticker).history(period="3y")
    data['target'] = data['Close'].shift(-1) > data['Close']
    data.dropna(inplace=True)
    X = data[['Open', 'High', 'Low', 'Close', 'Volume']]
    y = data['target']
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)
    clf = RandomForestClassifier()
    clf.fit(X_train, y_train)
    accuracy = clf.score(X_test, y_test)
    model_file = os.path.join(settings.BASE_DIR, 'myapp', 'models', f'predict_model.pkl')
    with open(model_file, 'wb') as f:
        pickle.dump(clf, f)
    return accuracy


def predict_signal(ticker):
    model_file = os.path.join(settings.BASE_DIR, 'myapp', 'models', f'predict_model.pkl')

    # Retrieve financial data for the instrument using yfinance
    data = yf.Ticker(ticker).history(period="max", interval="1m")
    data = data.dropna()

    if data.empty:
        return None, None, None, None, None

    scaler = StandardScaler()
    scaled_data = scaler.fit_transform(data[['Open', 'High', 'Low', 'Close', 'Volume']])

    # Split the data into training and testing sets
    X_train, X_test, y_train, y_test = train_test_split(scaled_data, data['Close'].shift(-1) > data['Close'], test_size=0.2, random_state=0)

    # Train the model on the training set
    model = RandomForestClassifier()
    model.fit(X_train, y_train)

    # Evaluate the model on the testing set using cross-validation if the testing set has sufficient samples
    if len(X_test) < 5:
        accuracy = 1.0
    else:
        scores = cross_val_score(model, X_test, y_test, cv=5)
        accuracy = scores.mean()

    # Save the trained model to a pickle file
    with open(model_file, 'wb') as f:
        pickle.dump(model, f)

    # Determine the prediction signal
    latest_data = yf.Ticker(ticker).history(period="5m").iloc[-1]
    scaled_latest_data = scaler.transform(latest_data[['Open', 'High', 'Low', 'Close', 'Volume']].values.reshape(1, -1))
    prediction = model.predict(scaled_latest_data)[0]
    if prediction == 1:
        signal = 'Buy'
    elif prediction == 0:
        signal = 'Sell'
    else:
        signal = 'Neutral'

    # Use the trained model to make predictions on the latest data
    X_latest = scaler.transform(data[['Open', 'High', 'Low', 'Close', 'Volume']])
    y_pred = model.predict(X_latest)

    # Calculate other metrics
    last_diff = data['Close'][-1] - data['Close'][-2]
    last_diff_percent = last_diff / data['Close'][-2] * 100
    close_price = data['Close'][-1]

    return close_price, signal, accuracy, last_diff, last_diff_percent

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




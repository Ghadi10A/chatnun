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

def predict_signal(ticker):
    conn = psycopg2.connect(host="ec2-3-218-171-44.compute-1.amazonaws.com", user="tgjmzvivuenzpj", password="ce5308e80b98ffa36c801aa819faac8d4f17729db81a2bf5fa613329cc0c5f32", dbname="d7f8rqmt3g6vk6")
    cursor = conn.cursor()
    cursor.execute("CREATE TABLE models (id SERIAL PRIMARY KEY, model BYTEA)")
    model_file = f"{ticker}.model.pkl"
    if os.path.exists(model_file):
        # Load the trained model from the pickle file
        with open(model_file, 'rb') as f:
            model = pickle.load(f)
    else:
        # Retrieve financial data for the instrument using yfinance
        data = yf.Ticker(ticker).history(period="max")
        # Calculate the VWAP
        data['VWAP'] = (data['Close'] * data['Volume']).cumsum() / data['Volume'].cumsum()
        # Calculate the moving average of the close price over the past 20 days
        data['MA'] = data['Close'].rolling(20).mean()
        # Use pandas to preprocess the data
        data.dropna(inplace=True)
        scaler = StandardScaler()
        scaled_data = scaler.fit_transform(data[['Open', 'High', 'Low', 'Close', 'Volume', 'VWAP']])
        data[['Open', 'High', 'Low', 'Close', 'Volume', 'VWAP']] = scaled_data
        # Define the target variable
        data['Signal'] = np.where(data['Close'].shift(-1) > data['Close'], 1, 0)
        # Split the data into training and testing sets
        # Split the data into training and testing sets
        X = data[['Open', 'High', 'Low', 'Close', 'Volume', 'VWAP']]
        y = data['Signal']
        X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)
        # Fit a random forest classifier to the training data
        model = RandomForestClassifier()
        model.fit(X_train, y_train)
        # Save the trained model to a pickle file
        with open(model_file, 'wb') as f:
            pickle.dump(model, f)
            cursor.execute("INSERT INTO models (model) VALUES (%s)", (psycopg2.Binary(f),))
            conn.commit()
            conn.close()
    # Use the trained model to make predictions on the latest data
    latest_data = yf.Ticker(ticker).history(period="5m").iloc[-1]
    X_latest = latest_data[['Open', 'High', 'Low', 'Close', 'Volume']]
    y_pred = model.predict(X_latest)
    accuracy = model.score(X_latest, y_pred)
    last_diff = data['Close'][-1] - data['Close'][-2]
    last_diff_percent = last_diff / data['Close'][-2] * 100
    scaled_latest_data = scaler.transform(latest_data[['Open', 'High', 'Low', 'Close', 'Volume', 'VWAP']].values.reshape(1, -1))
    prediction = model.predict(scaled_latest_data)[0]
    # Determine the predicted market signal based on the model's predictions
    if prediction == 1:
        signal = 'buy'
    elif prediction == 0:
        signal = 'sell'
    else:
        signal = 'Neutral'    
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


# views.py
import pandas as pd
import schedule
from django.shortcuts import render
from .forms import PredictForm, SignUpForm, LoginForm
from .utils import calculate_vwap, predict_signal, get_historical_data, get_news_articles
from .tasks import scanner
from django.shortcuts import render, redirect, redirect
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.forms import UserCreationForm
from django.contrib import messages
from django.contrib.auth.models import User
from django.contrib.auth.decorators import login_required
from django.utils.translation import gettext_lazy as _
from django.http import HttpResponse


def run_scanner(request):
# Run the scanner task
    results = scanner(request)
# Render the scanner.html template
    return render(request, 'scanner.html', {'results': results})

schedule.every(5).minutes.do(run_scanner)
    
def predict_signals(request):
    if request.method == 'POST':
        form = PredictForm(request.POST)
        if form.is_valid():
            ticker = form.cleaned_data['ticker']
            close_price, signal, accuracy, last_diff, last_diff_percent = predict_signal(ticker)
            vwap = calculate_vwap(ticker)
            data = get_historical_data(ticker)
            articles = get_news_articles(ticker)
            # diff, diff_pct, script, div = get_chart_data(ticker)
            context = {'close_price': round(close_price, 4), 'signal': signal, 'vwap': round(vwap, 4), 'ticker': ticker, 'accuracy': accuracy, 'last_diff': round(last_diff, 2), 'last_diff_percent': round(last_diff_percent, 2), 'data': data, 'articles': articles}
            return render(request, 'prediction_results.html', context)
    else:
        form = PredictForm()
    return render(request, 'predict_signal.html', {'form': form})   

def user_signup(request):
    if request.method == 'POST':
        form = UserCreationForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('login')
    else:
        form = UserCreationForm()
    return render(request, 'signup.html', {'form': form}) 

def user_login(request):
    if request.method == 'POST':
        form = LoginForm(request.POST)
        if form.is_valid():
            username = form.cleaned_data['username']
            password = form.cleaned_data['password']
            user = authenticate(request, username=username, password=password)
            if user is not None:
                login(request, user)
                return redirect('show_profile', username=request.user.username)
        else:
            messages.error(request, 'Invalid username or password.')
    else:
        form = LoginForm()
    return render(request, 'login.html', {'form': form})


def show_profile(request, username):
    user = User.objects.get(username=username)
    context = {'user': user}
    return render(request, 'profile.html', context)


def user_logout(request):
    logout(request)
    return redirect('predict_signals')    

def prediction_trend(request):
    # Get the latest prediction trend from the database
    trend = get_prediction_trend()
    # Render the base template with the trend included in the context
    return render(request, 'base.html', {'trend': trend}) 


def add_ticker(request):
    if request.method == 'POST':
        form = AddTickerForm(request.POST)
        if form.is_valid():
            ticker_symbol = form.cleaned_data['ticker_symbol']
            # Check if the ticker already exists in the database
            ticker, created = Ticker.objects.get_or_create(symbol=ticker_symbol)
            # Add the ticker to the user's list of favorite tickers
            UserTicker.objects.create(user=request.user, ticker=ticker)
            messages.success(request, f'{ticker_symbol} has been added to your list of favorite tickers')
            return HttpResponseRedirect(reverse('home'))
    else:
        form = AddTickerForm()
    return render(request, 'add_ticker.html', {'form': form})

def view_following(request):
    following = Follow.objects.filter(follower=request.user)
    context = {'following': following}
    return render(request, 'view_following.html', context)


def view_followers(request):
    followers = Follow.objects.filter(following=request.user)
    context = {'followers': followers}
    return render(request, 'view_followers.html', context)
                      
def get_user_followers(user):
    followers = Follow.objects.filter(following=user).values_list('follower', flat=True)
    return User.objects.filter(id__in=followers)

def get_user_following(user):
    following = Follow.objects.filter(follower=user).values_list('following', flat=True)
    return User.objects.filter(id__in=following)

def follow_user(follower, following):
    follow = Follow.objects.create(follower=follower, following=following)
    follow.save()
def my_view(request):
    message = _("Log in")
    return HttpResponse(message)   
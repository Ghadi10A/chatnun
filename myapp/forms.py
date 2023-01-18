from django import forms
from .models import User

class PredictForm(forms.Form):
    TICKER_CHOICES = (
        ('^NDX', 'Nasdaq100'),
        ('AAPL', 'Apple'),
        ('AMZN', 'Amazon'),
        ('GOOGL', 'Google'),
        ('TSLA', 'Tesla'),
        ('BTC-USD', 'Bitcoin'),
        ('GLD', 'Gold'),
        ('OIL', 'Oil'),
    )
    ticker = forms.ChoiceField(choices=TICKER_CHOICES)

class SignUpForm(forms.ModelForm):
    email = forms.EmailField(label="Email")
    password = forms.CharField(widget=forms.PasswordInput, strip=False, help_text="")
    password2 = forms.CharField(widget=forms.PasswordInput, strip=False, help_text="")

    class Meta:
        model = User
        fields = ('username', 'email', 'first_name', 'last_name')

    def clean_password2(self):
        cleaned_data = self.cleaned_data
        password = cleaned_data.get('password')
        password2 = cleaned_data.get('password2')

        if password != password2:
            raise forms.ValidationError("Passwords do not match")
        return password2 
        
class LoginForm(forms.Form):
    username = forms.CharField()
    password = forms.CharField(widget=forms.PasswordInput)  

class AddTickerForm(forms.Form):
    ticker = forms.CharField(label='Ticker', max_length=100)
    
class FollowUserForm(forms.Form):
    username = forms.CharField(label='Username', max_length=100)    


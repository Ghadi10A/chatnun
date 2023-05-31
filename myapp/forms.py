from django import forms
from django.db import models
from .models import User, Profile, Follow, Post, Message, Comment, EmojiReaction, Group, GroupPost, GroupMessage, CommentGroup, EmojiReactionGroup, GroupRequest
from django.utils import timezone
import emojis
from django.contrib.auth.forms import UserCreationForm
import yfinance as yf
from django.utils.translation import gettext as _
from location_field.forms.plain import PlainLocationField
from django.forms.widgets import Textarea
from django.forms.widgets import FileInput


class IntervalForm(forms.Form):
    INTERVAL_CHOICES = [
        ('1m', _('1 Minute')),
        ('5m', _('5 Minutes')),
        ('15m', _('15 Minutes')),
        ('30m', _('30 Minutes')),
        ('1h', _('1 Hour')),
        ('4h', _('4 Hours')),
        ('1d', _('1 Day')),
        ('1w', _('1 Week')),
        ('1M', _('1 Month')),
    ]
    interval = forms.ChoiceField(choices=INTERVAL_CHOICES)

class PredictForm(forms.Form):
    TICKER_CHOICES = (
    ('GC=F', 'Gold'),
    ('SI=F', 'Silver'),
    ('HG=F', 'Copper'),
    ('PL=F', 'Platinum'),
    ('GSPC', 'S&P 500'),
    ('DJI', 'Dow Jones'),
    ('NDX', 'Nasdaq 100'),
    ('EURUSD=X', 'EUR/USD'),
    ('GBPUSD=X', 'GBP/USD'),
    ('USDJPY=X', 'USD/JPY'),
    ('USDCHF=X', 'USD/CHF'),
    ('AUDUSD=X', 'AUD/USD'),
    ('NZDUSD=X', 'NZD/USD'),
    ('USDCAD=X', 'USD/CAD'),
    ('RUT', 'Russell 2000'),
    ('PA=F', 'Palladium'),
    ('ALI=F', 'Aluminum'),
    ('ZNC=F', 'Zinc'),
    ('LEA=F', 'Lead'),
    ('NI=F', 'Nickel'),
    ('TIN=F', 'Tin'),
    ('CA=F', 'Cobalt'),
    ('TNX', '10-Year Treasury Yield'),
    ('VIX', 'VIX'),
    ('AAPL', 'Apple'),
    ('AMZN', 'Amazon'),
    ('GOOGL', 'Google'),
    ('TSLA', 'Tesla'),
    ('BTC-USD', 'Bitcoin'),
    ('GLD', 'Gold ETF'),
    ('SLV', 'Silver ETF'),
    ('COPPER', 'Copper ETF'),
    ('PLTM', 'Platinum ETF'),
    ('PALL', 'Palladium ETF'),
    ('ALUM', 'Aluminum ETF'),
    ('ZINC', 'Zinc ETF'),
    ('LEAD', 'Lead ETF'),
    ('NICKEL', 'Nickel ETF'),
    ('TIN', 'Tin ETF'),
    ('COBALT', 'Cobalt ETF'),
    ('BABA', 'Alibaba'),
    ('MSFT', 'Microsoft'),
    ('NFLX', 'Netflix'),
    ('FB', 'Facebook'),
    ('TWTR', 'Twitter'),
    ('SNAP', 'Snap Inc'),
    ('PYPL', 'PayPal'),
    ('MA', 'Mastercard'),
    ('V', 'Visa'),
    ('JPM', 'JP Morgan Chase'),
    ('BAC', 'Bank of America'),
    ('C', 'Citigroup'),
    ('WFC', 'Wells Fargo'),
    ('JNJ', 'Johnson & Johnson'),
    ('PFE', 'Pfizer'),
    ('MRK', 'Merck & Co.'),
    ('NKE', 'Nike'),
    ('SBUX', 'Starbucks'),
    ('MCD', 'McDonalds'),
    )
    
    ticker = forms.ChoiceField(choices=TICKER_CHOICES, label="")

class SignUpForm(UserCreationForm):
    email = forms.EmailField(max_length=254, required=True, help_text='Required. Enter a valid email address.')
    first_name = forms.CharField(max_length=30, required=True, help_text='Required.')
    last_name = forms.CharField(max_length=30, required=True, help_text='Required.')

    class Meta:
        model = User
        fields = ('username', 'first_name', 'last_name')

    def save(self, commit=True):
        user = super(SignUpForm, self).save(commit=False)
        user.email = self.cleaned_data['email']
        user.first_name = self.cleaned_data['first_name']
        user.last_name = self.cleaned_data['last_name']
        if commit:
            user.save()
        return user


        
class LoginForm(forms.Form):
    username = forms.CharField()
    password = forms.CharField(widget=forms.PasswordInput)  

class SearchForm(forms.Form):
    query = forms.CharField(max_length=100, label='')

class AddTickerForm(forms.Form):
    ticker = forms.CharField(label='Ticker', max_length=100)
    
class FollowUserForm(forms.Form):
    username = forms.CharField(label='Username', max_length=100)    

class ProfileUpdateForm(forms.ModelForm):
    image = forms.ClearableFileInput(attrs={'class': 'form-group', 'accept': 'image/*', 'required': False})
    bio = forms.CharField(widget=forms.Textarea(attrs={'class': 'form-group', 'rows': 3, 'required': False}), required=False)
    birthdate = forms.DateField(required=False)
    city = forms.CharField(max_length=255, required=False)
    location = PlainLocationField(based_fields=['city'], zoom=7, blank=True, required=False)

    class Meta:
        model = Profile
        fields = ['image', 'bio', 'birthdate', 'city', 'location']

    def __init__(self, *args, **kwargs):
        super(ProfileUpdateForm, self).__init__(*args, **kwargs)
        self.fields['bio'].initial = self.instance.bio
        self.fields['birthdate'].initial = self.instance.birthdate
        self.fields['city'].initial = self.instance.city
        self.fields['location'].initial = self.instance.location

    def save(self, commit=True):
        profile = super(ProfileUpdateForm, self).save(commit=False)
        profile.bio = self.cleaned_data['bio']
        profile.birthdate = self.cleaned_data['birthdate']
        profile.city = self.cleaned_data['city']
        profile.location = self.cleaned_data['location']
        if commit:
            profile.save()
        return profile

class SubscriptionForm(forms.Form):
    PLAN_CHOICES = [
        ('threeMonths', '3 Months Subscription $9'),
        ('sixMonths', '6 Months Subscription $19'),
        ('oneYear', '1 Year Subscription $29'),
    ]
    
    plan = forms.ChoiceField(choices=PLAN_CHOICES, widget=forms.Select(attrs={'class': 'form-select'}))


class UpdateGroupForm(forms.ModelForm):
    name = forms.CharField(max_length=100)
    description = forms.CharField(widget=Textarea(attrs={'class': 'form-control', 'rows': 3}))
    image = forms.ImageField(widget=FileInput(attrs={'class': 'form-control-file my-2', 'accept': 'image/*'}), required=False)
    class Meta:
        model = Group
        fields = ['name', 'description', 'image']
    def __init__(self, *args, **kwargs):
        super(UpdateGroupForm, self).__init__(*args, **kwargs)
        self.fields['name'].initial = self.instance.name
        self.fields['description'].initial = self.instance.description
        self.fields['image'].initial = self.instance.image
    def save(self, commit=True):
        group = super(UpdateGroupForm, self).save(commit=False)
        group.name = self.cleaned_data['name']
        group.description = self.cleaned_data['description']
        group.image = self.cleaned_data['image']
        if commit:
            group.save()
        return group     

class PostForm(forms.ModelForm):
    content = forms.CharField(widget=forms.Textarea(attrs={
        'class': 'form-control',
        'placeholder': '...',
        'rows': 3,
    }))
    image = forms.ImageField(widget=forms.ClearableFileInput(attrs={
        'class': 'form-control-file my-2',
        'style': 'font-size: 80%;',
        'id': 'id_image',  # Add the ID attribute
    }), required=False)

    video = forms.FileField(widget=forms.ClearableFileInput(attrs={
        'class': 'form-control-file my-2',
        'style': 'font-size: 80%;',
        'id': 'id_video',  # Add the ID attribute
    }), required=False)

    sound = forms.FileField(widget=forms.ClearableFileInput(attrs={
        'class': 'form-control-file my-2',
        'style': 'font-size: 80%;',
        'id': 'id_sound',  # Add the ID attribute
    }), required=False)

    # Add fields for save, edit, and delete actions
    save = forms.BooleanField(widget=forms.HiddenInput(), required=False)
    edit = forms.BooleanField(widget=forms.HiddenInput(), required=False)
    delete = forms.BooleanField(widget=forms.HiddenInput(), required=False)

    class Meta:
        model = Post
        fields = ['content', 'image', 'video', 'sound']

    def save(self, author=None, commit=True):
        instance = super().save(commit=False)
        if author:
            instance.author = author
        if commit:
            instance.save()
        return instance


class CreateGroupForm(forms.ModelForm):
    name = forms.CharField(max_length=100)
    description = forms.CharField(widget=Textarea(attrs={'class': 'form-control', 'rows': 3}))
    image = forms.ImageField(widget=FileInput(attrs={'class': 'form-control-file my-2', 'accept': 'image/*'}), required=False)

    class Meta:
        model = Group
        fields = ['name', 'description', 'image']

    def __init__(self, *args, **kwargs):
        super(CreateGroupForm, self).__init__(*args, **kwargs)

    def save(self, commit=True, admin=None):
        group = super(CreateGroupForm, self).save(commit=False)
        group.admin = admin
        if commit:
            group.save()
            self.save_m2m()
        return group
         
class GroupPostForm(forms.ModelForm):
    content = forms.CharField(widget=forms.Textarea(attrs={
        'class': 'form-control',
        'placeholder': '...',
        'rows': 3,
    }))
    image = forms.ImageField(widget=forms.ClearableFileInput(attrs={
        'class': 'form-control-file my-2',
        'style': 'font-size: 80%;',
        'id': 'id_image',  # Add the ID attribute
    }), required=False)

    video = forms.FileField(widget=forms.ClearableFileInput(attrs={
        'class': 'form-control-file my-2',
        'style': 'font-size: 80%;',
        'id': 'id_video',  # Add the ID attribute
    }), required=False)

    sound = forms.FileField(widget=forms.ClearableFileInput(attrs={
        'class': 'form-control-file my-2',
        'style': 'font-size: 80%;',
        'id': 'id_sound',  # Add the ID attribute
    }), required=False)

    # Add fields for save, edit, and delete actions
    save = forms.BooleanField(widget=forms.HiddenInput(), required=False)
    edit = forms.BooleanField(widget=forms.HiddenInput(), required=False)
    delete = forms.BooleanField(widget=forms.HiddenInput(), required=False)

    class Meta:
        model = GroupPost
        fields = ['content', 'image', 'video', 'sound']

    def save(self, author=None, commit=True):
        instance = super().save(commit=False)
        if author:
            instance.author = author
        if commit:
            instance.save()
        return instance     

class CommentForm(forms.ModelForm):
    comment = forms.CharField(
        label='',
        widget=forms.Textarea(attrs={'class': 'form-control', 'placeholder': '...', 'rows': '3'}),
    )

    class Meta:
        model = Comment
        fields = ['comment']

class CommentFormGroup(forms.ModelForm):
    comment = forms.CharField(
        label='',
        widget=forms.Textarea(attrs={'class': 'form-control', 'placeholder': '...', 'rows': '3'}),
    )

    class Meta:
        model = CommentGroup
        fields = ['comment']

class ReactionForm(forms.ModelForm):
    EMOJI_CHOICES = [
        ('heart', '❤️'),
        # ('thumbs_up', '👍'),
        # ('thumbs_down', '👎'),
        # ('smiling_face', '😊'),
        # ('angry', '😠')
    ]
    emoji = forms.ChoiceField(choices=EMOJI_CHOICES, widget=forms.Select(attrs={'class': 'form-control'}))

    class Meta:
        model = EmojiReaction  # add model attribute
        fields = ('emoji',)

    def __init__(self, *args, post_id=None, **kwargs):
        super().__init__(*args, **kwargs)
        for choice in self.EMOJI_CHOICES:
            self.fields[choice[0]] = forms.BooleanField(required=False, widget=forms.CheckboxInput(attrs={
                'class': 'emoji-picker-item btn-sm',
                'type': 'button',
                'data-emoji': choice[1],
            }))

    def save(self, commit=True, author=None, post=None):
        emoji = super().save(commit=False)
        emoji.author = author
        emoji.post = post
        if commit:
            emoji.save()
        return emoji  

# class CreateGroupForm(forms.ModelForm):
#     class Meta:
#         model = Group
#         fields = ['name', 'description']
#         widgets = {
#             'members': forms.CheckboxSelectMultiple,
#         }

class EmojiReactionFormGroup(forms.ModelForm):
    EMOJI_CHOICES = [
        ('heart', '❤️'),
        # ('thumbs_up', '👍'),
        # ('thumbs_down', '👎'),
        # ('smiling_face', '😊'),
        # ('angry', '😠')
    ]
    emoji = forms.ChoiceField(choices=EMOJI_CHOICES, widget=forms.Select(attrs={'class': 'form-control'}))

    class Meta:
        model = EmojiReactionGroup  # add model attribute
        fields = ('emoji',)

    def __init__(self, *args, post_id=None, **kwargs):
        super().__init__(*args, **kwargs)
        for choice in self.EMOJI_CHOICES:
            self.fields[choice[0]] = forms.BooleanField(required=False, widget=forms.CheckboxInput(attrs={
                'class': 'emoji-picker-item btn-sm',
                'type': 'button',
                'data-emoji': choice[1],
            }))

    def save(self, commit=True, author=None, post=None):
        emoji = super().save(commit=False)
        emoji.author = author
        emoji.post = post
        if commit:
            emoji.save()
        return emoji

class ChatbotForm(forms.Form):
    prompt = forms.CharField(widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': '...!', 'rows': '3'}))        
class MessageForm(forms.ModelForm):
    class Meta:
        model = Message
        fields = ['content']
        widgets = {
            'content': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
        }
class GroupMessageForm(forms.ModelForm):
    class Meta:
        model = GroupMessage
        fields = ['message']
        widgets = {
            'message': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
        }  
class GroupRequestForm(forms.ModelForm):
    class Meta:
        model = GroupRequest
        fields = ['user', 'group']
        
    def __init__(self, *args, **kwargs):
        super(GroupRequestForm, self).__init__(*args, **kwargs)
        self.fields['user'].widget = forms.HiddenInput()
        self.fields['group'].widget.attrs.update({'class': 'selectpicker', 'multiple': 'multiple'})

# views.py
import pandas as pd
import schedule
import uuid
import os
import pickle
import emojis
import openai
import joblib
from datetime import timedelta
from django.http import JsonResponse
from django.db.models import Count, Prefetch
from django.utils import timezone
from django.db import models
from .models import User, Profile, Follow, Post, Comment, Message, EmojiReaction, Group, JoinRequest, CommentGroup, EmojiReactionGroup, GroupPost, GroupMessage, Notification, ChatHistory
from django.shortcuts import render
from .forms import IntervalForm, PredictForm, SignUpForm, LoginForm, SubscriptionForm, ProfileUpdateForm, PostForm, GroupPostForm, MessageForm, GroupMessageForm, CommentForm, CommentFormGroup, ReactionForm, SearchForm, EmojiReactionFormGroup, ChatbotForm, CreateGroupForm, UpdateGroupForm
from .utils import calculate_vwap, train_and_save_model, predict_signal, get_historical_data, get_news_articles
from .tasks import scanner
from django.shortcuts import render, redirect, redirect
from django.contrib.auth import authenticate, login, logout
from allauth.socialaccount.models import SocialAccount
from django.contrib.auth.forms import UserCreationForm
from django.contrib import messages
from django.contrib.auth.models import User
from django.contrib.auth.decorators import login_required
from django.utils.translation import gettext_lazy as _
from django.http import HttpResponse
from django.shortcuts import get_object_or_404 
from django.contrib.auth import get_user_model
from django.db.models import Q
from channels.layers import get_channel_layer
from asgiref.sync import async_to_sync
from langdetect import detect
from django.conf import settings
from django.template.loader import render_to_string
from django.utils.encoding import force_bytes, force_str
from django.utils.http import urlsafe_base64_encode, urlsafe_base64_decode
from django.contrib.sites.shortcuts import get_current_site
from django.contrib.auth.tokens import PasswordResetTokenGenerator
import stripe
from functools import wraps
from django.contrib.auth.tokens import default_token_generator
from django.contrib.auth.hashers import check_password
import smtplib
from sendgrid import SendGridAPIClient
from sendgrid.helpers.mail import Mail, Email, Content
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from django.utils import translation
from django.utils.translation import gettext as _
from django.http import HttpResponseRedirect, HttpResponseBadRequest
from django.utils.translation import activate
from django.contrib.auth.models import User
from django.core.mail import send_mail, EmailMultiAlternatives
from django.utils.html import strip_tags
from django.db import IntegrityError
from django.contrib.auth.forms import PasswordResetForm
from django.urls import reverse
from django.contrib.auth.forms import SetPasswordForm


openai.api_key = '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'
model_file = os.path.join(settings.BASE_DIR, 'myapp', 'models', f'model.pkl')
account_activation_token = PasswordResetTokenGenerator()

stripe.api_key = settings.STRIPE_SECRET_KEY



def switch_language(request, language_code):
    if request.method == 'POST':
        language_code = request.POST.get('language')
        if language_code and translation.check_for_language(language_code):
            translation.activate(language_code)
            response = HttpResponseRedirect(request.POST.get('next', '/'))
            response.set_cookie(settings.LANGUAGE_COOKIE_NAME, language_code)
            request.session['django_language'] = language_code
            request.LANGUAGE_CODE = language_code  # Set the LANGUAGE_CODE variable
            return response
    return HttpResponseBadRequest()

def requires_subscription(view_func):
    @wraps(view_func)
    def wrapper(request, *args, **kwargs):
        user = request.user
        if user.is_authenticated and user.profile.subscription_status == 'active':
            return view_func(request, *args, **kwargs)
        else:
            return redirect('choose_plan')
    return wrapper
def choose_plan(request):
    if request.method == 'POST':
        form = SubscriptionForm(request.POST)
        if form.is_valid():
            plan = form.cleaned_data.get('plan')
            if plan in ('threeMonths', 'sixMonths', 'oneYear'):
                return redirect('subscribe', plan=plan)
    else:
        form = SubscriptionForm()

    return render(request, 'modals/choose_plan.html', {'form': form})
def subscribe(request, plan):
    if plan not in ('threeMonths', 'sixMonths', 'oneYear'):
        return redirect('choose_plan')

    # Check if user already has an active subscription
    user = request.user

    # Create a dictionary of plan names and their corresponding prices
    plans = {
        'threeMonths': settings.STRIPE_PRICE_3MONTHS,
        'sixMonths': settings.STRIPE_PRICE_6MONTHS,
        'oneYear': settings.STRIPE_PRICE_1YEAR,
    }

    # Create Stripe checkout session and redirect user to payment page
    session = stripe.checkout.Session.create(
        customer_email=user.email,
        payment_method_types=['card'],
        line_items=[{
            'price': plans[plan],
            'quantity': 1,
        }],
        mode='subscription',
        success_url='http://localhost:8000/subscribe/success/?plan='+plan,
        cancel_url='http://localhost:8000/subscribe/cancel/',
    )

    # Store the plan and other relevant information in session variables
    request.session['subscription_plan'] = plan
    request.session['subscription_session_id'] = session.id

    return redirect(session.url)

def subscribe_success(request):
    # Retrieve the stored subscription plan and session ID from session variables
    plan = request.session.get('subscription_plan')
    session_id = request.session.get('subscription_session_id')

    # Verify the payment and session ID with Stripe API
    session = stripe.checkout.Session.retrieve(session_id)

    if session.payment_status == 'paid':
        # Payment successful, update subscription status and profile information
        user = request.user
        profile = user.profile

        if plan == 'threeMonths':
            profile.subscription_plan = '3m'
            profile.subscription_end = timezone.now() + timedelta(days=90)
        elif plan == 'sixMonths':
            profile.subscription_plan = '6m'
            profile.subscription_end = timezone.now() + timedelta(days=180)
        elif plan == 'oneYear':
            profile.subscription_plan = '1y'
            profile.subscription_end = timezone.now() + timedelta(days=365)

        profile.subscription_status = 'active'
        profile.save()

    # Clear the session variables
    del request.session['subscription_plan']
    del request.session['subscription_session_id']

    return render(request, 'subscribe_success.html')

def subscribe_cancel(request):
    # Clear the session variables
    del request.session['subscription_plan']
    del request.session['subscription_session_id']

    return render(request, 'subscribe_cancel.html')


def renew_subscription(request):
    # Check if user already has an active subscription
    user = request.user
    if user.profile.subscription_status != 'active':
        return redirect('choose_plan')

    return render(request, 'renew_subscription.html')

@login_required(login_url='user_login') 
def choose_interval(request, interval):
    form = IntervalForm(initial={'interval': interval})
    if request.method == 'POST':
        form = IntervalForm(request.POST)
        if form.is_valid():
            interval = form.cleaned_data['interval']
            results = scanner(request, interval)
            new_conversation_id = str(uuid.uuid4())
            return render(request, 'scanner.html', {'results': results, 'form': form, 'interval': interval, 'new_conversation_id': new_conversation_id, 'LANGUAGES': settings.LANGUAGES})
    new_conversation_id = str(uuid.uuid4())
    return render(request, 'scanner.html', {'form': form, 'interval': interval, 'new_conversation_id': new_conversation_id, 'LANGUAGES': settings.LANGUAGES})    

@login_required(login_url='user_login')
def run_scanner(request, interval):
    results = scanner(request, interval)
    form = IntervalForm(initial={'interval': interval})
    new_conversation_id = str(uuid.uuid4())
    return render(request, 'scanner.html', {'form': form, 'results': results, 'interval': interval, 'new_conversation_id': new_conversation_id, 'LANGUAGES': settings.LANGUAGES})    

@requires_subscription
def predict_signals(request):
    new_conversation_id = str(uuid.uuid4())
    form = PredictForm(request.POST)
    if request.method == 'POST':
        if form.is_valid():
            ticker = form.cleaned_data['ticker']
            accuracy = train_and_save_model(ticker)
            close_price, signal, last_diff, last_diff_percent = predict_signal(ticker)
            vwap = calculate_vwap(ticker)
            data = get_historical_data(ticker)
            articles = get_news_articles(ticker)
            # diff, diff_pct, script, div = get_chart_data(ticker)
            context = {'form': form, 'close_price': round(close_price, 2), 'signal': signal, 'vwap': round(vwap, 2), 'ticker': ticker, 'accuracy': round(accuracy)*100, 'last_diff': round(last_diff, 2), 'last_diff_percent': round(last_diff_percent, 2), 'data': data, 'articles': articles, 'new_conversation_id': new_conversation_id, 'LANGUAGES': settings.LANGUAGES}
            return render(request, 'prediction_results.html', context)
    else:
        form = PredictForm()
    return render(request, 'predict_signal.html', {'form': form, 'new_conversation_id': new_conversation_id, 'LANGUAGES': settings.LANGUAGES})
def generate_verification_link(request, user):
    current_site = get_current_site(request)
    uid = urlsafe_base64_encode(force_bytes(user.pk))
    token = account_activation_token.make_token(user)
    verification_link = f"{request.scheme}://{current_site.domain}/activate/{uid}/{token}/"
    return verification_link

def send_verification_email(request, user):
    current_site = get_current_site(request)
    mail_subject = 'Verify your email'
    verification_link = generate_verification_link(request, user)
    message = f"Click the following link to verify your email: {verification_link}"
    email = EmailMultiAlternatives(mail_subject, message, from_email=settings.DEFAULT_FROM_EMAIL, to=[user.email])
    email.send()

def verification_email_sent(request):
    user = request.user
    return render(request, 'auth/email_verification_sent.html', {'verification_sent': True, 'user': user})

def verification_email_resend(request):
    user = request.user
    send_verification_email(request, user)
    return render(request, 'auth/email_verification_sent.html', {'verification_sent': True, 'user': user})

def user_signup(request):
    if request.method == 'POST':
        form = SignUpForm(request.POST)
        if form.is_valid():
            user = form.save(commit=False)
            user.is_active = False  # User is not active until they verify their email
            user.save()
            Profile.objects.create(user=user)

            send_verification_email(request, user)

            # Redirect the user to the verification sent page
            return redirect('verification_email_sent')
    else:
        form = SignUpForm()

    new_conversation_id = str(uuid.uuid4())
    return render(request, 'auth/signup.html', {'form': form, 'new_conversation_id': new_conversation_id, 'LANGUAGES': settings.LANGUAGES})

def activate_account(request, uidb64, token):
    try:
        uid = force_str(urlsafe_base64_decode(uidb64))
        user = User.objects.get(pk=uid)
    except (TypeError, ValueError, OverflowError, User.DoesNotExist):
        user = None

    if user is not None and account_activation_token.check_token(user, token):
        user.is_active = True
        user.save()
        return render(request, 'auth/account_activated.html')
    else:
        return render(request, 'auth/email_verification_sent.html')
def user_login(request):
    if request.method == 'POST':
        form = LoginForm(request.POST)
        if form.is_valid():
            username = form.cleaned_data['username']
            password = form.cleaned_data['password']
            user = authenticate(request, username=username, password=password)
            if user is not None:
                if user.is_active:
                    login(request, user)
                    return redirect('home')
                else:
                    return redirect('verification_email_sent')
            else:
                messages.error(request, 'Invalid username or password.')
        else:
            messages.error(request, 'Please correct the errors below.')
    else:
        form = LoginForm() 
    return render(request, 'auth/login.html', {'form': form, 'LANGUAGES': settings.LANGUAGES})

def forgot_password(request):
    if request.method == 'POST': 
        form = PasswordResetForm(request.POST)
        if form.is_valid():
            email = form.cleaned_data['email']
            associated_users = User.objects.filter(email=email)
            
            if associated_users.exists():
                for user in associated_users:
                    # Generate reset password token
                    token = default_token_generator.make_token(user)
                    
                    # Build reset password URL
                    uid = urlsafe_base64_encode(force_bytes(user.pk))
                    reset_password_url = reverse('reset_password', kwargs={'uidb64': uid, 'token': token})
                    reset_password_url = request.build_absolute_uri(reset_password_url)
                    
                    # Render email template
                    mail_subject = 'Reset your password'
                    message = render_to_string('auth/reset_password_email.html', {
                        'user': user,
                        'reset_password_url': reset_password_url,
                    })
                    
                    # Send email
                    send_mail(mail_subject, message, settings.DEFAULT_FROM_EMAIL, [email])
                
                messages.success(request, 'A password reset link has been sent to your email.')
            else:
                messages.error(request, 'No user associated with this email.')
            
            return redirect('forgot_password')
    else:
        form = PasswordResetForm()
    
    return render(request, 'auth/forgot_password.html', {'form': form})


def reset_password(request, uidb64, token):
    try:
        uid = force_str(urlsafe_base64_decode(uidb64))
        user = User.objects.get(pk=uid)
    except (TypeError, ValueError, OverflowError, User.DoesNotExist):
        user = None
    
    if user is not None and default_token_generator.check_token(user, token):
        if request.method == 'POST':
            form = SetPasswordForm(user, request.POST)
            if form.is_valid():
                form.save()
                messages.success(request, 'Your password has been reset successfully.')
                return redirect('user_login')
        else:
            form = SetPasswordForm(user)
        
        return render(request, 'auth/reset_password.html', {'form': form, 'uidb64': uidb64, 'token': token})
    else:
        messages.error(request, 'Invalid reset password link.')
        return redirect('user_login')
def user_logout(request):
    logout(request)
    return redirect('user_login')    

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

def follow_user(request, username):
    user = get_object_or_404(User, username=username)

    if request.user.is_authenticated:
        following = Follow.objects.filter(follower=request.user, following=user)
        if not following.exists():
            # create a new follow object
            Follow.objects.create(follower=request.user, following=user)
    return redirect('show_profile', username=user.username)

def unfollow_user(request, username):
    user = get_object_or_404(User, username=username)

    if request.user.is_authenticated:
        following = Follow.objects.filter(follower=request.user, following=user)
        if following.exists():
            # delete the existing follow object
            following.delete()
    return redirect('show_profile', username=user.username)

@login_required(login_url='user_login')
def show_profile(request, username):
    new_conversation_id = str(uuid.uuid4())
    User = get_user_model()
    user = get_object_or_404(User, username=username)

    # Retrieve or create the profile object for the user
    try:
        profile = user.profile
    except Profile.DoesNotExist:
        profile = Profile.objects.create(user=user)
    posts = Post.objects.filter(author=request.user)
    # Get notifications for current user
    notifications = Notification.objects.filter(user=request.user).order_by('-timestamp')[:10]
    unread_notifications = Notification.objects.filter(user=request.user, is_read=False)
     # Get unread notifications for the current user
    notifications = Notification.objects.filter(user=request.user).order_by('-timestamp')

        # Mark all notifications as read
    unread_notifications = Notification.objects.filter(user=request.user, is_read=False)

    # Separate notifications by type
    message_notifications = []
    post_notifications = []
    group_message_notifications = []
    group_post_notifications = []
    emoji_reaction_notifications = []
    comment_notifications = []
    emoji_reaction_group_notifications = []
    comment_group_notifications = []
    join_request_notifications = []
    for notification in unread_notifications:
        if notification.message:
            message_notifications.append(notification)
        elif notification.post:
            post_notifications.append(notification)
        elif notification.group_post:
            group_post_notifications.append(notification)     
        elif notification.group_message:
            group_message_notifications.append(notification)
        elif notification.emoji_reaction:
            emoji_reaction_notifications.append(notification)
        elif notification.comment:
            comment_notifications.append(notification)
        elif notification.emoji_reaction_group:
            emoji_reaction_group_notifications.append(notification)
        elif notification.comment_group:
            comment_group_notifications.append(notification)
        elif notification.join_request:
            join_request_notifications.append(notification)

        notification.is_read = True
        notification.save()
    form_profile = ProfileUpdateForm(request.POST, request.FILES, instance=request.user.profile)
    form_group = CreateGroupForm()
    if request.method == 'POST':
        form = CreateGroupForm(request.POST)
        if form.is_valid():
            group = form.save(commit=False)
            group.admin = request.user
            group.save()
            form.save_m2m()
            messages.success(request, 'Your group has been created successfully!')
            return redirect('show_profile', username=request.user)
    is_following = False
    following = Follow.objects.filter(follower=request.user, following=user)
    if request.user.is_authenticated:
        if request.user.username == username:  # check if the user is visiting their own profile
            if request.method == 'POST':
                form_profile = ProfileUpdateForm(request.POST, request.FILES, instance=profile)
                if form_profile.is_valid():
                    form_profile.save()
                    messages.success(request, ('Your Profile Was successfully updated'))
                else:
                    form_profile = ProfileUpdateForm(instance=request.user.profile)
            return render(request, 'profile.html', {'form_profile': form_profile, 'form_group': form_group, 'user': user, 'posts': posts, 'messages': messages.get_messages(request), 'notifications': notifications, 'unread_notifications': unread_notifications, 'new_conversation_id': new_conversation_id, 'LANGUAGES': settings.LANGUAGES})
        else:  # the user is visiting someone else's profile
            following = Follow.objects.filter(follower=request.user, following=user)
            if following.exists():
                is_following = True  
            posts = Post.objects.filter(author=user)    
            return render(request, 'public_profile.html', {'user': user, 'posts': posts, 'is_following': is_following, 'notifications': notifications, 'unread_notifications': unread_notifications, 'new_conversation_id': new_conversation_id, 'LANGUAGES': settings.LANGUAGES})
    else:  # user is not authenticated
        posts = Post.objects.filter(author=user)
        return render(request, 'public_profile.html', {'user': user, 'posts': posts, 'is_following': is_following, 'notifications': notifications, 'unread_notifications': unread_notifications, 'new_conversation_id': new_conversation_id, 'LANGUAGES': settings.LANGUAGES})

@login_required
def create_group(request):
    if request.method == 'POST':
        form = CreateGroupForm(request.POST)
        if form.is_valid():
            group = form.save(commit=False)
            group.admin = request.user
            group.save()
            form.save_m2m()
            messages.success(request, 'Your group has been created successfully!')
            return redirect('group/group_detail', pk=group.pk)
    else:
        form = GroupForm()
    context = {'form': form}
    return redirect('show_profile') 
@login_required
def delete_account(request):
    if request.method == 'POST':
        user = request.user
        user.delete()
        messages.success(request, 'Your account has been deleted.')
        logout(request)
        return redirect('home')
    return render(request, 'modals/delete_account.html')          

@login_required(login_url='get_started')
def home(request, post_id=None):
    if post_id is not None:
        post = get_object_or_404(Post, id=post_id)
    else:
        post = None

    # Retrieve group object
    group = Group.objects.filter(members=request.user).first() or Group.objects.filter(admin=request.user).first()

    # Retrieve all GroupPost objects and order by created_at descending
    group_post = GroupPost.objects.all().order_by('-created_at')
    group_message = GroupMessage.objects.all().order_by('-timestamp')

    # Create search form
    search_form = SearchForm()
    # Retrieve posts for the user and users they are following, ordered by created_at descending
    following = request.user.following.values_list('following__id', flat=True)
    posts = Post.objects.filter(Q(author=request.user) | Q(author__in=following)).order_by('-created_at')

    # Fetch emoji reactions and comments for all posts using prefetch_related
    posts = posts.prefetch_related(
        'emoji_reactions',
        Prefetch('comments', queryset=Comment.objects.order_by('-created_at'))
    )
    # Create forms for post, reaction, and comment
    form_post = PostForm()
    form_reaction = ReactionForm(initial={'post': post_id})
    form_comment = CommentForm(initial={'post': post_id})
    user = request.user
    if request.method == 'POST':
        # Handle post creation
        if 'content' in request.POST:
            form_post = PostForm(request.POST, request.FILES)
            if form_post.is_valid():
                post = form_post.save(commit=False, author=request.user)
                post.created_at = timezone.now()
                post.save()
                # Create notifications for followers
                for follower in request.user.followers.all():
                    Notification.objects.create(
                        user=follower.user,
                        post=post,
                        message=None,
                        group_message=None,
                        emoji_reaction=None,
                        comment=None,
                        emoji_reaction_group=None,
                        comment_group=None,
                        join_request=None,
                        invitation=None,
                        timestamp=timezone.now(),
                        is_read=False
                    )
                return redirect('show_post', post_id=post.id)

        # Handle comment creation
        elif 'comment' in request.POST:
            form_comment = CommentForm(request.POST)
            if form_comment.is_valid():
                comment = form_comment.save(commit=False)
                comment.author = request.user

                post_id = request.POST.get('post_id')
                if post_id:
                    post = get_object_or_404(Post, id=post_id)

                comment.post = post
                comment.created_at = timezone.now()
                comment.save()
                # for follower in request.user.followers.all():
                #     Notification.objects.create(
                #         user=follower,
                #         post=post,
                #         message=None,
                #         group_message=None,
                #         emoji_reaction=None,
                #         comment=comment,
                #         emoji_reaction_group=None,
                #         comment_group=None,
                #         join_request=None,
                #         invitation=None,
                #         timestamp=timezone.now(),
                #         is_read=False
                #     )
                return redirect('show_post', post_id=request.POST.get('post_id'))

        # Handle emoji reaction creation
        elif 'emoji' in request.POST:
            form_reaction = ReactionForm(request.POST)
            if form_reaction.is_valid():
                emoji = form_reaction.save(commit=False)
                emoji.author = request.user
                post_id = request.POST.get('post_id')
                if post_id:
                    post = get_object_or_404(Post, id=post_id)
                emoji.post = post
                emoji.created_at = timezone.now()
                emoji.save()
                # for follower in request.user.followers.all():
                #     Notification.objects.create(
                #         user=follower.user,
                #         post=post,
                #         message=None,
                #         group_message=None,
                #         emoji_reaction=emoji,
                #         comment=None,
                #         emoji_reaction_group=None,
                #         comment_group=None,
                #         join_request=None,
                #         invitation=None,
                #         timestamp=timezone.now(),
                #         is_read=False
                #     )
                return redirect('show_post', post_id=request.POST.get('post_id'))

    else:
        form_reaction = ReactionForm()
        form_comment = CommentForm()
        post_form = PostForm()    
    reactions = {}
    emoji_reactions = None
    for post in posts:
        emoji_reactions = EmojiReaction.objects.filter(post=post)
        reactions[post.id] = {}
        for reaction in emoji_reactions:
            if reaction.emoji not in reactions[post.id]:
                reactions[post.id][reaction.emoji] = 1
            else:
                reactions[post.id][reaction.emoji] += 1

    # Retrieve the comments and emoji reactions for the current post
    comments = None
    for post in posts:
        comments = Comment.objects.filter(post=post.id).order_by('-created_at')
        emoji_reactions = EmojiReaction.objects.filter(post=post).order_by('-created_at')
        reactions = EmojiReaction.objects.filter(post=post).order_by('-created_at')
        reaction_counts = {
            'heart': reactions.filter(emoji='❤️').count(),
            'thumbs_up': reactions.filter(emoji='👍').count(),
            'thumbs_down': reactions.filter(emoji='👎').count(),
            'angry': reactions.filter(emoji='😠').count(),
            'cool': reactions.filter(emoji='😎').count(),
            'smile': reactions.filter(emoji='😊').count(),
        }


    # Retrieve the comments and emoji reactions for the current post
    unread_notifications = Notification.objects.filter(user=request.user, is_read=False)
    # Mark all notifications as read
    notifications = Notification.objects.filter(user=request.user).order_by('-timestamp')[:10]
    # Separate notifications by type
     # Get unread notifications for the current user
    # notifications = Notification.objects.filter(user=request.user).order_by('-timestamp')

    #     # Mark all notifications as read
    # unread_notifications = Notification.objects.filter(user=request.user, is_read=False)
    # if post_id is not None:
    #     post = Post.objects.get(pk=post_id)
    #     comments = post.comments.all()
    #     emoji_reactions = post.emoji_reactions.all()
    # Separate notifications by type
    message_notifications = []
    post_notifications = []
    group_message_notifications = []
    group_post_notifications = []
    emoji_reaction_notifications = []
    comment_notifications = []
    emoji_reaction_group_notifications = []
    comment_group_notifications = []
    join_request_notifications = []
    for notification in unread_notifications:
        if notification.message:
            message_notifications.append(notification)
        elif notification.post:
            post_notifications.append(notification)
        elif notification.group_post:
            group_post_notifications.append(notification)     
        elif notification.group_message:
            group_message_notifications.append(notification)
        elif notification.emoji_reaction:
            emoji_reaction_notifications.append(notification)
        elif notification.comment:
            comment_notifications.append(notification)
        elif notification.emoji_reaction_group:
            emoji_reaction_group_notifications.append(notification)
        elif notification.comment_group:
            comment_group_notifications.append(notification)
        elif notification.join_request:
            join_request_notifications.append(notification)

        notification.is_read = True
        notification.save()      
    new_conversation_id = str(uuid.uuid4())
    users = User.objects.all()
    return render(request, 'home.html', {'form_post': form_post, 'search_form': search_form, 'form_comment': form_comment, 'form_reaction': form_reaction, 'posts': posts, 'reactions': reactions, 'notifications': notifications, 'unread_notifications': unread_notifications, 'message_notifications': message_notifications, 'post_notifications': post_notifications, 'group_message_notifications': group_message_notifications, 'group_post_notifications': group_post_notifications, 'comments': comments, 'emoji_reactions': emoji_reactions, 'new_conversation_id': new_conversation_id, 'LANGUAGES': settings.LANGUAGES}) 

@login_required(login_url='get_started')
def show_post(request, post_id):
    post = get_object_or_404(Post, id=post_id)

    # Retrieve all comments for the post with the given post_id
    comments = post.comments.all()

    # Retrieve all emoji reactions for the post with the given post_id
    emoji_reactions = post.emoji_reactions.all()

    reactions = post.emoji_reactions.all()

    # Retrieve group object
    group = Group.objects.filter(members=request.user).first() or Group.objects.filter(admin=request.user).first()

    # Retrieve all GroupPost objects and order by created_at descending
    group_post = GroupPost.objects.all().order_by('-created_at')
    group_message = GroupMessage.objects.all().order_by('-timestamp')

    # Create search form
    search_form = SearchForm()

    # Retrieve posts for the user and users they are following, ordered by created_at descending
    following = request.user.following.values_list('following__id', flat=True)
    posts = Post.objects.filter(Q(id=post_id) | Q(author=request.user.id) | Q(author__in=following)).order_by('-created_at').annotate(num_comments=Count('comments'))

    form_reaction = ReactionForm(initial={'post': post_id})
    form_comment = CommentForm(initial={'post': post_id})

    if request.method == 'POST':
        if 'emoji' in request.POST:
            form_reaction = ReactionForm(request.POST)
            if form_reaction.is_valid():
                emoji = form_reaction.save(commit=False)
                emoji.author = request.user
                emoji.post = post
                emoji.created_at = timezone.now()
                emoji.save()
                return redirect('show_post', post_id=post_id)
        elif 'comment' in request.POST:
            form_comment = CommentForm(request.POST)
            if form_comment.is_valid():
                comment = form_comment.save(commit=False)
                comment.author = request.user
                comment.post = post
                comment.save()
                messages.success(request, 'Comment added successfully!')
                return redirect('show_post', post_id=post_id)

    # Retrieve all reactions for each post and count them
    reactions = {}
    for p in posts:
        for reaction in p.emoji_reactions.all():
            if p.id not in reactions:
                reactions[p.id] = {}
            if reaction.emoji not in reactions[p.id]:
                reactions[p.id][reaction.emoji] = 1
            else:
                reactions[p.id][reaction.emoji] += 1
    
    unread_notifications = Notification.objects.filter(user=request.user, is_read=False)
    reactions = post.emoji_reactions.all()
    reaction_counts = {
            'heart': reactions.filter(emoji='❤️').count(),
            'thumbs_up': reactions.filter(emoji='👍').count(),
            'thumbs_down': reactions.filter(emoji='👎').count(),
            'angry': reactions.filter(emoji='😠').count(),
            'cool': reactions.filter(emoji='😎').count(),
            'smile': reactions.filter(emoji='😊').count(),
        }
            
    posts_author = Post.objects.filter(author__in=[request.user])
    unread_notifications = Notification.objects.filter(user=request.user, is_read=False)

    # Mark all notifications as read
    notifications = Notification.objects.filter(user=request.user).order_by('-timestamp')[:10]

     # Get unread notifications for the current user
    notifications = Notification.objects.filter(user=request.user).order_by('-timestamp')

        # Mark all notifications as read
    unread_notifications = Notification.objects.filter(user=request.user, is_read=False)

    # Separate notifications by type
    message_notifications = []
    post_notifications = []
    group_message_notifications = []
    group_post_notifications = []
    emoji_reaction_notifications = []
    comment_notifications = []
    emoji_reaction_group_notifications = []
    comment_group_notifications = []
    join_request_notifications = []
    for notification in unread_notifications:
        if notification.message:
            message_notifications.append(notification)
        elif notification.post:
            post_notifications.append(notification)
        elif notification.group_post:
            group_post_notifications.append(notification)     
        elif notification.group_message:
            group_message_notifications.append(notification)
        elif notification.emoji_reaction:
            emoji_reaction_notifications.append(notification)
        elif notification.comment:
            comment_notifications.append(notification)
        elif notification.emoji_reaction_group:
            emoji_reaction_group_notifications.append(notification)
        elif notification.comment_group:
            comment_group_notifications.append(notification)
        elif notification.join_request:
            join_request_notifications.append(notification)

        notification.is_read = True
        notification.save()     
    new_conversation_id = str(uuid.uuid4()) 
    return render(request, 'post/show_post.html', {'search_form': search_form, 'form_comment': form_comment, 'form_reaction': form_reaction, 'post': post, 'comments': comments, 'emoji_reactions': emoji_reactions, 'reactions': reactions, 'posts_author': posts_author, 'notifications': notifications, 'unread_notifications': unread_notifications, 'new_conversation_id': new_conversation_id, 'group': group, 'LANGUAGES': settings.LANGUAGES})

def edit_comment(request, post_id, comment_id):
    new_conversation_id = str(uuid.uuid4())
    comment = Comment.objects.get(id=comment_id)
    if request.method == 'POST':
        form_comment = CommentForm(request.POST, instance=comment)
        if form_comment.is_valid():
            comment = form.save()
            if request.is_ajax():
                return JsonResponse({'success': True})
            else:
                messages.success(request, 'Post updated successfully!')
                return redirect('show_post', post_id=post_id)
        else:
            if request.is_ajax():
                return JsonResponse({'success': False, 'errors': form.errors})
    else:
        form = PostForm(instance=post)
        context = {'form': form, 'new_conversation_id': new_conversation_id}
        return render(request, 'modals/edit_post.html', context)
def delete_comment(request, post_id, comment_id):
    new_conversation_id = str(uuid.uuid4())
    comment = get_object_or_404(Comment, id=comment_id)
    if request.method == 'POST':
        comment.delete()
        messages.success(request, 'Your post has been deleted!')
        return redirect('show_post', post_id=post_id)

    data = {
        'new_conversation_id': new_conversation_id,

    }

    if request.META.get('HTTP_X_REQUESTED_WITH') == 'XMLHttpRequest':
        html = render_to_string('delete_post_modal.html', data, request=request)
        return JsonResponse({'html': html})    
    return render(request, 'modals/delete_post.html', data) 
 
def get_started(request):
    new_conversation_id = str(uuid.uuid4())
    if request.user.is_authenticated:
        return redirect('home')
    else:
        return render(request, 'get_started.html', {'new_conversation_id': new_conversation_id})  
User = get_user_model()
@login_required
def search_users(request):
    users = []
    search_form = SearchForm(request.GET)
    if 'search' in request.POST:
        if search_form.is_valid():
            query = search_form.cleaned_data['query']
            users = User.objects.filter(username__icontains=query)
            threads = Message.get_user_threads(request.user)
            threads_dict = {t.user.username: t for t in threads}
            threads_to_display = [threads_dict.get(user.username) for user in users]
            context = {'users': users, 'threads': threads_to_display}
            return render(request, 'modals/search.html', context)
    else:
        context = {}

    # Separate notifications by type
    unread_notifications = Notification.objects.filter(user=request.user, is_read=False)

    # Mark all notifications as read
    notifications = Notification.objects.filter(user=request.user).order_by('-timestamp')
    message_notifications = []
    post_notifications = []
    group_message_notifications = []
    group_post_notifications = []
    emoji_reaction_notifications = []
    comment_notifications = []
    emoji_reaction_group_notifications = []
    comment_group_notifications = []
    join_request_notifications = []
    for notification in unread_notifications:
        if notification.message:
            message_notifications.append(notification)
        elif notification.post:
            post_notifications.append(notification)
        elif notification.group_post:
            group_post_notifications.append(notification)     
        elif notification.group_message:
            group_message_notifications.append(notification)
        elif notification.emoji_reaction:
            emoji_reaction_notifications.append(notification)
        elif notification.comment:
            comment_notifications.append(notification)
        elif notification.emoji_reaction_group:
            emoji_reaction_group_notifications.append(notification)
        elif notification.comment_group:
            comment_group_notifications.append(notification)
        elif notification.join_request:
            join_request_notifications.append(notification)

        notification.is_read = True
        notification.save()        
    new_conversation_id = str(uuid.uuid4()) 
    context.update({'search_form': search_form, 'notifications': notifications, 'unread_notifications': unread_notifications, 'new_conversation_id': new_conversation_id, 'LANGUAGES': settings.LANGUAGES})   
    return render(request, 'modals/search.html', context)
             
@login_required
def search(request):
    # Get notifications for current user
    notifications = Notification.objects.filter(user=request.user).order_by('-timestamp')[:10]
    unread_notifications = Notification.objects.filter(user=request.user, is_read=False)
    search_form = SearchForm()
    users = []
    posts = []
    groups = []
    if 'search' in request.POST:
        search_form = SearchForm(request.POST)
        if search_form.is_valid():
            query = search_form.cleaned_data['query']
            users = User.objects.filter(username__icontains=query)
            posts = Post.objects.filter(content__icontains=query)
            groups = Group.objects.filter(name__icontains=query)

    # Separate notifications by type
    message_notifications = []
    post_notifications = []
    group_message_notifications = []
    group_post_notifications = []
    emoji_reaction_notifications = []
    comment_notifications = []
    emoji_reaction_group_notifications = []
    comment_group_notifications = []
    join_request_notifications = []
    for notification in unread_notifications:
        if notification.message:
            message_notifications.append(notification)
        elif notification.post:
            post_notifications.append(notification)
        elif notification.group_post:
            group_post_notifications.append(notification)     
        elif notification.group_message:
            group_message_notifications.append(notification)
        elif notification.emoji_reaction:
            emoji_reaction_notifications.append(notification)
        elif notification.comment:
            comment_notifications.append(notification)
        elif notification.emoji_reaction_group:
            emoji_reaction_group_notifications.append(notification)
        elif notification.comment_group:
            comment_group_notifications.append(notification)
        elif notification.join_request:
            join_request_notifications.append(notification)

        notification.is_read = True
        notification.save()        
    new_conversation_id = str(uuid.uuid4())
    return render(request, 'results_search.html', {'users': users, 'posts': posts, 'search_form': search_form, 'notifications': notifications, 'unread_notifications': unread_notifications, 'new_conversation_id': new_conversation_id, 'LANGUAGES': settings.LANGUAGES})
@login_required
def update_post(request, post_id):
    new_conversation_id = str(uuid.uuid4())
    post = get_object_or_404(Post, id=post_id, author=request.user)
    if request.method == 'POST':
        form = PostForm(request.POST, instance=post)
        if form.is_valid():
            post = form.save(commit=False)
            post.author = request.user
            post.group = post.group # assuming the group is not being modified
            post.save()
            if request.is_ajax():
                return JsonResponse({'success': True})
            else:
                messages.success(request, 'Post updated successfully!')
                return redirect('show_profile', username=request.user)
        else:
            if request.is_ajax():
                return JsonResponse({'success': False, 'errors': form.errors})
    else:
        form = PostForm(instance=post)
        context = {'form': form, 'new_conversation_id': new_conversation_id}
        return render(request, 'modals/edit_post.html', context)
@login_required
def delete_post(request, post_id):
    new_conversation_id = str(uuid.uuid4())
    post = get_object_or_404(Post, id=post_id, author=request.user)

    if request.method == 'POST':
        post.delete()
        messages.success(request, 'Your post has been deleted!')
        return redirect('show_profile', username=request.user)

    data = {
        'post': post,
        'new_conversation_id': new_conversation_id,

    }

    if request.META.get('HTTP_X_REQUESTED_WITH') == 'XMLHttpRequest':
        html = render_to_string('delete_post_modal.html', data, request=request)
        return JsonResponse({'html': html})    
    return render(request, 'modals/delete_post.html', data) 
@login_required
def update_post_group(request, post_id):
    new_conversation_id = str(uuid.uuid4())
    post = get_object_or_404(GroupPost, id=post_id, author=request.user)
    if request.method == 'POST':
        form = GroupPostForm(request.POST, instance=post)
        if form.is_valid():
            post = form.save(commit=False)
            post.author = request.user
            post.group = post.group  # assuming the group is not being modified
            post.save()
            if request.is_ajax():
                return JsonResponse({'success': True})
            else:
                messages.success(request, 'Post updated successfully!')
                return redirect('group_detail', name=post.group.name, pk=post.group.pk)
        else:
            if request.is_ajax():
                return JsonResponse({'success': False, 'errors': form.errors})
    else:
        form = GroupPostForm(instance=post)
        context = {'form': form, 'new_conversation_id': new_conversation_id}
        return render(request, 'modals/edit_post.html', context)


@login_required
def delete_post_group(request, post_id):
    new_conversation_id = str(uuid.uuid4())
    post = get_object_or_404(GroupPost, id=post_id, author=request.user)

    if request.method == 'POST':
        group = post.group  # Get the associated group
        post.delete()
        messages.success(request, 'Your post has been deleted!')
        return redirect('group_detail', name=group.name, pk=group.pk)

    data = {
        'post': post,
        'new_conversation_id': new_conversation_id,
    }

    if request.META.get('HTTP_X_REQUESTED_WITH') == 'XMLHttpRequest':
        html = render_to_string('delete_post_modal.html', data, request=request)
        return JsonResponse({'html': html})
    return render(request, 'modals/delete_post.html', data)

@login_required
def edit_comment_group(request, post_id, comment_id):
    new_conversation_id = str(uuid.uuid4())
    post = get_object_or_404(GroupPost, id=post_id, author=request.user)
    comment = get_object_or_404(CommentGroup, id=comment_id, author=request.user)
    if request.method == 'POST':
        form = CommentFormGroup(request.POST, instance=comment)
        if form.is_valid():
            group = post.group
            comment = form.save(commit=False)
            comment.save()
            if request.is_ajax():
                return JsonResponse({'success': True})
            else:
                messages.success(request, 'Comment updated successfully!')
                return redirect('group_detail', name=group.name, pk=group.pk)
        else:
            if request.is_ajax():
                return JsonResponse({'success': False, 'errors': form.errors})
    else:
        form = CommentFormGroup(instance=comment)
        context = {'form': form, 'new_conversation_id': new_conversation_id}
        return render(request, 'modals/edit_comment.html', context)


@login_required
def delete_comment_group(request, post_id, comment_id):
    new_conversation_id = str(uuid.uuid4())
    comment = get_object_or_404(CommentGroup, id=comment_id, author=request.user)
    post = get_object_or_404(GroupPost, id=post_id, author=request.user)
    if request.method == 'POST':
        group = post.group
        comment.delete()
        messages.success(request, 'Your comment has been deleted!')
        return redirect('group_detail', name=group.name, pk=group.pk)

    data = {
        'comment': comment,
        'new_conversation_id': new_conversation_id,
    }

    if request.META.get('HTTP_X_REQUESTED_WITH') == 'XMLHttpRequest':
        html = render_to_string('delete_comment_modal.html', data, request=request)
        return JsonResponse({'html': html})
    return render(request, 'modals/delete_comment.html', data)

@login_required(login_url='get_started')
def chatbotTrade(request, post_id=None, conversation_id=None):
    if post_id is not None:
        post = get_object_or_404(Post, id=post_id)
    else:
        post = None
        
    # Generate a new conversation ID if none is provided
    if not conversation_id:
        conversation_id = str(uuid.uuid4()) 
    
    # Get the user's followers
    following = request.user.following.values_list('following__id', flat=True)    
    
    # Get all posts by the user and their followers
    posts = Post.objects.filter(Q(author=request.user) | Q(author__in=following)).order_by('-created_at')    
    form = ChatbotForm()
    response = None
    history = []
    user = request.user
    saved_chats = ChatHistory.objects.filter(user=request.user).order_by('timestamp')[:4]
    chats = ChatHistory.objects.filter(user=request.user, conversation_id=conversation_id).order_by('timestamp')
    # Check for prompt parameter in GET request
    prompt = request.GET.get('prompt')
    if prompt:
        form = ChatbotForm(initial={'prompt': prompt})
        history.append(('User', prompt))

    if request.method == 'POST':
        form = ChatbotForm(request.POST)
        if form.is_valid():
            prompt = form.cleaned_data['prompt']
            history.append(("You", prompt))
            user_lang = detect(prompt)
            completions = openai.Completion.create(
                engine="text-davinci-002",
                prompt=prompt,
                max_tokens=4000,
                n=2,
                stop=None,
                temperature=0.5,
            )
            response = completions.choices[0].text
            if user_lang != 'en':
                translated_response = _(response)
                response = str(translated_response)
            history.append(("Chatbot", response))

            # Try to create a new ChatHistory record
            try:
                chat_history = ChatHistory.objects.create(
                    user=user,
                    prompt=prompt,
                    response=response,
                    conversation_id=conversation_id
                )
            except IntegrityError:
                # If a duplicate conversation ID is detected, update the existing record
                chat_history = ChatHistory.objects.get(conversation_id=conversation_id)
                chat_history.prompt = prompt
                chat_history.response = response
                chat_history.save()

            return redirect('chatbotTrade', conversation_id=conversation_id)

    elif request.method == 'GET' and 'new' in request.GET:
        # Clear the history list when the new conversation button is clicked
        history = []
        response = None
        form = ChatbotForm()

    elif request.method == 'GET' and 'history' in request.GET:
        chat_id = request.GET.get('history')
        history_chat = ChatHistory.objects.filter(user=user, id=chat_id).first()
        if history_chat:
            prompt = history_chat.prompt
            response = history_chat.response
            form = ChatbotForm(initial={'prompt': prompt})
            history.append(('User', prompt))
            history.append(('Chatbot', response))

    unread_notifications = Notification.objects.filter(user=request.user, is_read=False)
    # Mark all notifications as read
    notifications = Notification.objects.filter(user=request.user).order_by('-timestamp')[:10]
    # Separate notifications by type
    message_notifications = []
    post_notifications = []
    group_message_notifications = []
    group_post_notifications = []
    for notification in notifications:
        if notification.message:
            message_notifications.append(notification)
        elif notification.post:
            post_notifications.append(notification)
        elif notification.group_post:
            group_post_notifications.append(notification)
        elif notification.group_message:
            group_message_notifications.append(notification)
            notification.is_read = True
            notification.save()

    new_conversation_id = str(uuid.uuid4())

    return render(request, 'chatbot/chatbotTrade.html', {
        'form': form,
        'history': history,
        'saved_chats': saved_chats,
        'unread_notifications': unread_notifications,
        'notifications': notifications,
        'message_notifications': message_notifications,
        'post_notifications': post_notifications,
        'group_message_notifications': group_message_notifications,
        'new_conversation_id': new_conversation_id,
        'LANGUAGES': settings.LANGUAGES
    })
@login_required(login_url='get_started')
def chatbot(request, post_id=None, conversation_id=None):
    if post_id is not None:
        post = get_object_or_404(Post, id=post_id)
    else:
        post = None
        
    # Generate a new conversation ID if none is provided
    if not conversation_id:
        conversation_id = str(uuid.uuid4()) 
    
    # Get the user's followers
    following = request.user.following.values_list('following__id', flat=True)    
    
    # Get all posts by the user and their followers
    posts = Post.objects.filter(Q(author=request.user) | Q(author__in=following)).order_by('-created_at')    
    form = ChatbotForm()
    response = None
    history = []
    user = request.user
    saved_chats = ChatHistory.objects.filter(user=request.user).order_by('timestamp')[:4]
    chats = ChatHistory.objects.filter(user=request.user, conversation_id=conversation_id).order_by('timestamp')
    # Check for prompt parameter in GET request
    prompt = request.GET.get('prompt')
    if prompt:
        form = ChatbotForm(initial={'prompt': prompt})
        history.append(('User', prompt))

    if request.method == 'POST':
        form = ChatbotForm(request.POST)
        if form.is_valid():
            prompt = form.cleaned_data['prompt']
            history.append(("You", prompt))
            user_lang = detect(prompt)
            completions = openai.Completion.create(
                engine="text-davinci-002",
                prompt=prompt,
                max_tokens=4000,
                n=2,
                stop=None,
                temperature=0.5,
            )
            response = completions.choices[0].text
            if user_lang != 'en':
                translated_response = _(response)
                response = str(translated_response)
            history.append(("Chatbot", response))

            # Try to create a new ChatHistory record
            try:
                chat_history = ChatHistory.objects.create(
                    user=user,
                    prompt=prompt,
                    response=response,
                    conversation_id=conversation_id
                )
            except IntegrityError:
                # If a duplicate conversation ID is detected, update the existing record
                chat_history = ChatHistory.objects.get(conversation_id=conversation_id)
                chat_history.prompt = prompt
                chat_history.response = response
                chat_history.save()

            return redirect('chatbot', conversation_id=conversation_id)

    elif request.method == 'GET' and 'new' in request.GET:
        # Clear the history list when the new conversation button is clicked
        history = []
        response = None
        form = ChatbotForm()

    elif request.method == 'GET' and 'history' in request.GET:
        chat_id = request.GET.get('history')
        history_chat = ChatHistory.objects.filter(user=user, id=chat_id).first()
        if history_chat:
            prompt = history_chat.prompt
            response = history_chat.response
            form = ChatbotForm(initial={'prompt': prompt})
            history.append(('User', prompt))
            history.append(('Chatbot', response))

    unread_notifications = Notification.objects.filter(user=request.user, is_read=False)
    # Mark all notifications as read
    notifications = Notification.objects.filter(user=request.user).order_by('-timestamp')[:10]
    # Separate notifications by type
    message_notifications = []
    post_notifications = []
    group_message_notifications = []
    group_post_notifications = []
    for notification in notifications:
        if notification.message:
            message_notifications.append(notification)
        elif notification.post:
            post_notifications.append(notification)
        elif notification.group_post:
            group_post_notifications.append(notification)
        elif notification.group_message:
            group_message_notifications.append(notification)
            notification.is_read = True
            notification.save()

    new_conversation_id = str(uuid.uuid4())        
    return render(request, 'chatbot/chatbot.html', {'form': form, 'response': response, 'history': history, 'saved_chats': saved_chats, 'conversation_id': conversation_id, 'new_conversation_id': new_conversation_id, 'LANGUAGES': settings.LANGUAGES})

@login_required(login_url='login')
def delete_chat(request, timestamp, conversation_id):
    user = request.user
    chat_history = get_object_or_404(ChatHistory, user=request.user, timestamp=timestamp, conversation_id=conversation_id)
    chat_history.delete()
    if conversation_id is None:
        conversation_id = str(uuid.uuid4())
    return redirect('chatbotTrade', conversation_id=conversation_id)
@login_required
def delete_group(request, name, pk):
    group = get_object_or_404(Group, name=name, pk=pk)
    if group.admin != request.user:
        messages.error(request, "You are not the admin of this group.")
        return redirect('group_detail', name=name, pk=pk)

    if request.method == 'POST':
        group.delete()
        messages.success(request, "Group has been deleted.")
        return redirect('show_profile')

    return render(request, 'myapp/delete_group.html', {'group': group})  
@login_required
def message_thread(request, username):
    unread_messages = Message.objects.filter(recipient=request.user, is_read=False)
    recipient = get_object_or_404(get_user_model(), username=username)
    # Get all messages sent by the current user to the recipient and all messages received by the current user from the recipient
    messages_sent = Message.objects.filter(sender=request.user, recipient=recipient)
    messages_received = Message.objects.filter(sender=recipient, recipient=request.user)
    
    # Merge the sent and received messages into one queryset and order by timestamp
    conversations = messages_sent.union(messages_received).order_by('timestamp')

    if request.method == 'POST':
        form = MessageForm(request.POST)
        if form.is_valid():
            message = form.save(commit=False)
            message.sender = request.user
            message.recipient = recipient
            message.save()

            # Check if a notification already exists for the recipient and the message
            existing_notification = Notification.objects.filter(
                Q(user=recipient) & Q(message=message)
            ).first()

            if existing_notification:
                existing_notification.timestamp = timezone.now()
                existing_notification.is_read = False
                existing_notification.save()
            else:
                Notification.objects.create(
                    user=recipient,
                    post=None, 
                    message=message,
                    group_message=None,
                    invitation=None,
                    timestamp=timezone.now(),
                    is_read=False
                )

            # Send real-time message to recipient
            channel_layer = get_channel_layer()
            if request.user.profile.image:
                sender_image = str(request.user.profile.image.url)
            else:
                sender_image = None

            async_to_sync(channel_layer.group_send)(
                f"chat_{recipient.username}",
                {
                    "type": "chat_message",
                    "message": {
                        "sender": request.user.username,
                        "sender_image": sender_image,
                        "recipient": recipient.username,
                        "content": message.content,
                        "timestamp": str(timezone.now())
                    }
                }
            )


            return redirect('message_thread', username=username)
    else:
        form = MessageForm()

    # Get notifications for current user
    notifications = Notification.objects.filter(user=request.user).order_by('-timestamp')[:10]
    unread_notifications = Notification.objects.filter(user=request.user, is_read=False)
    
    # Separate notifications by type
    message_notifications = []
    post_notifications = []
    group_message_notifications = []
    group_post_notifications = []
    emoji_reaction_notifications = []
    comment_notifications = []
    emoji_reaction_group_notifications = []
    comment_group_notifications = []
    join_request_notifications = []
    for notification in unread_notifications:
        if notification.message:
            message_notifications.append(notification)
        elif notification.post:
            post_notifications.append(notification)
        elif notification.group_post:
            group_post_notifications.append(notification)     
        elif notification.group_message:
            group_message_notifications.append(notification)
        elif notification.emoji_reaction:
            emoji_reaction_notifications.append(notification)
        elif notification.comment:
            comment_notifications.append(notification)
        elif notification.emoji_reaction_group:
            emoji_reaction_group_notifications.append(notification)
        elif notification.comment_group:
            comment_group_notifications.append(notification)
        elif notification.join_request:
            join_request_notifications.append(notification)

        notification.is_read = True
        notification.save()
    # Get sender user object
    sender = User.objects.get(username=request.user.username)
    new_conversation_id = str(uuid.uuid4())
    return render(request, 'chat/message_thread.html', {'unread_messages': unread_messages, 'recipient': recipient, 'messages': conversations, 'form': form, 'sender': sender, 'notifications': notifications, 'messages_received':messages_received, 'unread_notifications': unread_notifications, 'new_conversation_id': new_conversation_id, 'LANGUAGES': settings.LANGUAGES})

@login_required(login_url='get_started')
def chat_group_detail(request, name, pk):
    User = get_user_model()
    user = request.user
    group = get_object_or_404(Group, pk=pk)
    is_admin = request.user == group.admin
     # Get notifications for current user
    notifications = Notification.objects.filter(user=request.user).order_by('-timestamp')[:10]
    unread_notifications = Notification.objects.filter(user=request.user, is_read=False)
    messages = group.messages.order_by('timestamp')

    unread_messages = GroupMessage.objects.filter(sender=request.user, is_read=False)
    sender = get_object_or_404(get_user_model(), username=user.username)
    # Get all messages sent by the current user to the recipient and all messages received by the current user from the recipient
    messages_sent = GroupMessage.objects.filter(sender=sender)
    messages_received = GroupMessage.objects.filter(sender=request.user)
    
    # Merge the sent and received messages into one queryset and order by timestamp
    conversations = messages_sent.union(messages_received).order_by('timestamp')

    if request.method == 'POST':
        form = GroupMessageForm(request.POST)
        if form.is_valid():
            message = form.save(commit=False)
            message.sender = request.user
            message.group = group
            message.save()

            # Send real-time message to chat group
            channel_layer = get_channel_layer()
            if request.user.profile.image:
                sender_image = str(request.user.profile.image.url)
            else:
                sender_image = None
            async_to_sync(channel_layer.group_send)(
                f"group_{group.name}",
                {
                    "type": "chat_group_message",
                    "message": {
                        "sender": request.user.username,
                        "sender_image": sender_image,
                        "chat_group": group.name,
                        "body": message.message,
                        "timestamp": str(timezone.now())
                    }
                }
            )
            for member in group.members.all():
                if member.user != request.user:
                    Notification.objects.create(
                        user=member.user,
                        message=message,
                        chat_group=group,
                        notification_type='group'
                    )

            # Send message to group members using channels
            async_to_sync(channel_layer.group_send)(
                f"group_{group.id}", {
                    "type": "group.message",
                    "message": message.message,
                    "group_pk": group.pk
                }
            )

            return redirect('chat_group_detail', name=group.name, pk=group.pk)

    else:
        form = GroupMessageForm()
     # Separate notifications by type
    message_notifications = []
    post_notifications = []
    group_message_notifications = []
    group_post_notifications = []
    emoji_reaction_notifications = []
    comment_notifications = []
    emoji_reaction_group_notifications = []
    comment_group_notifications = []
    join_request_notifications = []
    for notification in unread_notifications:
        if notification.message:
            message_notifications.append(notification)
        elif notification.post:
            post_notifications.append(notification)
        elif notification.group_post:
            group_post_notifications.append(notification)     
        elif notification.group_message:
            group_message_notifications.append(notification)
        elif notification.emoji_reaction:
            emoji_reaction_notifications.append(notification)
        elif notification.comment:
            comment_notifications.append(notification)
        elif notification.emoji_reaction_group:
            emoji_reaction_group_notifications.append(notification)
        elif notification.comment_group:
            comment_group_notifications.append(notification)
        elif notification.join_request:
            join_request_notifications.append(notification)

        notification.is_read = True
        notification.save()
    # Get sender user object
    sender = User.objects.get(username=request.user.username)
    new_conversation_id = str(uuid.uuid4())
    # Render template with context
    return render(request, 'chat/group_chat.html', {'group': group, 'unread_messages': unread_messages, 'messages': conversations, 'messages': messages, 'form': form, 'sender': sender, 'notifications': notifications, 'messages_received':messages_received, 'unread_notifications': unread_notifications, 'new_conversation_id': new_conversation_id, 'LANGUAGES': settings.LANGUAGES})

def contact_us(request):
    if request.method == 'POST':
        name = request.POST['name']
        email = request.POST['email']
        message = request.POST['message']

        # Prepare the email content
        #html_content = render_to_string('about/contact_us.html', {'name': name, 'email': email, 'message': message})
        #text_content = strip_tags(html_content)

        # Create the EmailMultiAlternatives object
        msg = EmailMultiAlternatives(
            subject=f'New message from {name}',
            body=message,
            from_email=email,
            to=[settings.ADMIN_EMAIL],
        )

        # Attach the HTML content
        #msg.attach_alternative(message, 'plain')

        # Send the email
        msg.send()

        messages.success(request, 'Thank you for contacting us! We will get back to you as soon as possible.')
        return redirect('contact_us')

    if request.user.is_authenticated:
        unread_notifications = Notification.objects.filter(user=request.user, is_read=False).order_by('-timestamp')[:10]
        notifications = Notification.objects.filter(user=request.user).order_by('-timestamp')[:10]
    else:
        unread_notifications = []
        notifications = []

    # Mark all notifications as read
    for notification in unread_notifications:
        notification.is_read = True
        notification.save()

    new_conversation_id = str(uuid.uuid4())

    return render(request, 'about/contact_us.html', {
        'unread_notifications': unread_notifications,
        'notifications': notifications,
        'new_conversation_id': new_conversation_id,
        'LANGUAGES': settings.LANGUAGES
    })
@login_required
def join_group(request, pk):
    new_conversation_id = str(uuid.uuid4())
    group = get_object_or_404(Group, pk=pk)
    if request.method == 'POST':
        if not group.is_member(request.user):
            join_request = JoinRequest(user=request.user, group=group)
            join_request.save()
            messages.success(request, f"Your join request has been sent to the {group.name} group's admin for approval.")
        else:
            messages.warning(request, f"You are already a member of the {group.name} group.")
        return redirect('group_detail', pk=pk)
    return render(request, 'groups/group_detail.html', {'group': group})

@login_required
def join_requests(request, pk):
    new_conversation_id = str(uuid.uuid4())
    group = get_object_or_404(Group, pk=pk)
    if request.user != group.admin:
        raise PermissionDenied
    join_requests = JoinRequest.objects.filter(group=group).order_by('-created_at')
    return render(request, 'modals/join_requests.html', {'group': group, 'join_requests': join_requests, 'new_conversation_id': new_conversation_id})
@login_required
def approve_join_request(request, group_pk, join_request_pk):
    group = get_object_or_404(Group, pk=group_pk)
    join_request = get_object_or_404(JoinRequest, pk=join_request_pk)
    if request.user != group.admin:
        raise PermissionDenied
    if request.method == 'POST':
        action = request.POST.get('action')
        if action == 'approve':
            group.add_member(join_request.user)
            join_request.delete()
            messages.success(request, f"{join_request.user} has been added to the {group.name}")
            return redirect('group_detail', group.pk)
    return render(request, 'modals/approve_join_request.html', {'group': group, 'join_request': join_request})

@login_required
def leave_group(request, pk):
    group = get_object_or_404(Group, pk=pk)
    if group.is_member(request.user):
        group.remove_member(request.user)
        messages.success(request, f'You have left {group.name}.')
    else:
        messages.warning(request, 'You are not a member of this group.')
    return redirect('groups:group_detail', pk=pk)      
@login_required(login_url='get_started')
def group_detail(request, name, pk, post_id=None):
    if post_id is not None:
        post = get_object_or_404(GroupPost, id=post_id)
    else:
        post = None

    # Retrieve group object
    group = Group.objects.filter(members=request.user).first() or Group.objects.filter(admin=request.user).first()

    # Retrieve all GroupPost objects and order by created_at descending
    group_post = GroupPost.objects.all().order_by('-created_at')
    group_message = GroupMessage.objects.all().order_by('-timestamp')

    # Create search form
    search_form = SearchForm()
    # Retrieve posts for the user and users they are following, ordered by created_at descending
    following = request.user.following.values_list('following__id', flat=True)
    posts = GroupPost.objects.all().order_by('-created_at')

    # Fetch emoji reactions and comments for all posts using prefetch_related
    posts = posts.prefetch_related(
        'emoji_reactions_group',
        Prefetch('comments_group', queryset=CommentGroup.objects.order_by('-created_at'))
    )
    # Create forms for post, reaction, and comment
    is_admin = request.user == group.admin
    form_update = UpdateGroupForm()
    if request.method == 'POST':
        if is_admin:
            form_update = UpdateGroupForm(request.POST, request.FILES, instance=group)
            if form_update.is_valid():
                form_update.save()
                return redirect('group_detail', name=group.name, pk=group.pk)
        else:
            messages.warning(request, 'You are not allowed to edit this group.')
    else:
        form_update = UpdateGroupForm(instance=group)
    
    post_form = GroupPostForm()
    form_reaction = EmojiReactionFormGroup(initial={'post': post_id})
    form_comment = CommentFormGroup(initial={'post': post_id})
    search_form = SearchForm()
    reactions = []
    user = request.user
    if request.method == 'POST':
        if 'content' in request.POST:
            post_form = GroupPostForm(request.POST, request.FILES)
            if post_form.is_valid():
                post = post_form.save(commit=False)
                post.author = request.user
                post.created_at = timezone.now()
                post.group = group
                post.save()
                messages.success(request, 'Post created successfully!')
                for member in group.members.all():
                    Notification.objects.create(
                        user=member,
                        post=None,
                        group_post=post,
                        message=None,
                        group_message=None,
                        invitation=None,
                        timestamp=timezone.now(),
                        is_read=False
                    )
                return redirect('group_detail', name=group.name, pk=group.pk)
        elif 'comment' in request.POST:
            form_comment = CommentFormGroup(request.POST)
            if form_comment.is_valid():
                comment = form_comment.save(commit=False)
                comment.author = request.user
                comment.group = group
                post_id = request.POST.get('post_id')
                if post_id:
                    post = get_object_or_404(GroupPost, id=post_id)
                comment.post = post
                comment.created_at = timezone.now()
                comment.save()
                return redirect('show_group_post', group_name=group.name, post_id=request.POST.get('post_id')) 

        # Handle emoji reaction creation
        elif 'emoji' in request.POST:
            form_reaction = EmojiReactionFormGroup(request.POST)
            if form_reaction.is_valid():
                emoji = form_reaction.save(commit=False)
                emoji.author = request.user
                emoji.group = group
                post_id = request.POST.get('post_id')
                if post_id:
                    post = get_object_or_404(GroupPost, id=post_id)
                emoji.post = post  # Here you assign the `post` value, but it may be None
                emoji.created_at = timezone.now()
                emoji.save()
                return redirect('show_group_post', group_name=group.name, post_id=request.POST.get('post_id'))
  
    else:
        form_reaction = EmojiReactionFormGroup()
        form_comment = CommentFormGroup()
        post_form = GroupPostForm()    
    reactions = {}
    emoji_reactions = None
    for post in posts:
        emoji_reactions = EmojiReactionGroup.objects.filter(post=post)
        reactions[post.id] = {}
        for reaction in emoji_reactions:
            if reaction.emoji not in reactions[post.id]:
                reactions[post.id][reaction.emoji] = 1
            else:
                reactions[post.id][reaction.emoji] += 1

    # Retrieve the comments and emoji reactions for the current post
    user = request.user
    is_member = user in group.members.all()
    is_admin = user == group.admin
    posts_author = Post.objects.filter(author__in=[request.user])
    comments = None
    for post in posts:
        comments = CommentGroup.objects.filter(post=post.id).order_by('-created_at')
        emoji_reactions = EmojiReactionGroup.objects.filter(post=post).order_by('-created_at')
        reactions = EmojiReactionGroup.objects.filter(post=post).order_by('-created_at')
        reaction_counts = {
            'heart': reactions.filter(emoji='❤️').count(),
            'thumbs_up': reactions.filter(emoji='👍').count(),
            'thumbs_down': reactions.filter(emoji='👎').count(),
            'angry': reactions.filter(emoji='😠').count(),
            'cool': reactions.filter(emoji='😎').count(),
            'smile': reactions.filter(emoji='😊').count(),
        }
            
    posts_author = GroupPost.objects.filter(author__in=[request.user])
    unread_notifications = Notification.objects.filter(user=request.user, is_read=False)

    # Mark all notifications as read
    notifications = Notification.objects.filter(user=request.user).order_by('-timestamp')[:10]

    # Separate notifications by type
    message_notifications = []
    post_notifications = []
    group_message_notifications = []
    group_post_notifications = []
    emoji_reaction_notifications = []
    comment_notifications = []
    emoji_reaction_group_notifications = []
    comment_group_notifications = []
    join_request_notifications = []
    for notification in unread_notifications:
        if notification.message:
            message_notifications.append(notification)
        elif notification.post:
            post_notifications.append(notification)
        elif notification.group_post:
            group_post_notifications.append(notification)     
        elif notification.group_message:
            group_message_notifications.append(notification)
        elif notification.emoji_reaction:
            emoji_reaction_notifications.append(notification)
        elif notification.comment:
            comment_notifications.append(notification)
        elif notification.emoji_reaction_group:
            emoji_reaction_group_notifications.append(notification)
        elif notification.comment_group:
            comment_group_notifications.append(notification)
        elif notification.join_request:
            join_request_notifications.append(notification)

        notification.is_read = True
        notification.save()

    # Get the total count of unread notifications
    unread_count = len(unread_notifications)     
    new_conversation_id = str(uuid.uuid4()) 
    return render(request, 'group/group_detail.html', {'group': group, 'posts': posts, 'reactions': reactions, 'search_form': search_form, 'post_form': post_form, 'form_reaction': form_reaction, 'form_comment': form_comment, 'form_update': form_update, 'is_member': is_member, 'is_admin': is_admin, 'notifications': notifications, 'unread_notifications': unread_notifications, 'reactions': reactions, 'emoji_reactions': emoji_reactions, 'comments': comments, 'reaction_counts': reaction_counts, 'new_conversation_id': new_conversation_id, 'LANGUAGES': settings.LANGUAGES}) 

def terms_of_service(request):
    new_conversation_id = str(uuid.uuid4())
    return render(request, 'about/terms_of_service.html', {'new_conversation_id': new_conversation_id})
def privacy_policy(request):
    new_conversation_id = str(uuid.uuid4())
    return render(request, 'about/privacy_policy.html', {'new_conversation_id': new_conversation_id})
def about_us(request):
    new_conversation_id = str(uuid.uuid4())
    return render(request, 'about/about_us.html', {'new_conversation_id': new_conversation_id})    
def mark_notification_as_read(request):
    notification_id = request.GET.get('notification_id')
    notification = Notification.objects.filter(id=notification_id, user=request.user).first()
    if notification:
        notification.is_read = True
        notification.save()
        return JsonResponse({'success': True, 'redirect_url': get_redirect_url(notification)})
    else:
        return JsonResponse({'success': False})

@login_required
def notification(request):
    # Get unread notifications for the current user
    notifications = Notification.objects.filter(user=request.user).order_by('-timestamp')

        # Mark all notifications as read
    unread_notifications = Notification.objects.filter(user=request.user, is_read=False)

    # Separate notifications by type
    message_notifications = []
    post_notifications = []
    group_message_notifications = []
    group_post_notifications = []
    emoji_reaction_notifications = []
    comment_notifications = []
    emoji_reaction_group_notifications = []
    comment_group_notifications = []
    join_request_notifications = []
    for notification in unread_notifications:
        if notification.message:
            message_notifications.append(notification)
        elif notification.post:
            post_notifications.append(notification)
        elif notification.group_post:
            group_post_notifications.append(notification)     
        elif notification.group_message:
            group_message_notifications.append(notification)
        elif notification.emoji_reaction:
            emoji_reaction_notifications.append(notification)
        elif notification.comment:
            comment_notifications.append(notification)
        elif notification.emoji_reaction_group:
            emoji_reaction_group_notifications.append(notification)
        elif notification.comment_group:
            comment_group_notifications.append(notification)
        elif notification.join_request:
            join_request_notifications.append(notification)

        notification.is_read = True
        notification.save()

    # Get the total count of unread notifications
    unread_count = len(unread_notifications)

    new_conversation_id = str(uuid.uuid4())
    return render(request, 'notifications.html', {
        'message_notifications': message_notifications,
        'post_notifications': post_notifications,
        'group_post_notifications': group_post_notifications,
        'group_message_notifications': group_message_notifications,
        'emoji_reaction_notifications': emoji_reaction_notifications,
        'comment_notifications': comment_notifications,
        'emoji_reaction_group_notifications': emoji_reaction_group_notifications,
        'comment_group_notifications': comment_group_notifications,
        'join_request_notifications': join_request_notifications,
        'unread_notifications': unread_notifications,
         'new_conversation_id': new_conversation_id, 
         'LANGUAGES': settings.LANGUAGES,
    })
@login_required
def saved_conversations(request):
    # Get notifications for current user
    notifications = Notification.objects.filter(user=request.user).order_by('-timestamp')[:10]
    unread_notifications = Notification.objects.filter(user=request.user, is_read=False)
    search_form = SearchForm()
    users = []
    if request.GET.get('search'):
        search_form = SearchForm(request.GET)
        if search_form.is_valid():
            query = search_form.cleaned_data['query']
            users = User.objects.filter(username__icontains=query)
            conversations = []
            for user in users:
                conversation = Message.objects.filter(Q(sender=request.user, recipient=user) | Q(sender=user, recipient=request.user)).order_by('timestamp').last()
                if conversation:
                    conversations.append(conversation)
            return render(request, 'chat/saved_conversations.html', {
                'users': users,
                'conversations': conversations,
                'search_form': search_form,
                'notifications': notifications,
                'unread_notifications': unread_notifications,
            })
    
    conversations = Message.objects.filter(Q(sender=request.user) | Q(recipient=request.user)).order_by('recipient', '-timestamp').distinct('recipient')
    search_form = SearchForm()
    notifications = Notification.objects.filter(user=request.user).order_by('-timestamp')

        # Mark all notifications as read
    unread_notifications = Notification.objects.filter(user=request.user, is_read=False)

    # Separate notifications by type
    message_notifications = []
    post_notifications = []
    group_message_notifications = []
    group_post_notifications = []
    emoji_reaction_notifications = []
    comment_notifications = []
    emoji_reaction_group_notifications = []
    comment_group_notifications = []
    join_request_notifications = []
    for notification in unread_notifications:
        if notification.message:
            message_notifications.append(notification)
        elif notification.post:
            post_notifications.append(notification)
        elif notification.group_post:
            group_post_notifications.append(notification)     
        elif notification.group_message:
            group_message_notifications.append(notification)
        elif notification.emoji_reaction:
            emoji_reaction_notifications.append(notification)
        elif notification.comment:
            comment_notifications.append(notification)
        elif notification.emoji_reaction_group:
            emoji_reaction_group_notifications.append(notification)
        elif notification.comment_group:
            comment_group_notifications.append(notification)
        elif notification.join_request:
            join_request_notifications.append(notification)

        notification.is_read = True
        notification.save()
    new_conversation_id = str(uuid.uuid4())
    return render(request, 'chat/saved_conversations.html', {
        'users': User.objects.none(),
        'conversations': conversations,
        'search_form': search_form,
        'notifications': notifications,
        'unread_notifications': unread_notifications,
        'new_conversation_id': new_conversation_id,
        'LANGUAGES': settings.LANGUAGES,
    })
@login_required(login_url='get_started')   
def show_group_post(request, group_name, post_id):
    posts = GroupPost.objects.all()
    # Retrieve all comments for the post with the given post_id
    post = get_object_or_404(GroupPost, id=post_id)
    comments = post.comments_group.all()

    # Retrieve all emoji reactions for the post with the given post_id
    emoji_reactions = post.emoji_reactions_group.all()

    reactions = post.emoji_reactions_group.all()

    # Retrieve group object
    group = Group.objects.filter(members=request.user).first() or Group.objects.filter(admin=request.user).first()

    # Retrieve all GroupPost objects and order by created_at descending
    group_post = GroupPost.objects.all().order_by('-created_at')
    group_message = GroupMessage.objects.all().order_by('-timestamp')

    # Create search form
    search_form = SearchForm()

    form_reaction = EmojiReactionFormGroup(initial={'post': post_id})
    form_comment = CommentFormGroup(initial={'post': post_id})

    if request.method == 'POST':
        if 'emoji' in request.POST:
            form_reaction = EmojiReactionFormGroup(request.POST)
            if form_reaction.is_valid():
                emoji = form_reaction.save(commit=False)
                emoji.author = request.user
                emoji.group = group
                emoji.post = post
                emoji.created_at = timezone.now()
                emoji.save()
                return redirect('show_group_post', group_name=group_name, post_id=post_id)
        elif 'comment' in request.POST:
            form_comment = CommentFormGroup(request.POST)
            if form_comment.is_valid():
                comment = form_comment.save(commit=False)
                comment.author = request.user
                comment.group = group
                comment.post = post
                comment.save()
                messages.success(request, 'Comment added successfully!')
                return redirect('show_group_post', group_name=group_name, post_id=post_id)

    # Retrieve all reactions for each post and count them
    reactions = {}
    for p in posts:
        for reaction in p.emoji_reactions_group.all():
            if p.id not in reactions:
                reactions[p.id] = {}
            if reaction.emoji not in reactions[p.id]:
                reactions[p.id][reaction.emoji] = 1
            else:
                reactions[p.id][reaction.emoji] += 1
    
    unread_notifications = Notification.objects.filter(user=request.user, is_read=False)
    reactions = post.emoji_reactions_group.all()
    reaction_counts = {
            'heart': reactions.filter(emoji='❤️').count(),
            'thumbs_up': reactions.filter(emoji='👍').count(),
            'thumbs_down': reactions.filter(emoji='👎').count(),
            'angry': reactions.filter(emoji='😠').count(),
            'cool': reactions.filter(emoji='😎').count(),
            'smile': reactions.filter(emoji='😊').count(),
        }
                
    unread_notifications = Notification.objects.filter(user=request.user, is_read=False)

    # Mark all notifications as read
    notifications = Notification.objects.filter(user=request.user).order_by('-timestamp')[:10]

     # Get unread notifications for the current user
    # notifications = Notification.objects.filter(user=request.user).order_by('-timestamp')

        # Mark all notifications as read
    unread_notifications = Notification.objects.filter(user=request.user, is_read=False)

    # Separate notifications by type
    message_notifications = []
    post_notifications = []
    group_message_notifications = []
    group_post_notifications = []
    emoji_reaction_notifications = []
    comment_notifications = []
    emoji_reaction_group_notifications = []
    comment_group_notifications = []
    join_request_notifications = []
    for notification in unread_notifications:
        if notification.message:
            message_notifications.append(notification)
        elif notification.post:
            post_notifications.append(notification)
        elif notification.group_post:
            group_post_notifications.append(notification)     
        elif notification.group_message:
            group_message_notifications.append(notification)
        elif notification.emoji_reaction:
            emoji_reaction_notifications.append(notification)
        elif notification.comment:
            comment_notifications.append(notification)
        elif notification.emoji_reaction_group:
            emoji_reaction_group_notifications.append(notification)
        elif notification.comment_group:
            comment_group_notifications.append(notification)
        elif notification.join_request:
            join_request_notifications.append(notification)

        notification.is_read = True
        notification.save()     
    new_conversation_id = str(uuid.uuid4())                    
    return render(request, 'post/group_post.html', {'group': group, 'post': post, 'group_post': group_post, 'search_form': search_form,  'form_comment': form_comment, 'form_reaction': form_reaction, 'reactions': reactions, 'notifications': 'notifications', 'unread_notifications': unread_notifications, 'reactions': reactions, 'emoji_reactions': emoji_reactions, 'comments': comments, 'reaction_counts': reaction_counts, 'new_conversation_id': new_conversation_id, 'LANGUAGES': settings.LANGUAGES}) 

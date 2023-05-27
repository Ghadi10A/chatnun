from django.urls import include, path, re_path
from django.views.generic.base import RedirectView
from . import views
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    path('get-signal', views.predict_signals, name='predict_signals'),
    path('accounts/profile/<str:username>', include('django.contrib.auth.urls')),
    path('signup/', views.user_signup, name='user_signup'),
    path('login/', views.user_login, name='user_login'),
    path('choose-plan/', views.choose_plan, name='choose_plan'),
    path('subscribe/<str:plan>/', views.subscribe, name='subscribe'),
    path('renew-subscription/', views.renew_subscription, name='renew_subscription'),
    path('verification-email/', views.verification_email_sent, name='verification_email_sent'),
    path('verification-email-resend/', views.verification_email_resend, name='verification_email_resend'),
    path('accounts/profile/<str:username>/', views.show_profile, name='show_profile'),
    path('delete-account/', views.delete_account, name='delete_account'),
    path('follow/<str:username>/', views.follow_user, name='follow'),
    path('unfollow/<str:username>/', views.unfollow_user, name='unfollow'),
    path('logout/', views.user_logout, name='logout'),
    path('scanner/<str:interval>', views.choose_interval, name='choose_interval'),
    path('scanner/<str:interval>/', views.run_scanner, name='run_scanner'),
    path('posts/<int:post_id>/', views.show_post, name='show_post'),
    path('posts/<str:group_name>/<int:post_id>/', views.show_group_post, name='show_group_post'),
    path('get-started/', views.get_started, name='get_started'),
    path('', views.home, name='home'),
    path('chatbotTrade/<str:conversation_id>/', views.chatbotTrade, name='chatbotTrade'),
    path('chatbotTrade/', views.chatbotTrade, {'conversation_id': ''}, name='chatbotTrade'),
    path('chatbot/<str:conversation_id>/', views.chatbot, name='chatbot'),
    path('chatbot/', views.chatbot, {'conversation_id': ''}, name='chatbot'),
    path('chatbotTrade/<str:conversation_id>/delete/<str:timestamp>/', views.delete_chat, name='delete_chat'),
    path('search/', views.search, name='search'),
    path('search-users/', views.search_users, name='search_users'),
    path('comment/<int:post_id>/<int:comment_id>/edit/', views.edit_comment, name='edit_comment'),
    path('comment/<int:post_id>/<int:comment_id>/delete/', views.delete_comment, name='delete_comment'),
    path('comments/<int:post_id>/<int:comment_id>/edit/', views.edit_comment_group, name='edit_comment_group'),
    path('comments/<int:post_id>/<int:comment_id>/delete/', views.delete_comment_group, name='delete_comment_group'),
    path('post/<int:post_id>/update/', views.update_post, name='update_post'),
    path('post/<int:post_id>/delete/', views.delete_post, name='delete_post'),
    path('posts/<int:post_id>/update/', views.update_post_group, name='update_post_group'),
    path('posts/<int:post_id>/delete/', views.delete_post_group, name='delete_post_group'),
    path('messages/<str:username>/', views.message_thread, name='message_thread'),
    path('messages-and-conversations/', views.saved_conversations, name='saved_conversations'),
    path('create-group/', views.create_group, name='create_group'),
    path('chat/group/<str:name>/<int:pk>/', views.chat_group_detail, name='chat_group_detail'),
    path('join/<int:pk>/', views.join_group, name='join_group'),
    path('group/<int:pk>/join-requests/', views.join_requests, name='join_requests'),
    path('group/<int:group_pk>/join-requests/<int:join_request_pk>/approve/', views.approve_join_request, name='approve_join_request'),
    path('leave/<int:pk>/', views.leave_group, name='leave_group'),
    path('group/<str:name>/<int:pk>/', views.group_detail, name='group_detail'),
    path('<str:name>/<int:pk>/delete/', views.delete_group, name='delete_group'),
    path('terms-of-service/', views.terms_of_service, name='terms_of_service'),
    path('about-us/', views.about_us, name='about_us'),
    path('contact-us/', views.contact_us, name='contact_us'),
    path('privacy-policy/', views.privacy_policy, name='privacy_policy'),
    path('notifications/', views.notification, name='notification'),
    path('mark-notification-as-read/', views.mark_notification_as_read, name='mark_notification_as_read'),
    path('<str:language_code>/', views.switch_language, name='switch_language'),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)

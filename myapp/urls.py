from django.urls import include, path
from . import views

urlpatterns = [
    path('/predict_signals', views.predict_signals, name='predict_signals'),
    path('accounts/profile/<str:username>', include('django.contrib.auth.urls')),
    path('signup/', views.user_signup, name='signup'),
    path('login/', views.user_login, name='login'),
    path('profile/<str:username>', views.show_profile, name='show_profile'),
    path('logout/', views.user_logout, name='logout'),
    path('scanner/', views.run_scanner, name='run_scanner'),
]


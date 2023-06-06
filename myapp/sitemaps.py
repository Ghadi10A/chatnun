from django.contrib.sitemaps import Sitemap
from django.urls import reverse

class MyModel:
    def __init__(self, url_name):
        self.url_name = url_name

class MySitemap(Sitemap):
    def items(self):
        # Return a list of dummy objects to include in the sitemap
        return [
            MyModel('myapp:home'),
            MyModel('myapp:about_us'),
            MyModel('myapp:contact_us'),
            MyModel('myapp:terms_of_service'),
            MyModel('myapp:privacy_policy'),
            MyModel('myapp:choose_plan'),
            MyModel('myapp:run_scanner'),
            MyModel('myapp:predict_signals'),
            MyModel('myapp:user_signup'),
            MyModel('myapp:user_login'),
            MyModel('myapp:show_profile'),
            MyModel('myapp:show_post'),
            MyModel('myapp:get_started'),
            MyModel('myapp:chatbotTrade'),
            MyModel('myapp:chatbot'),
            MyModel('myapp:chat_group_detail'),
            MyModel('myapp:group_detail'),
            # Add more dummy objects as needed
        ]

    def location(self, item):
        # Return the URL for each object
        return reverse(item.url_name)

sitemaps = {
    'MyModel': MySitemap,
}

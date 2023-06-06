from django.contrib.sitemaps import Sitemap
from django.urls import reverse

class chatnun:
    def __init__(self, url_name):
        self.url_name = url_name
        
class MySitemap(Sitemap):
    def items(self):
        # Return a list of dummy objects to include in the sitemap
        return [
            ('myapp:index', 'home'),
            ('myapp:about', 'about-us'),
            # Add more dummy objects as needed
        ]

    def location(self, item):
        # Return the URL for each object
        return reverse(item[0], args=[item[1]])
sitemaps = {
    'chatnun': MySitemap,
}

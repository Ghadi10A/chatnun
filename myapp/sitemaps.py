from django.contrib.sitemaps import Sitemap
from django.urls import reverse

class MySitemap(Sitemap):
    def items(self):
        # Return a queryset of objects to include in the sitemap
        return MyModel.objects.all()

    def location(self, item):
        # Return the URL for each object
        return reverse('myapp:detail', args=[item.pk])
sitemaps = {
    'chatnun': MySitemap,
}

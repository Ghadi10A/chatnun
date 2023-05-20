from django import template

register = template.Library()

@register.filter
def get_comments(comments, post_id):
    return comments.get(post_id, [])
@register.filter
def emoji_unicode_to_char(value):
    try:
        emoji_char = chr(int(value, 16))
        return emoji_char
    except ValueError:
        return value
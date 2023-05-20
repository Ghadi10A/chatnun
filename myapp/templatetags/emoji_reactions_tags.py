from django import template

register = template.Library()

@register.filter
def has_reacted(post, user):
    return post.emoji_reactions.filter(author=user).exists()

@register.filter
def has_reacted_group(post, user):
    return post.emoji_reactions_group.filter(author=user).exists()    

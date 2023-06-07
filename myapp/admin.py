from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import User, Profile, Post, EmojiReaction, ChatHistory, Follow, Notification, Message, Group, GroupPost, Invitation, GroupMessage, Notification, Comment, EmojiReaction, ChatHistory

admin.site.register(User)
admin.site.register(Profile)
admin.site.register(Post)
admin.site.register(Follow)
admin.site.register(Message)
admin.site.register(Group)
admin.site.register(GroupPost)
admin.site.register(GroupMessage)
admin.site.register(Comment)
admin.site.register(EmojiReaction)
admin.site.register(ChatHistory)
admin.site.register(Invitation)
admin.site.register(Notification)

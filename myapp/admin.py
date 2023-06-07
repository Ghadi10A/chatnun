from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import User, Profile, Post, EmojiReaction, ChatHistory, Follow, Notification, Message, Group, GroupPost, Invitation, GroupMessage, Notification, Comment, EmojiReaction, ChatHistory

class UserAdminCustom(UserAdmin):
    fieldsets = (
        (None, {'fields': ('username', 'password')}),
        ('Personal info', {'fields': ('first_name', 'last_name', 'email')}),
        ('Permissions', {'fields': ('is_active', 'is_staff', 'is_superuser',
                                    'groups', 'user_permissions')}),
        ('Important dates', {'fields': ('last_login', 'date_joined')}),
        ('Subscription', {'fields': ('profile.subscription_plan', 'profile.subscription_end',
                                     'profile.subscription_status')}),
    )

admin.site.unregister(User)
admin.site.register(User, UserAdminCustom)
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

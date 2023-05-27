from django.db import models
from django.contrib.auth.models import AbstractUser, Group, Permission
from django.utils import timezone
from six import python_2_unicode_compatible
import datetime
import emojis
import uuid
# from modeltranslation.fields import TranslationField

class Prediction(models.Model):
    app_label = 'myapp'

    INSTRUMENTS = [
        ('nasdaq100', 'NASDAQ 100'),
        ('tesla', 'Tesla'),
        ('google', 'Google'),
        ('apple', 'Apple'),
        ('amazon', 'Amazon'),
        ('btc', 'Bitcoin'),
        ('gold', 'Gold'),
        ('oil', 'Oil'),
    ]

    instrument = models.CharField(max_length=50, choices=INSTRUMENTS)
    close_price = models.FloatField()
    vwap = models.FloatField()
    signal = models.CharField(max_length=50)
    accuracy = models.FloatField()
    created_at = models.DateTimeField(auto_now_add=True)

class User(AbstractUser):
    username = models.CharField(max_length=150, unique=True)
    email = models.EmailField(unique=True)
    first_name = models.CharField(max_length=30)
    last_name = models.CharField(max_length=30)
    groups = models.ManyToManyField(Group, related_name='custom_groups')
    user_permissions = models.ManyToManyField(Permission, related_name='custom_permissions')  
    is_active = models.BooleanField(default=False)
    is_connected = models.BooleanField(default=False)

from django.contrib.auth.models import User
class Profile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    image = models.ImageField(upload_to='media/profile_pics', blank=True, null=True)
    bio = models.TextField(max_length=500, blank=True)
    birthdate = models.DateField(null=True, blank=True)
    city = models.CharField(max_length=255, null=True, blank=True)
    location = models.CharField(max_length=30, blank=True)
    stripe_customer_id = models.CharField(max_length=50, blank=True, null=True)
    subscription_plan = models.CharField(max_length=10, blank=True, null=True)
    subscription_end = models.DateTimeField(blank=True, null=True)
    subscription_status = models.CharField(max_length=10, blank=True, null=True, default='inactive')

    def __str__(self):
        return self.user
                   
class Follow(models.Model):
    follower = models.ForeignKey(User, on_delete=models.CASCADE, related_name='following', null=True, blank=True)
    following = models.ForeignKey(User, on_delete=models.CASCADE, related_name='followers', null=True, blank=True)

class Post(models.Model):
    author = models.ForeignKey(User, on_delete=models.CASCADE)
    content = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    image = models.ImageField(upload_to='posts/', null=True, blank=True)
    video = models.FileField(upload_to='videos/', null=True, blank=True)
    sound = models.FileField(upload_to='sounds/', null=True, blank=True)
    

    def __str__(self):
        return f'{self.content} by {self.author.username} ({self.pk})'


class Comment(models.Model):
    post = models.ForeignKey(Post, on_delete=models.CASCADE, related_name='comments')
    author = models.ForeignKey(User, on_delete=models.CASCADE)
    comment = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f'{self.comment} {self.pk}'

    def get_absolute_url(self):
        return reverse('show_post', kwargs={
            'post_id': self.id,
            'author_profile_image': self.author.profile.image.url,
            'comments': self.comments.all(),
        })    

    def save(self, *args, **kwargs):
        """Override save method to update created_at field"""
        if not self.id:
            self.created_at = timezone.now()
        super(Comment, self).save(*args, **kwargs)

    def edit(self, new_content):
        """Update the comment field of the comment object"""
        self.comment = new_comment
        self.save()

    def delete(self):
        """Delete the comment object"""
        super(Comment, self).delete()

class EmojiReaction(models.Model):
    EMOJI_CHOICES = [(emojis.encode(x[0]), x[1]) for x in [
        ('heart', '❤️'),
        ('thumbs_up', '👍'),
        ('thumbs_down', '👎'),
        ('angry', '😠'),
        ('smiling_face', '😊'),
    ]]
    post = models.ForeignKey(Post, on_delete=models.CASCADE, related_name='emoji_reactions')
    author = models.ForeignKey(User, on_delete=models.CASCADE, related_name='post_reactions')
    emoji = models.CharField(choices=EMOJI_CHOICES, max_length=20)
    created_at = models.DateTimeField(default=datetime.datetime.now)

    def __str__(self):
        return f'{self.emoji} {self.pk}'

    def get_emoji_display(self):
        return emojis.decode(self.emoji)

    def get_absolute_url(self):
        return reverse('show_post', kwargs={
            'post_id': self.post.id,
            'author_profile_image': self.author.profile.image.url,
            'emoji_reactions': self.post.emoji_reactions.all(),
        })

    def save(self, *args, **kwargs):
        if not self.pk and self.post:
            self.post_id = self.post.pk
        super(EmojiReaction, self).save(*args, **kwargs)



class ChatHistory(models.Model):
    conversation_id = models.CharField(max_length=100, default=str(uuid.uuid4()), unique=True)
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    prompt = models.TextField()
    response = models.TextField()
    timestamp = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.prompt}'s chat history ({self.timestamp.strftime('%Y-%m-%d %H:%M:%S')})"
  
class Message(models.Model):
    sender = models.ForeignKey(User, on_delete=models.CASCADE, related_name='sender_messages')
    recipient = models.ForeignKey(User, related_name='received_messages', on_delete=models.CASCADE)
    content = models.TextField()
    timestamp = models.DateTimeField(auto_now_add=True)
    is_read = models.BooleanField(default=False)

    def __str__(self):
        return f"{self.sender} to {self.recipient}"

    class Meta:
        ordering = ['-timestamp'] 

class Group(models.Model):
    name = models.CharField(max_length=100)
    description = models.TextField()
    members = models.ManyToManyField(User, related_name='joined_groups')
    admin = models.ForeignKey(User, on_delete=models.CASCADE, related_name='admin_groups')
    image = models.ImageField(upload_to='group_images/', blank=True, null=True)

    def __str__(self):
        return self.name

    def add_member(self, user):
        self.members.add(user)

    def remove_member(self, user):
        self.members.remove(user)

    def is_member(self, user):
        return user in self.members.all()

    def get_absolute_url(self):
        return reverse('group_detail', args=[str(self.id)])

class GroupRequest(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    group = models.ForeignKey(Group, on_delete=models.CASCADE)
    date_requested = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.user.username} requested to join {self.group.name}"  

class JoinRequest(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    group = models.ForeignKey(Group, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)

    def get_absolute_url(self):
        return reverse('group_detail', args=[str(self.group.id)])
        
class GroupPost(models.Model):
    group = models.ForeignKey(Group, on_delete=models.CASCADE, null=True, blank=True)
    author = models.ForeignKey(User, on_delete=models.CASCADE, null=True, blank=True)
    content = models.TextField()
    created_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(auto_now=True)
    image = models.ImageField(upload_to='posts/', null=True, blank=True)
    video = models.FileField(upload_to='videos/', null=True, blank=True)
    sound = models.FileField(upload_to='sounds/', null=True, blank=True)

    def __str__(self):
        return f'{self.content} by {self.author.username} ({self.pk})'


class CommentGroup(models.Model):
    group = models.ForeignKey(Group, on_delete=models.CASCADE, related_name='group_comments')
    author = models.ForeignKey(User, on_delete=models.CASCADE)
    post = models.ForeignKey(GroupPost, on_delete=models.CASCADE, related_name='comments_group')
    comment = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f'{self.comment} by {self.author.username} ({self.pk})'

    def save(self, *args, **kwargs):
        """Override save method to update created_at field"""
        if not self.id:
            self.created_at = timezone.now()
        super(CommentGroup, self).save(*args, **kwargs)

    def edit(self, new_comment):
        """Update the comment field of the comment object"""
        self.comment = new_comment
        self.save()

    def delete(self):
        """Delete the comment object"""
        super(CommentGroup, self).delete()

class EmojiReactionGroup(models.Model):
    EMOJI_CHOICES = [(emojis.encode(x[0]), x[1]) for x in [
            ('heart', '❤️'),
            ('thumbs_up', '👍'),
            ('thumbs_down', '👎'),
            ('angry', '😠'),
            ('smiling_face', '😊'),
        ]]
    group = models.ForeignKey(Group, on_delete=models.CASCADE, related_name='group_reactions')
    post = models.ForeignKey(GroupPost, on_delete=models.CASCADE, related_name='emoji_reactions_group')
    author = models.ForeignKey(User, on_delete=models.CASCADE, related_name='author_reactions_group')
    emoji = models.CharField(choices=EMOJI_CHOICES, max_length=20)
    created_at = models.DateTimeField(default=datetime.datetime.now)

    def __str__(self):
        return f'{self.emoji} {self.pk}'

    def get_emoji_display(self):
        return emojis.decode(self.emoji)

    def get_absolute_url(self):
        return reverse('show_post', kwargs={
            'post_id': self.post.id,
            'author_profile_image': self.author.profile.image.url,
            'emoji_reactions_group': self.post.emoji_reactions_group.all(),
        })

    def save(self, *args, **kwargs):
        if not self.pk and self.post:
            self.post_id = self.post.pk
        super(EmojiReactionGroup, self).save(*args, **kwargs)
class GroupMessage(models.Model):
    sender = models.ForeignKey(User, on_delete=models.CASCADE, related_name='sent_messages')
    group = models.ForeignKey(Group, on_delete=models.CASCADE, related_name='messages')
    message = models.TextField()
    timestamp = models.DateTimeField(auto_now_add=True)
    is_read = models.BooleanField(default=False)

    def __str__(self):
        return f'{self.sender.username} ({self.group.name}): {self.message}'

    class Meta:
        ordering = ['-timestamp']  

class Invitation(models.Model):
    sender = models.ForeignKey(User, on_delete=models.CASCADE, related_name='sent_invitations')
    recipient = models.ForeignKey(User, on_delete=models.CASCADE, related_name='received_invitations')
    group = models.ForeignKey(Group, on_delete=models.CASCADE)
    is_accepted = models.BooleanField(default=False)

class Notification(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='notifications_received')
    post = models.ForeignKey(Post, on_delete=models.CASCADE, null=True, blank=True)
    message = models.ForeignKey(Message, on_delete=models.CASCADE, null=True, blank=True)
    group_message = models.ForeignKey(GroupMessage, on_delete=models.CASCADE, null=True, blank=True)
    invitation = models.ForeignKey(Invitation, on_delete=models.CASCADE, null=True, blank=True)
    emoji_reaction = models.ForeignKey(EmojiReaction, on_delete=models.CASCADE, null=True, blank=True)
    comment = models.ForeignKey(Comment, on_delete=models.CASCADE, null=True, blank=True)
    emoji_reaction_group = models.ForeignKey(EmojiReactionGroup, on_delete=models.CASCADE, null=True, blank=True)
    comment_group = models.ForeignKey(CommentGroup, on_delete=models.CASCADE, null=True, blank=True)
    join_request = models.ForeignKey(JoinRequest, on_delete=models.CASCADE, null=True, blank=True)
    timestamp = models.DateTimeField(auto_now_add=True)
    is_read = models.BooleanField(default=False)

    def __str__(self):
        return f"{self.user}: {self.get_notification_type()}"

    def get_notification_type(self):
        if self.post:
            return f"New post from {self.post.author.username}"
        elif self.message:
            return f"New message from {self.message.sender.username}"
        elif self.group_message:
            return f"New message in {self.group_message.group.name} from {self.group_message.sender.username}"
        elif self.invitation:
            return f"You have been invited to join {self.invitation.group.name}"
        elif self.emoji_reaction:
            return f"{self.emoji_reaction.author.username} reacted to your post with {self.emoji_reaction.get_emoji_display()}"
        elif self.comment:
            return f"{self.comment.author.username} commented on your post"    
        elif self.emoji_reaction_group:
            return f"{self.emoji_reaction_group.author.username} reacted to your post group with {self.emoji_reaction_group.get_emoji_display()}"
        elif self.comment_group:
            return f"{self.comment_group.author.username} commented on your post group"
        elif self.join_request:
            return f"{self.join_request.user.username} has requested to join {self.join_request.group.name}"
        else:
            return "Unknown notification type"
    
    class Meta:
        ordering = ['-timestamp'] 

     


from django.conf import settings
from django.core.validators import MinLengthValidator
from django.db import models
from django.db.models import F, Q

class Profile(models.Model):
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='profile')
    full_name = models.CharField(max_length=100, blank=True)
    bio = models.CharField(max_length=160, blank=True)
    phone_number = models.CharField(max_length=20, blank=True, default='')
    profile_picture = models.ImageField(upload_to='profiles/', blank=True)
    is_private = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    class Meta:
        constraints = [models.UniqueConstraint(fields=('phone_number',), condition=~Q(phone_number=''), name='unique_profile_phone')]
    def __str__(self):
        return f'@{self.user.username}'

class Follow(models.Model):
    follower = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='following_links')
    following = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='follower_links')
    created_at = models.DateTimeField(auto_now_add=True)
    class Meta:
        constraints = [
            models.UniqueConstraint(fields=('follower', 'following'), name='unique_follow'),
            models.CheckConstraint(condition=~Q(follower=F('following')), name='prevent_self_follow'),
        ]
        indexes = [models.Index(fields=('following', 'created_at')), models.Index(fields=('follower', 'created_at'))]

class FollowRequest(models.Model):
    requester = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='sent_follow_requests')
    target = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='received_follow_requests')
    created_at = models.DateTimeField(auto_now_add=True)
    class Meta:
        constraints = [
            models.UniqueConstraint(fields=('requester', 'target'), name='unique_follow_request'),
            models.CheckConstraint(condition=~Q(requester=F('target')), name='prevent_self_follow_request'),
        ]
        ordering = ('created_at',)

class Post(models.Model):
    VISIBILITY = [('public', 'Public'), ('followers', 'Followers only')]
    MEDIA = [('text', 'Text'), ('image', 'Photo'), ('video', 'Video')]
    author = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='posts')
    media = models.FileField(upload_to='posts/%Y/%m/', blank=True)
    media_type = models.CharField(max_length=8, choices=MEDIA, default='text')
    caption = models.TextField(max_length=2000, blank=True)
    visibility = models.CharField(max_length=12, choices=VISIBILITY, default='public', db_index=True)
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)
    updated_at = models.DateTimeField(auto_now=True)
    class Meta:
        ordering = ('-created_at',)
    def __str__(self):
        return f'{self.author.username}: {self.caption[:45]}'

class Like(models.Model):
    post = models.ForeignKey(Post, on_delete=models.CASCADE, related_name='likes')
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='likes')
    created_at = models.DateTimeField(auto_now_add=True)
    class Meta:
        constraints = [models.UniqueConstraint(fields=('post', 'user'), name='unique_post_like')]
        indexes = [models.Index(fields=('post', 'created_at'))]

class Comment(models.Model):
    post = models.ForeignKey(Post, on_delete=models.CASCADE, related_name='comments')
    author = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='comments')
    content = models.CharField(max_length=500, validators=[MinLengthValidator(1)])
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    class Meta:
        ordering = ('created_at',)

class Notification(models.Model):
    TYPES = [
        ('like', 'liked your post'),
        ('comment', 'commented on your post'),
        ('follow', 'started following you'),
        ('follow_request', 'requested to follow you'),
    ]
    recipient = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='notifications')
    actor = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='sent_notifications')
    notification_type = models.CharField(max_length=20, choices=TYPES)
    related_post = models.ForeignKey(Post, on_delete=models.CASCADE, blank=True, null=True, related_name='notifications')
    is_read = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)
    class Meta:
        ordering = ('-created_at',)

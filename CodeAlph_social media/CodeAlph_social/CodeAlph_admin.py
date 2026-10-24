from django.contrib import admin
from .models import Profile, Post, Comment, Like, Follow, FollowRequest, Notification

@admin.register(Profile)
class ProfileAdmin(admin.ModelAdmin):
    list_display = ('user', 'full_name', 'is_private', 'created_at')
    search_fields = ('user__username', 'full_name')
    list_filter = ('is_private',)

@admin.register(Post)
class PostAdmin(admin.ModelAdmin):
    list_display = ('author', 'media_type', 'visibility', 'created_at')
    search_fields = ('author__username', 'caption')
    list_filter = ('visibility', 'media_type', 'created_at')

@admin.register(Comment)
class CommentAdmin(admin.ModelAdmin):
    list_display = ('author', 'post', 'created_at')
    search_fields = ('author__username', 'content')

@admin.register(Like)
class LikeAdmin(admin.ModelAdmin):
    list_display = ('user', 'post', 'created_at')
    search_fields = ('user__username', 'post__caption')

@admin.register(Follow)
class FollowAdmin(admin.ModelAdmin):
    list_display = ('follower', 'following', 'created_at')
    search_fields = ('follower__username', 'following__username')

@admin.register(FollowRequest)
class FollowRequestAdmin(admin.ModelAdmin):
    list_display = ('requester', 'target', 'created_at')
    search_fields = ('requester__username', 'target__username')

@admin.register(Notification)
class NotificationAdmin(admin.ModelAdmin):
    list_display = ('recipient', 'actor', 'notification_type', 'is_read', 'created_at')
    list_filter = ('notification_type', 'is_read')
    search_fields = ('recipient__username', 'actor__username')

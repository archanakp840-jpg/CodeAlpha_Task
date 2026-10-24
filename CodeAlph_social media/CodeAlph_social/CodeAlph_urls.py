from django.urls import path
from . import views

app_name = 'social'
urlpatterns = [
    path('', views.home, name='home'),
    path('register/', views.register, name='register'),
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    path('profile/edit/', views.edit_profile, name='edit_profile'),
    path('u/<str:username>/', views.profile, name='profile'),
    path('u/<str:username>/follow/', views.follow_toggle, name='follow_toggle'),
    path('requests/', views.follow_requests, name='follow_requests'),
    path('requests/<int:request_id>/<str:action>/', views.resolve_follow_request, name='resolve_follow_request'),
    path('posts/new/', views.create_post, name='create_post'),
    path('posts/<int:post_id>/', views.post_detail, name='post_detail'),
    path('posts/<int:post_id>/media/', views.serve_post_media, name='serve_post_media'),
    path('profiles/<int:user_id>/picture/', views.serve_profile_picture, name='serve_profile_picture'),
    path('posts/<int:post_id>/edit/', views.edit_post, name='edit_post'),
    path('posts/<int:post_id>/delete/', views.delete_post, name='delete_post'),
    path('posts/<int:post_id>/like/', views.toggle_like, name='toggle_like'),
    path('posts/<int:post_id>/comment/', views.add_comment, name='add_comment'),
    path('comments/<int:comment_id>/delete/', views.delete_comment, name='delete_comment'),
    path('search/', views.search, name='search'),
    path('contacts/', views.contacts, name='contacts'),
    path('explore/', views.explore, name='explore'),
    path('notifications/', views.notifications, name='notifications'),
    path('people/<str:username>/<str:kind>/', views.people_list, name='people_list'),
]

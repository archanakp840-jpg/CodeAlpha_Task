from django.contrib import messages
from django.contrib.auth import get_user_model, login, logout
import mimetypes
import re
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.db import transaction
from django.db.models import Count, Exists, OuterRef, Q
from django.http import FileResponse, JsonResponse, Http404
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_POST
from .forms import SignupForm, LoginForm, ProfileForm, PostForm, CommentForm
from .models import Comment, Follow, FollowRequest, Like, Notification, Post

User = get_user_model()

def notify(recipient, actor, kind, post=None):
    if recipient.pk != actor.pk:
        Notification.objects.create(recipient=recipient, actor=actor, notification_type=kind, related_post=post)

def can_view_post(user, post):
    if not user.is_authenticated:
        return False
    if post.author_id == user.pk:
        return True
    following = Follow.objects.filter(follower=user, following=post.author).exists()
    if post.author.profile.is_private and not following:
        return False
    return post.visibility == 'public' or following

def with_feed_annotations(qs, user):
    return qs.select_related('author', 'author__profile').annotate(
        likes_total=Count('likes', distinct=True),
        comments_total=Count('comments', distinct=True),
        is_liked=Exists(Like.objects.filter(post_id=OuterRef('pk'), user=user)),
    )

def visible_posts_for(user, author=None):
    followed = Follow.objects.filter(follower=user).values('following_id')
    qs = with_feed_annotations(Post.objects.all(), user)
    if author is not None:
        qs = qs.filter(author=author)
        if author.pk == user.pk:
            return qs
        follows = Follow.objects.filter(follower=user, following=author).exists()
        if author.profile.is_private and not follows:
            return qs.none()
        if not follows:
            qs = qs.filter(visibility='public')
        return qs
    return qs.filter(Q(author=user) | Q(author_id__in=followed)).filter(
        Q(author=user) | Q(visibility='public') | Q(author_id__in=followed)
    )

def register(request):
    if request.user.is_authenticated:
        return redirect('social:home')
    form = SignupForm(request.POST or None)
    if request.method == 'POST' and form.is_valid():
        user = form.save()
        login(request, user)
        messages.success(request, 'Welcome to iworld. Your account is ready.')
        return redirect('social:home')
    return render(request, 'social/auth.html', {'form': form, 'mode': 'register'})

def login_view(request):
    if request.user.is_authenticated:
        return redirect('social:home')
    form = LoginForm(request, data=request.POST or None)
    if request.method == 'POST' and form.is_valid():
        login(request, form.get_user())
        return redirect(request.GET.get('next') or 'social:home')
    return render(request, 'social/auth.html', {'form': form, 'mode': 'login'})

@require_POST
def logout_view(request):
    logout(request)
    messages.info(request, 'You have signed out.')
    return redirect('social:login')

@login_required
def home(request):
    posts = visible_posts_for(request.user).order_by('-created_at')
    page = Paginator(posts, 10).get_page(request.GET.get('page'))
    following_ids = Follow.objects.filter(follower=request.user).values_list('following_id', flat=True)
    suggestions = User.objects.select_related('profile').exclude(pk=request.user.pk).exclude(pk__in=following_ids).annotate(
        followers_total=Count('follower_links')
    ).order_by('-followers_total', 'username')[:5]
    stories = User.objects.filter(pk__in=following_ids).select_related('profile')[:12]
    return render(request, 'social/home.html', {
        'posts': page, 'suggestions': suggestions, 'page_obj': page,
        'stories': stories, 'follow_request_count': request.user.received_follow_requests.count(), 'active': 'home',
    })

@login_required
def profile(request, username):
    person = get_object_or_404(User.objects.select_related('profile'), username__iexact=username)
    is_following = Follow.objects.filter(follower=request.user, following=person).exists()
    request_pending = FollowRequest.objects.filter(requester=request.user, target=person).exists()
    can_see = person.pk == request.user.pk or not person.profile.is_private or is_following
    posts = visible_posts_for(request.user, person).order_by('-created_at') if can_see else Post.objects.none()
    page = Paginator(posts.order_by('-created_at'), 12).get_page(request.GET.get('page'))
    return render(request, 'social/profile.html', {
        'person': person, 'posts': page, 'page_obj': page, 'active': 'profile', 'is_following': is_following,
        'request_pending': request_pending, 'can_see': can_see,
        'followers_count': person.follower_links.count(), 'following_count': person.following_links.count(),
    })

@login_required
def edit_profile(request):
    profile = request.user.profile
    form = ProfileForm(request.POST or None, request.FILES or None, instance=profile, user=request.user)
    if request.method == 'POST' and form.is_valid():
        was_private = profile.is_private
        form.save()
        if was_private and not request.user.profile.is_private:
            FollowRequest.objects.filter(target=request.user).delete()
        messages.success(request, 'Your profile was updated.')
        return redirect('social:profile', username=request.user.username)
    return render(request, 'social/edit_profile.html', {'form': form, 'active': 'profile'})

@login_required
@require_POST
def follow_toggle(request, username):
    person = get_object_or_404(User, username__iexact=username)
    if person.pk == request.user.pk:
        messages.error(request, 'You cannot follow yourself.')
        return redirect('social:profile', username=person.username)
    follow = Follow.objects.filter(follower=request.user, following=person).first()
    if follow:
        follow.delete()
        messages.info(request, f'You unfollowed @{person.username}.')
    elif person.profile.is_private:
        item, created = FollowRequest.objects.get_or_create(requester=request.user, target=person)
        if created:
            notify(person, request.user, 'follow_request')
            messages.success(request, 'Follow request sent.')
        else:
            item.delete()
            messages.info(request, 'Follow request canceled.')
    else:
        Follow.objects.get_or_create(follower=request.user, following=person)
        notify(person, request.user, 'follow')
        messages.success(request, f'You are following @{person.username}.')
    return redirect('social:profile', username=person.username)

@login_required
def follow_requests(request):
    requests = request.user.received_follow_requests.select_related('requester', 'requester__profile')
    return render(request, 'social/follow_requests.html', {'requests': requests, 'active': 'requests'})

@login_required
@require_POST
def resolve_follow_request(request, request_id, action):
    if action not in ('approve', 'decline'):
        messages.error(request, 'Unknown request action.')
        return redirect('social:follow_requests')
    item = get_object_or_404(request.user.received_follow_requests.select_related('requester'), pk=request_id)
    if action == 'approve':
        with transaction.atomic():
            Follow.objects.get_or_create(follower=item.requester, following=request.user)
            notify(item.requester, request.user, 'follow')
        messages.success(request, f'@{item.requester.username} is now following you.')
    else:
        messages.info(request, 'Follow request declined.')
    item.delete()
    return redirect('social:follow_requests')

@login_required
def create_post(request):
    form = PostForm(request.POST or None, request.FILES or None)
    if request.method == 'POST' and form.is_valid():
        post = form.save(commit=False)
        post.author = request.user
        post.save()
        messages.success(request, 'Your post is live.')
        return redirect('social:post_detail', post_id=post.pk)
    return render(request, 'social/post_form.html', {'form': form, 'title': 'Create a post'})

@login_required
def edit_post(request, post_id):
    post = get_object_or_404(Post, pk=post_id, author=request.user)
    form = PostForm(request.POST or None, request.FILES or None, instance=post)
    if request.method == 'POST' and form.is_valid():
        form.save()
        messages.success(request, 'Post updated.')
        return redirect('social:post_detail', post_id=post.pk)
    return render(request, 'social/post_form.html', {'form': form, 'title': 'Edit post', 'post': post})

@login_required
@require_POST
def delete_post(request, post_id):
    post = get_object_or_404(Post, pk=post_id, author=request.user)
    post.delete()
    messages.success(request, 'Post deleted.')
    return redirect('social:profile', username=request.user.username)

@login_required
def post_detail(request, post_id):
    post = get_object_or_404(with_feed_annotations(Post.objects.all(), request.user), pk=post_id)
    if not can_view_post(request.user, post):
        raise Http404
    comments = post.comments.select_related('author', 'author__profile')[:100]
    return render(request, 'social/post_detail.html', {'post': post, 'comments': comments, 'comment_form': CommentForm()})

@login_required
def serve_post_media(request, post_id):
    post = get_object_or_404(Post, pk=post_id)
    if not can_view_post(request.user, post):
        raise Http404
    if not post.media:
        raise Http404
    response = FileResponse(post.media.open('rb'), content_type=mimetypes.guess_type(post.media.name)[0] or 'application/octet-stream')
    response['X-Content-Type-Options'] = 'nosniff'
    return response

@login_required
def serve_profile_picture(request, user_id):
    from .models import Profile
    profile = get_object_or_404(Profile.objects.select_related('user'), user_id=user_id)
    if not profile.profile_picture:
        raise Http404
    response = FileResponse(profile.profile_picture.open('rb'), content_type=mimetypes.guess_type(profile.profile_picture.name)[0] or 'application/octet-stream')
    response['X-Content-Type-Options'] = 'nosniff'
    return response

@login_required
@require_POST
def toggle_like(request, post_id):
    post = get_object_or_404(Post.objects.select_related('author', 'author__profile'), pk=post_id)
    if not can_view_post(request.user, post):
        return JsonResponse({'error': 'This post is private.'}, status=403)
    like = Like.objects.filter(post=post, user=request.user).first()
    if like:
        like.delete()
        liked = False
    else:
        Like.objects.get_or_create(post=post, user=request.user)
        liked = True
        notify(post.author, request.user, 'like', post)
    return JsonResponse({'liked': liked, 'count': post.likes.count()})

@login_required
@require_POST
def add_comment(request, post_id):
    post = get_object_or_404(Post.objects.select_related('author', 'author__profile'), pk=post_id)
    if not can_view_post(request.user, post):
        raise Http404
    form = CommentForm(request.POST)
    if form.is_valid():
        comment = form.save(commit=False)
        comment.post = post
        comment.author = request.user
        comment.save()
        notify(post.author, request.user, 'comment', post)
    else:
        messages.error(request, form.errors.get('content', ['Could not add comment.'])[0])
    return redirect('social:post_detail', post_id=post.pk)

@login_required
@require_POST
def delete_comment(request, comment_id):
    comment = get_object_or_404(Comment.objects.select_related('post'), pk=comment_id, author=request.user)
    post_id = comment.post_id
    comment.delete()
    messages.success(request, 'Comment deleted.')
    return redirect('social:post_detail', post_id=post_id)

@login_required
def search(request):
    q = request.GET.get('q', '').strip()[:80]
    people = User.objects.select_related('profile').exclude(pk=request.user.pk)
    if q:
        people = people.filter(Q(username__icontains=q) | Q(profile__full_name__icontains=q))
    else:
        people = User.objects.none()
    return render(request, 'social/search.html', {'query': q, 'people': people[:50], 'active': 'search'})

@login_required
def explore(request):
    followed = Follow.objects.filter(follower=request.user).values('following_id')
    posts = with_feed_annotations(Post.objects.filter(
        visibility='public', author__profile__is_private=False
    ).exclude(author=request.user).exclude(author_id__in=followed), request.user)
    page = Paginator(posts.order_by('-created_at'), 12).get_page(request.GET.get('page'))
    return render(request, 'social/explore.html', {'posts': page, 'page_obj': page, 'active': 'explore'})

@login_required
def notifications(request):
    Notification.objects.filter(recipient=request.user, is_read=False).update(is_read=True)
    rows = request.user.notifications.select_related('actor', 'actor__profile', 'related_post')[:100]
    return render(request, 'social/notifications.html', {
        'notifications': rows, 'pending_requests': request.user.received_follow_requests.count(), 'active': 'notifications',
    })

@login_required
def people_list(request, username, kind):
    person = get_object_or_404(User.objects.select_related('profile'), username__iexact=username)
    follows = Follow.objects.filter(follower=request.user, following=person).exists()
    if person.profile.is_private and person.pk != request.user.pk and not follows:
        raise Http404
    if kind == 'followers':
        people = User.objects.filter(following_links__following=person).select_related('profile').distinct()
    elif kind == 'following':
        people = User.objects.filter(follower_links__follower=person).select_related('profile').distinct()
    else:
        return redirect('social:profile', username=person.username)
    return render(request, 'social/people.html', {'person': person, 'people': people, 'kind': kind})


@login_required
def contacts(request):
    matches = []
    error = ''
    uploaded = request.FILES.get('contacts_file')
    if request.method == 'POST':
        if not uploaded:
            error = 'Choose a .vcf contacts file to find people.'
        elif uploaded.size > 2 * 1024 * 1024:
            error = 'Contacts files must be 2 MB or smaller.'
        elif not uploaded.name.lower().endswith('.vcf'):
            error = 'Please export your contacts as a .vcf file.'
        else:
            try:
                raw = uploaded.read().decode('utf-8', errors='ignore').replace('\r\n', '\n').replace('\r', '\n')
                lines = []
                for line in raw.split('\n'):
                    if line.startswith((' ', '\t')) and lines:
                        lines[-1] += line[1:]
                    else:
                        lines.append(line)
                emails, phones = set(), set()
                for line in lines:
                    key, separator, value = line.partition(':')
                    if not separator:
                        continue
                    field = key.split(';', 1)[0].upper()
                    value = value.strip()
                    if field == 'EMAIL':
                        value = value.removeprefix('mailto:').lower()
                        if '@' in value:
                            emails.add(value[:254])
                    elif field == 'TEL':
                        digits = re.sub(r'\D', '', value)
                        if len(digits) >= 8:
                            phones.add(digits[-15:])
                query = Q()
                if emails:
                    query |= Q(email__in=emails)
                if phones:
                    query |= Q(profile__phone_number__in=list(phones))
                    query |= Q(profile__phone_number__in=['+' + number for number in phones])
                if query:
                    matches = User.objects.select_related('profile').exclude(pk=request.user.pk).filter(query).distinct()[:100]
            except Exception:
                error = 'We could not read that contacts file. Please try exporting it again.'
    following = set(Follow.objects.filter(follower=request.user, following__in=matches).values_list('following_id', flat=True)) if matches else set()
    requested = set(FollowRequest.objects.filter(requester=request.user, target__in=matches).values_list('target_id', flat=True)) if matches else set()
    return render(request, 'social/contacts.html', {'matches': matches, 'error': error, 'following_ids': following, 'requested_ids': requested, 'active': 'contacts'})

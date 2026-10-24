from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse
from .models import Comment, Follow, FollowRequest, Like, Notification, Post, Profile

User = get_user_model()

class SocialFlowTests(TestCase):
    password = 'Strong!passphrase-42'

    def make_user(self, username, email=None, private=False):
        user = User.objects.create_user(username=username, email=email or f'{username}@example.test', password=self.password)
        user.profile.is_private = private
        user.profile.save()
        return user

    def test_register_and_login_with_email(self):
        response = self.client.post(reverse('social:register'), {
            'username': 'newviewer', 'email': 'new@example.test', 'full_name': 'New Viewer', 'phone_number': '+14155550123',
            'password1': self.password, 'password2': self.password,
        })
        self.assertRedirects(response, reverse('social:home'))
        user = User.objects.get(username='newviewer')
        self.assertEqual(user.profile.full_name, 'New Viewer')
        self.assertEqual(user.profile.phone_number, '+14155550123')
        self.client.post(reverse('social:logout'))
        response = self.client.post(reverse('social:login'), {'username': 'new@example.test', 'password': self.password})
        self.assertRedirects(response, reverse('social:home'))
        self.client.post(reverse('social:logout'))
        response = self.client.post(reverse('social:login'), {'username': '+14155550123', 'password': self.password})
        self.assertRedirects(response, reverse('social:home'))

    def test_username_is_case_insensitively_unique(self):
        self.make_user('reader')
        response = self.client.post(reverse('social:register'), {
            'username': 'READER', 'email': 'other@example.test',
            'password1': self.password, 'password2': self.password,
        })
        self.assertEqual(response.status_code, 200)
        self.assertEqual(User.objects.filter(username__iexact='reader').count(), 1)

    def test_public_follow_like_comment_and_permissions(self):
        author = self.make_user('author')
        self.make_user('viewer')
        post = Post.objects.create(author=author, caption='A real post')
        self.client.login(username='viewer', password=self.password)
        response = self.client.get(reverse('social:home'))
        self.assertEqual(response.status_code, 200)
        self.assertNotContains(response, 'A real post')
        self.client.post(reverse('social:follow_toggle', args=['author']))
        self.assertTrue(Follow.objects.filter(follower__username='viewer', following=author).exists())
        response = self.client.get(reverse('social:home'))
        self.assertContains(response, 'A real post')
        like_url = reverse('social:toggle_like', args=[post.pk])
        self.assertEqual(self.client.post(like_url).json(), {'liked': True, 'count': 1})
        self.assertEqual(self.client.post(like_url).json(), {'liked': False, 'count': 0})
        self.client.post(reverse('social:add_comment', args=[post.pk]), {'content': 'Nice view!'})
        self.assertTrue(Comment.objects.filter(post=post, content='Nice view!').exists())
        self.assertTrue(Notification.objects.filter(recipient=author, notification_type='comment').exists())
        self.assertEqual(self.client.post(reverse('social:edit_post', args=[post.pk])).status_code, 404)

    def test_private_account_requires_approval_before_posts_are_visible(self):
        owner = self.make_user('privateowner', private=True)
        self.make_user('follower')
        post = Post.objects.create(author=owner, caption='Only for approved followers')
        self.client.login(username='follower', password=self.password)
        self.assertEqual(self.client.get(reverse('social:post_detail', args=[post.pk])).status_code, 404)
        self.client.post(reverse('social:follow_toggle', args=[owner.username]))
        request = FollowRequest.objects.get(requester__username='follower', target=owner)
        self.client.logout()
        self.client.login(username=owner.username, password=self.password)
        self.client.post(reverse('social:resolve_follow_request', args=[request.pk, 'approve']))
        self.assertTrue(Follow.objects.filter(follower__username='follower', following=owner).exists())
        self.client.logout()
        self.client.login(username='follower', password=self.password)
        self.assertContains(self.client.get(reverse('social:post_detail', args=[post.pk])), 'Only for approved followers')

    def test_profile_update_and_authentication_protection(self):
        self.assertRedirects(self.client.get(reverse('social:home')), f"{reverse('social:login')}?next=/")
        user = self.make_user('editor')
        self.client.login(username='editor', password=self.password)
        response = self.client.post(reverse('social:edit_profile'), {
            'username': 'editor', 'full_name': 'Profile Editor', 'bio': 'A short bio',
            'is_private': 'on',
        })
        self.assertRedirects(response, reverse('social:profile', args=['editor']))
        user.profile.refresh_from_db()
        self.assertEqual(user.profile.full_name, 'Profile Editor')
        self.assertTrue(user.profile.is_private)

    def test_post_creation_rejects_invalid_media_and_accepts_text(self):
        user = self.make_user('creator')
        self.client.login(username='creator', password=self.password)
        response = self.client.post(reverse('social:create_post'), {
            'caption': 'Text thought', 'visibility': 'public',
        })
        self.assertEqual(response.status_code, 302)
        text_post = Post.objects.get(author=user)
        self.assertEqual(text_post.media_type, 'text')
        response = self.client.post(reverse('social:create_post'), {
            'caption': 'Bad file', 'visibility': 'public',
            'media': __import__('django.core.files.uploadedfile', fromlist=['SimpleUploadedFile']).SimpleUploadedFile('bad.png', b'not an image'),
        })
        self.assertEqual(response.status_code, 200)
        self.assertEqual(Post.objects.filter(author=user).count(), 1)
    def test_remaining_pages_render_for_authenticated_user(self):
        owner = self.make_user('pageowner')
        stranger = self.make_user('pageviewer')
        private_owner = self.make_user('pendingowner', private=True)
        post = Post.objects.create(author=owner, caption='Detail page')
        FollowRequest.objects.create(requester=stranger, target=private_owner)
        self.client.login(username='pageviewer', password=self.password)
        paths = [
            reverse('social:search'), reverse('social:contacts'), reverse('social:explore'),
            reverse('social:notifications'), reverse('social:follow_requests'),
            reverse('social:profile', args=['pageviewer']),
            reverse('social:profile', args=['pageowner']),
            reverse('social:people_list', args=['pageowner', 'followers']),
            reverse('social:people_list', args=['pageowner', 'following']),
            reverse('social:post_detail', args=[post.pk]),
            reverse('social:create_post'),
            reverse('social:edit_profile'),
        ]
        for path in paths:
            with self.subTest(path=path):
                self.assertEqual(self.client.get(path).status_code, 200)


    def test_vcard_contact_matching(self):
        from django.core.files.uploadedfile import SimpleUploadedFile
        friend = self.make_user('contactfriend', email='friend@example.test')
        friend.profile.phone_number = '+14155550999'
        friend.profile.save()
        self.make_user('contactowner')
        self.client.login(username='contactowner', password=self.password)
        card = b'BEGIN:VCARD\nVERSION:3.0\nFN:Friend\nEMAIL:friend@example.test\nTEL:+1 415 555 0999\nEND:VCARD\n'
        response = self.client.post(reverse('social:contacts'), {
            'contacts_file': SimpleUploadedFile('contacts.vcf', card, content_type='text/vcard'),
        })
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, '@contactfriend')


    def test_owner_can_edit_and_delete_post_and_comment(self):
        owner = self.make_user('owneredit')
        self.client.login(username=owner.username, password=self.password)
        post = Post.objects.create(author=owner, caption='Original caption')
        response = self.client.post(reverse('social:edit_post', args=[post.pk]), {
            'caption': 'Updated caption', 'visibility': 'public',
        })
        self.assertRedirects(response, reverse('social:post_detail', args=[post.pk]))
        post.refresh_from_db()
        self.assertEqual(post.caption, 'Updated caption')
        self.client.post(reverse('social:add_comment', args=[post.pk]), {'content': 'My comment'})
        comment = Comment.objects.get(post=post)
        self.assertEqual(self.client.post(reverse('social:delete_comment', args=[comment.pk])).status_code, 302)
        self.assertFalse(Comment.objects.filter(pk=comment.pk).exists())
        self.assertEqual(self.client.post(reverse('social:delete_post', args=[post.pk])).status_code, 302)
        self.assertFalse(Post.objects.filter(pk=post.pk).exists())

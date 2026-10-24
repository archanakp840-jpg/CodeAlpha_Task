from pathlib import Path
import re
from django import forms
from django.contrib.auth import get_user_model
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm
from django.core.exceptions import ValidationError
from PIL import Image, UnidentifiedImageError
from .models import Profile, Post, Comment

User = get_user_model()
MAX_IMAGE = 8 * 1024 * 1024
MAX_VIDEO = 30 * 1024 * 1024

def validate_phone(value):
    value = re.sub(r'[^0-9+]', '', value or '')
    if value and not re.fullmatch(r'\+?[1-9]\d{7,14}', value):
        raise ValidationError('Enter a valid phone number with 8 to 15 digits.')
    return value
IMAGE_EXTS = {'.jpg', '.jpeg', '.png', '.webp', '.gif'}
VIDEO_EXTS = {'.mp4', '.webm', '.mov'}

class SignupForm(UserCreationForm):
    email = forms.EmailField()
    full_name = forms.CharField(max_length=100, required=False)
    phone_number = forms.CharField(max_length=20, required=True, label='Phone number')
    class Meta:
        model = User
        fields = ('username', 'email', 'phone_number', 'full_name', 'password1', 'password2')
    def clean_username(self):
        value = self.cleaned_data['username'].strip()
        if User.objects.filter(username__iexact=value).exists():
            raise ValidationError('That username is already taken.')
        return value
    def clean_email(self):
        value = self.cleaned_data['email'].strip().lower()
        if User.objects.filter(email__iexact=value).exists():
            raise ValidationError('An account already uses this email.')
        return value
    def clean_phone_number(self):
        value = validate_phone(self.cleaned_data.get('phone_number', ''))
        if value and Profile.objects.filter(phone_number=value).exists():
            raise ValidationError('That phone number is already connected to an account.')
        return value
    def save(self, commit=True):
        user = super().save(commit=False)
        user.email = self.cleaned_data['email'].lower()
        if commit:
            user.save()
            user.profile.full_name = self.cleaned_data.get('full_name', '')
            user.profile.phone_number = self.cleaned_data.get('phone_number', '')
            user.profile.save()
        return user

class LoginForm(AuthenticationForm):
    username = forms.CharField(label='Username or email')
    def clean(self):
        identifier = self.cleaned_data.get('username', '').strip()
        if '@' in identifier:
            user = User.objects.filter(email__iexact=identifier).first()
            if user:
                self.cleaned_data['username'] = user.get_username()
        elif not User.objects.filter(username__iexact=identifier).exists():
            phone = validate_phone(identifier)
            user = User.objects.filter(profile__phone_number=phone).first() if phone else None
            if user:
                self.cleaned_data['username'] = user.get_username()
        return super().clean()

class ProfileForm(forms.ModelForm):
    username = forms.CharField(max_length=150)
    class Meta:
        model = Profile
        fields = ('full_name', 'phone_number', 'bio', 'profile_picture', 'is_private')
        widgets = {'bio': forms.Textarea(attrs={'rows': 3, 'maxlength': 160})}
    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop('user')
        super().__init__(*args, **kwargs)
        self.fields['username'].initial = self.user.username
        self.fields['profile_picture'].required = False
    def clean_username(self):
        value = self.cleaned_data['username'].strip()
        if User.objects.filter(username__iexact=value).exclude(pk=self.user.pk).exists():
            raise ValidationError('That username is already taken.')
        return value
    def clean_phone_number(self):
        value = validate_phone(self.cleaned_data.get('phone_number', ''))
        if value and Profile.objects.filter(phone_number=value).exclude(pk=self.instance.pk).exists():
            raise ValidationError('That phone number is already connected to an account.')
        return value
    def clean_profile_picture(self):
        image = self.cleaned_data.get('profile_picture')
        if image and image.size > MAX_IMAGE:
            raise ValidationError('Profile pictures must be 8 MB or smaller.')
        if image:
            try:
                data = Image.open(image)
                data.verify()
                if data.format not in {'JPEG', 'PNG', 'WEBP', 'GIF'}:
                    raise ValidationError('Choose a JPEG, PNG, WebP, or GIF profile picture.')
            except (UnidentifiedImageError, OSError):
                raise ValidationError('That file is not a valid image.')
            image.seek(0)
        return image
    def save(self, commit=True):
        profile = super().save(commit=False)
        self.user.username = self.cleaned_data['username']
        if commit:
            self.user.save(update_fields=['username'])
            profile.save()
        return profile

class PostForm(forms.ModelForm):
    class Meta:
        model = Post
        fields = ('caption', 'visibility', 'media')
        widgets = {'caption': forms.Textarea(attrs={'rows': 3, 'maxlength': 2000, 'placeholder': 'Write a caption…'})}
    def clean_media(self):
        f = self.cleaned_data.get('media')
        if not f:
            return f
        ext = Path(f.name).suffix.lower()
        if ext in IMAGE_EXTS:
            if f.size > MAX_IMAGE:
                raise ValidationError('Photos must be 8 MB or smaller.')
            try:
                image = Image.open(f)
                image.verify()
                if image.format not in {'JPEG', 'PNG', 'WEBP', 'GIF'}:
                    raise ValidationError('Choose a JPEG, PNG, WebP, or GIF photo.')
            except (UnidentifiedImageError, OSError):
                raise ValidationError('That file is not a valid image.')
            self.media_type = 'image'
        elif ext in VIDEO_EXTS:
            if f.size > MAX_VIDEO:
                raise ValidationError('Videos must be 30 MB or smaller.')
            self.media_type = 'video'
        else:
            raise ValidationError('Choose a JPEG, PNG, WebP, GIF, MP4, WebM, or MOV file.')
        f.seek(0)
        return f
    def save(self, commit=True):
        post = super().save(commit=False)
        post.media_type = getattr(self, 'media_type', 'text') if post.media else 'text'
        if commit:
            post.save()
        return post

class CommentForm(forms.ModelForm):
    class Meta:
        model = Comment
        fields = ('content',)
        widgets = {'content': forms.TextInput(attrs={'placeholder': 'Add a comment…', 'maxlength': 500})}
    def clean_content(self):
        value = self.cleaned_data['content'].strip()
        if not value:
            raise ValidationError('Write something before posting your comment.')
        return value

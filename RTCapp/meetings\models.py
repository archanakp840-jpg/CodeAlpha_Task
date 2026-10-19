import secrets, string
from django.conf import settings
from django.db import models
from django.utils import timezone

def meeting_code():
    return "".join(secrets.choice(string.ascii_lowercase+string.digits) for _ in range(12))
def private_upload_path(instance, filename):
    ext=filename.rsplit(".",1)[-1].lower() if "." in filename else "bin"
    return f"meeting_files/{instance.meeting_id}/{secrets.token_hex(16)}.{ext}"
class Meeting(models.Model):
    title=models.CharField(max_length=120,default="Quick meeting")
    code=models.CharField(max_length=16,unique=True,default=meeting_code,db_index=True)
    host=models.ForeignKey(settings.AUTH_USER_MODEL,on_delete=models.CASCADE,related_name="hosted_meetings")
    description=models.TextField(blank=True,max_length=1000)
    scheduled_at=models.DateTimeField(null=True,blank=True)
    started_at=models.DateTimeField(null=True,blank=True)
    ended_at=models.DateTimeField(null=True,blank=True)
    status=models.CharField(max_length=12,choices=[("scheduled","Scheduled"),("live","Live"),("ended","Ended")],default="live",db_index=True)
    is_private=models.BooleanField(default=False)
    created_at=models.DateTimeField(auto_now_add=True)
    participants=models.ManyToManyField(settings.AUTH_USER_MODEL,through="MeetingParticipant",related_name="connectify_meetings")
    def __str__(self): return f"{self.title} ({self.code})"

class UserPreferences(models.Model):
    user=models.OneToOneField(settings.AUTH_USER_MODEL,on_delete=models.CASCADE,related_name="connectify_preferences")
    audio_input_id=models.CharField(max_length=255,blank=True)
    video_input_id=models.CharField(max_length=255,blank=True)
    updated_at=models.DateTimeField(auto_now=True)
class MeetingParticipant(models.Model):
    meeting=models.ForeignKey(Meeting,on_delete=models.CASCADE,related_name="memberships")
    user=models.ForeignKey(settings.AUTH_USER_MODEL,on_delete=models.CASCADE,related_name="meeting_memberships")
    joined_at=models.DateTimeField(default=timezone.now)
    left_at=models.DateTimeField(null=True,blank=True)
    role=models.CharField(max_length=12,choices=[("host","Host"),("participant","Participant")],default="participant")
    class Meta: constraints=[models.UniqueConstraint(fields=["meeting","user"],name="unique_meeting_member")]
class SharedFile(models.Model):
    meeting=models.ForeignKey(Meeting,on_delete=models.CASCADE,related_name="files")
    uploader=models.ForeignKey(settings.AUTH_USER_MODEL,on_delete=models.CASCADE)
    original_name=models.CharField(max_length=255)
    file=models.FileField(upload_to=private_upload_path)
    size=models.PositiveBigIntegerField()
    mime_type=models.CharField(max_length=120,blank=True)
    uploaded_at=models.DateTimeField(auto_now_add=True)
class ChatMessage(models.Model):
    meeting=models.ForeignKey(Meeting,on_delete=models.CASCADE,related_name="messages")
    sender=models.ForeignKey(settings.AUTH_USER_MODEL,on_delete=models.CASCADE)
    text=models.CharField(max_length=2000)
    created_at=models.DateTimeField(auto_now_add=True)
    class Meta: ordering=["created_at"]
class WhiteboardSession(models.Model):
    meeting=models.OneToOneField(Meeting,on_delete=models.CASCADE,related_name="whiteboard")
    state=models.JSONField(default=list,blank=True)
    updated_at=models.DateTimeField(auto_now=True)

from django.contrib import admin
from .models import Meeting,MeetingParticipant,SharedFile,ChatMessage,WhiteboardSession
admin.site.register([Meeting,MeetingParticipant,SharedFile,ChatMessage,WhiteboardSession])

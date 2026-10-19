from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion
import django.utils.timezone
import meetings.models

class Migration(migrations.Migration):
    initial=True
    dependencies=[migrations.swappable_dependency(settings.AUTH_USER_MODEL)]
    operations=[
        migrations.CreateModel(name="Meeting",fields=[
            ("id",models.BigAutoField(auto_created=True,primary_key=True,serialize=False,verbose_name="ID")),
            ("title",models.CharField(default="Quick meeting",max_length=120)),
            ("code",models.CharField(db_index=True,default=meetings.models.meeting_code,max_length=16,unique=True)),
            ("description",models.TextField(blank=True,max_length=1000)),
            ("scheduled_at",models.DateTimeField(blank=True,null=True)),
            ("started_at",models.DateTimeField(blank=True,null=True)),
            ("ended_at",models.DateTimeField(blank=True,null=True)),
            ("status",models.CharField(choices=[("scheduled","Scheduled"),("live","Live"),("ended","Ended")],db_index=True,default="live",max_length=12)),
            ("is_private",models.BooleanField(default=False)),
            ("created_at",models.DateTimeField(auto_now_add=True)),
            ("host",models.ForeignKey(on_delete=django.db.models.deletion.CASCADE,related_name="hosted_meetings",to=settings.AUTH_USER_MODEL)),
        ]),
        migrations.CreateModel(name="MeetingParticipant",fields=[
            ("id",models.BigAutoField(auto_created=True,primary_key=True,serialize=False,verbose_name="ID")),
            ("joined_at",models.DateTimeField(default=django.utils.timezone.now)),
            ("left_at",models.DateTimeField(blank=True,null=True)),
            ("role",models.CharField(choices=[("host","Host"),("participant","Participant")],default="participant",max_length=12)),
            ("meeting",models.ForeignKey(on_delete=django.db.models.deletion.CASCADE,related_name="memberships",to="meetings.meeting")),
            ("user",models.ForeignKey(on_delete=django.db.models.deletion.CASCADE,related_name="meeting_memberships",to=settings.AUTH_USER_MODEL)),
        ],options={"constraints":[models.UniqueConstraint(fields=("meeting","user"),name="unique_meeting_member")]}),
        migrations.AddField(model_name="meeting",name="participants",field=models.ManyToManyField(related_name="connectify_meetings",through="meetings.MeetingParticipant",to=settings.AUTH_USER_MODEL)),
        migrations.CreateModel(name="SharedFile",fields=[
            ("id",models.BigAutoField(auto_created=True,primary_key=True,serialize=False,verbose_name="ID")),
            ("original_name",models.CharField(max_length=255)),("file",models.FileField(upload_to=meetings.models.private_upload_path)),
            ("size",models.PositiveBigIntegerField()),("mime_type",models.CharField(blank=True,max_length=120)),("uploaded_at",models.DateTimeField(auto_now_add=True)),
            ("meeting",models.ForeignKey(on_delete=django.db.models.deletion.CASCADE,related_name="files",to="meetings.meeting")),
            ("uploader",models.ForeignKey(on_delete=django.db.models.deletion.CASCADE,to=settings.AUTH_USER_MODEL)),
        ]),
        migrations.CreateModel(name="ChatMessage",fields=[
            ("id",models.BigAutoField(auto_created=True,primary_key=True,serialize=False,verbose_name="ID")),
            ("text",models.CharField(max_length=2000)),("created_at",models.DateTimeField(auto_now_add=True)),
            ("meeting",models.ForeignKey(on_delete=django.db.models.deletion.CASCADE,related_name="messages",to="meetings.meeting")),
            ("sender",models.ForeignKey(on_delete=django.db.models.deletion.CASCADE,to=settings.AUTH_USER_MODEL)),
        ],options={"ordering":["created_at"]}),
        migrations.CreateModel(name="WhiteboardSession",fields=[
            ("id",models.BigAutoField(auto_created=True,primary_key=True,serialize=False,verbose_name="ID")),
            ("state",models.JSONField(blank=True,default=list)),("updated_at",models.DateTimeField(auto_now=True)),
            ("meeting",models.OneToOneField(on_delete=django.db.models.deletion.CASCADE,related_name="whiteboard",to="meetings.meeting")),
        ]),
    ]


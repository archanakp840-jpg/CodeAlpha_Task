from django.test import TestCase,Client
from django.contrib.auth.models import User
from django.core.files.uploadedfile import SimpleUploadedFile
from .models import Meeting,MeetingParticipant,SharedFile
class ConnectifyTests(TestCase):
 def setUp(self):
  self.host=User.objects.create_user("host",password="SafePass123!")
  self.guest=User.objects.create_user("guest",password="SafePass123!")
  self.meeting=Meeting.objects.create(host=self.host,title="Test room",status="live")
  MeetingParticipant.objects.create(meeting=self.meeting,user=self.host,role="host")
 def test_register_login_logout(self):
  r=self.client.post("/register/",{"name":"New User","username":"newuser","email":"n@example.com","password":"SafePass123!abc","confirm_password":"SafePass123!abc","terms":"on"})
  self.assertEqual(r.status_code,302); self.assertTrue(User.objects.filter(username="newuser").exists())
  self.client.post("/logout/"); r=self.client.post("/login/",{"identity":"host","password":"SafePass123!"}); self.assertEqual(r.status_code,302)
 def test_protected_dashboard_and_meeting_join(self):
  c=Client(); self.assertEqual(c.get("/dashboard/").status_code,302)
  c.force_login(self.guest); r=c.post("/meetings/join/",{"code":self.meeting.code}); self.assertEqual(r.status_code,302)
  self.assertTrue(MeetingParticipant.objects.filter(meeting=self.meeting,user=self.guest).exists())
 def test_private_meeting_denies_nonmember(self):
  self.meeting.is_private=True; self.meeting.save(); c=Client(); c.force_login(self.guest)
  self.assertEqual(c.get(f"/meetings/{self.meeting.code}/").status_code,403)
 def test_host_only_end(self):
  c=Client(); c.force_login(self.guest); self.assertEqual(c.post(f"/meetings/{self.meeting.code}/end/").status_code,404)
 def test_file_upload_type_and_authorized_download(self):
  MeetingParticipant.objects.create(meeting=self.meeting,user=self.guest)
  c=Client(); c.force_login(self.guest)
  r=c.post(f"/api/meetings/{self.meeting.code}/files/upload/",{"file":SimpleUploadedFile("notes.txt",b"hello")})
  self.assertEqual(r.status_code,200); item=SharedFile.objects.get()
  self.assertEqual(c.get(f"/files/{item.id}/download/").status_code,200)
  self.assertEqual(c.post(f"/api/meetings/{self.meeting.code}/files/upload/",{"file":SimpleUploadedFile("bad.exe",b"hello")}).status_code,415)
  c.force_login(User.objects.create_user("stranger",password="SafePass123!"))
  self.assertEqual(c.get(f"/files/{item.id}/download/").status_code,403)
 def test_schedule_meeting_and_profile_settings(self):
  from datetime import timedelta
  from django.utils import timezone
  c=Client(); c.force_login(self.host)
  future=(timezone.now()+timedelta(days=1)).strftime("%Y-%m-%dT%H:%M")
  response=c.post("/meetings/schedule/",{"title":"Planning","scheduled_at":future,"description":"Roadmap"})
  self.assertEqual(response.status_code,302)
  scheduled=Meeting.objects.get(title="Planning")
  self.assertEqual(scheduled.status,"scheduled"); self.assertEqual(scheduled.host,self.host)
  response=c.post("/profile/",{"name":"Host Name","audio_input_id":"mic-1","video_input_id":"cam-1"})
  self.assertEqual(response.status_code,302)
  self.host.refresh_from_db(); self.assertEqual(self.host.first_name,"Host Name")
  self.assertEqual(self.host.connectify_preferences.audio_input_id,"mic-1")


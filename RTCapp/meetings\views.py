import json,os,mimetypes
from datetime import datetime
from django.conf import settings
from django.contrib import messages
from django.contrib.auth import authenticate,login,logout
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError
from django.core.validators import validate_email
from django.db.models import Q
from django.http import JsonResponse,FileResponse,HttpResponseForbidden
from django.shortcuts import get_object_or_404,redirect,render
from django.utils import timezone
from asgiref.sync import async_to_sync
from channels.layers import get_channel_layer
from django.views.decorators.http import require_POST
from .models import Meeting,MeetingParticipant,SharedFile,WhiteboardSession,UserPreferences
from .permissions import can_access,join_member

def home(request): return redirect("dashboard" if request.user.is_authenticated else "login")
def register(request):
    error=""
    if request.method=="POST":
        name=request.POST.get("name","").strip(); username=request.POST.get("username","").strip(); email=request.POST.get("email","").strip().lower(); password=request.POST.get("password","")
        if not all([name,username,email,password]): error="Complete every required field."
        elif request.POST.get("terms")!="on": error="Please accept the terms to continue."
        elif password!=request.POST.get("confirm_password"): error="Passwords do not match."
        elif len(username)>150: error="Usernames must be 150 characters or fewer."
        elif not valid_email(email): error="Enter a valid email address."
        elif User.objects.filter(username__iexact=username).exists() or User.objects.filter(email__iexact=email).exists(): error="That username or email is already registered."
        else:
            try: validate_password(password,User(username=username,email=email,first_name=name))
            except ValidationError as exc: return render(request,"register.html",{"error":" ".join(exc.messages)})
            user=User.objects.create_user(username=username,email=email,password=password,first_name=name[:150]); login(request,user); return redirect("dashboard")
    return render(request,"register.html",{"error":error})

def valid_email(value):
    try: validate_email(value); return True
    except ValidationError: return False
def login_view(request):
    error=""
    if request.method=="POST":
        ident=request.POST.get("identity","").strip(); password=request.POST.get("password",""); user=authenticate(request,username=ident,password=password)
        if user is None:
            u=User.objects.filter(email__iexact=ident).first()
            if u: user=authenticate(request,username=u.username,password=password)
        if user: login(request,user); return redirect("dashboard")
        error="We couldn't sign you in with those details."
    return render(request,"login.html",{"error":error})
@require_POST
def logout_view(request): logout(request); return redirect("login")
@login_required
def dashboard(request):
    meetings=Meeting.objects.filter(Q(host=request.user)|Q(memberships__user=request.user)).distinct().order_by("-created_at")[:8]
    return render(request,"dashboard.html",{"meetings":meetings,"live_count":Meeting.objects.filter(host=request.user,status="live").count(),"scheduled_count":Meeting.objects.filter(host=request.user,status="scheduled").count()})
@login_required
@require_POST
def create_meeting(request):
    meeting=Meeting.objects.create(host=request.user,title=request.POST.get("title","Quick meeting").strip()[:120] or "Quick meeting",description=request.POST.get("description","")[:1000],status="live",started_at=timezone.now())
    join_member(meeting,request.user); return redirect("room",code=meeting.code)

@login_required
@require_POST
def schedule_meeting(request):
    title=request.POST.get("title","").strip()[:120]
    when=request.POST.get("scheduled_at","").strip()
    description=request.POST.get("description","").strip()[:1000]
    try:
        scheduled=datetime.fromisoformat(when)
        if timezone.is_naive(scheduled): scheduled=timezone.make_aware(scheduled)
        if scheduled <= timezone.now(): raise ValueError
    except (ValueError,TypeError):
        messages.error(request,"Choose a valid date and time in the future.")
        return redirect("dashboard")
    meeting=Meeting.objects.create(host=request.user,title=title or "Team meeting",description=description,scheduled_at=scheduled,status="scheduled")
    join_member(meeting,request.user)
    messages.success(request,"Meeting scheduled. Share this code: "+meeting.code)
    return redirect("dashboard")

@login_required
def profile(request):
    prefs,_=UserPreferences.objects.get_or_create(user=request.user)
    if request.method=="POST":
        name=request.POST.get("name","").strip()
        if not name:
            messages.error(request,"Display name cannot be blank.")
        else:
            request.user.first_name=name[:150]
            request.user.save(update_fields=["first_name"])
            prefs.audio_input_id=request.POST.get("audio_input_id","")[:255]
            prefs.video_input_id=request.POST.get("video_input_id","")[:255]
            prefs.save()
            messages.success(request,"Profile preferences saved.")
            return redirect("profile")
    return render(request,"profile.html",{"prefs":prefs})
@login_required
def join_meeting(request):
    if request.method=="POST":
        code=request.POST.get("code","").strip().rstrip("/").split("/")[-1]; meeting=Meeting.objects.filter(code=code).first()
        if meeting and meeting.status!="ended" and (not meeting.is_private or meeting.host_id==request.user.id or MeetingParticipant.objects.filter(meeting=meeting,user=request.user).exists()): join_member(meeting,request.user); return redirect("room",code=meeting.code)
        messages.error(request,"Meeting unavailable or access denied.")
    return render(request,"join.html")
@login_required
def room(request,code):
    meeting=get_object_or_404(Meeting,code=code)
    if meeting.status=="ended": return render(request,"meeting_ended.html",{"meeting":meeting})
    if meeting.is_private and not can_access(request.user,meeting): return HttpResponseForbidden("This meeting is private.")
    join_member(meeting,request.user)
    if meeting.status=="scheduled": meeting.status="live"; meeting.started_at=timezone.now(); meeting.save(update_fields=["status","started_at"])
    board,_=WhiteboardSession.objects.get_or_create(meeting=meeting)
    hist=[{"name":m.sender.username,"text":m.text,"at":m.created_at.isoformat()} for m in meeting.messages.select_related("sender").order_by("created_at")[:100]]
    prefs,_=UserPreferences.objects.get_or_create(user=request.user)
    return render(request,"room.html",{"meeting":meeting,"is_host":meeting.host_id==request.user.id,"history":hist,"board":board.state,"prefs":prefs,"ice_servers":settings.RTC_ICE_SERVERS})
@login_required
@require_POST
def end_meeting(request,code):
    meeting=get_object_or_404(Meeting,code=code,host=request.user); meeting.status="ended"; meeting.ended_at=timezone.now(); meeting.save(update_fields=["status","ended_at"])
    async_to_sync(get_channel_layer().group_send)("meeting_"+code,{"type":"broadcast","payload":{"type":"meeting_ended"}})
    return redirect("dashboard")
@login_required
@require_POST
def leave_meeting(request,code):
    meeting=get_object_or_404(Meeting,code=code); MeetingParticipant.objects.filter(meeting=meeting,user=request.user,left_at__isnull=True).update(left_at=timezone.now()); return redirect("dashboard")
@login_required
def participant_api(request,code):
    meeting=get_object_or_404(Meeting,code=code)
    if not can_access(request.user,meeting): return JsonResponse({"error":"Not a meeting participant"},status=403)
    return JsonResponse({"participants":[{"name":m.user.username,"role":m.role} for m in meeting.memberships.filter(left_at__isnull=True).select_related("user")]})
@login_required
@require_POST
def upload_file(request,code):
    meeting=get_object_or_404(Meeting,code=code)
    if not can_access(request.user,meeting): return JsonResponse({"error":"Not authorized"},status=403)
    f=request.FILES.get("file")
    if not f: return JsonResponse({"error":"Choose a file first."},status=400)
    ext=os.path.splitext(f.name)[1].lower().lstrip(".")
    if f.size>settings.MAX_UPLOAD_BYTES: return JsonResponse({"error":"File exceeds the size limit."},status=413)
    if ext not in {"pdf","png","jpg","jpeg","gif","txt","md","csv","docx","xlsx","pptx","zip"}: return JsonResponse({"error":"File type is not supported."},status=415)
    item=SharedFile.objects.create(meeting=meeting,uploader=request.user,original_name=os.path.basename(f.name)[:255],file=f,size=f.size,mime_type=mimetypes.guess_type(f.name)[0] or "application/octet-stream")
    return JsonResponse({"id":item.id,"name":item.original_name,"size":item.size,"uploader":request.user.username,"url":f"/files/{item.id}/download/"})
@login_required
def files_api(request,code):
    meeting=get_object_or_404(Meeting,code=code)
    if not can_access(request.user,meeting): return JsonResponse({"error":"Not authorized"},status=403)
    return JsonResponse({"files":[{"id":x.id,"name":x.original_name,"size":x.size,"uploader":x.uploader.username,"url":f"/files/{x.id}/download/","uploaded_at":x.uploaded_at.isoformat()} for x in meeting.files.select_related("uploader").order_by("-uploaded_at")]})
@login_required
def download_file(request,file_id):
    item=get_object_or_404(SharedFile.objects.select_related("meeting"),pk=file_id)
    if not can_access(request.user,item.meeting): return HttpResponseForbidden("Not authorized")
    return FileResponse(item.file.open("rb"),as_attachment=True,filename=item.original_name)


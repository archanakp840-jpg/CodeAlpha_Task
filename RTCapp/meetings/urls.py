from django.urls import path
from . import views
urlpatterns=[
 path("register/",views.register,name="register"),path("login/",views.login_view,name="login"),path("logout/",views.logout_view,name="logout"),
 path("dashboard/",views.dashboard,name="dashboard"),path("profile/",views.profile,name="profile"),path("meetings/create/",views.create_meeting,name="create_meeting"),path("meetings/schedule/",views.schedule_meeting,name="schedule_meeting"),path("meetings/join/",views.join_meeting,name="join_meeting"),
 path("meetings/<str:code>/",views.room,name="room"),path("meetings/<str:code>/end/",views.end_meeting,name="end_meeting"),path("meetings/<str:code>/leave/",views.leave_meeting,name="leave_meeting"),
 path("api/meetings/<str:code>/participants/",views.participant_api,name="participants"),path("api/meetings/<str:code>/files/",views.files_api,name="files_api"),path("api/meetings/<str:code>/files/upload/",views.upload_file,name="upload_file"),path("files/<int:file_id>/download/",views.download_file,name="download_file")
]

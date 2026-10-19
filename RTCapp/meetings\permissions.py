from .models import MeetingParticipant
def can_access(user,meeting):
    return user.is_authenticated and (meeting.host_id==user.id or MeetingParticipant.objects.filter(meeting=meeting,user=user,left_at__isnull=True).exists())
def join_member(meeting,user):
    from django.utils import timezone
    member,_=MeetingParticipant.objects.get_or_create(meeting=meeting,user=user,defaults={"role":"host" if meeting.host_id==user.id else "participant"})
    if member.left_at:
        member.joined_at=timezone.now(); member.left_at=None; member.save(update_fields=["joined_at","left_at"])
    return member

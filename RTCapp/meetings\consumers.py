import json
from channels.generic.websocket import AsyncJsonWebsocketConsumer
from channels.db import database_sync_to_async
from .models import Meeting,MeetingParticipant

class MeetingConsumer(AsyncJsonWebsocketConsumer):
 async def connect(self):
  user=self.scope["user"]; self.code=self.scope["url_route"]["kwargs"]["code"]; self.room="meeting_"+self.code
  if not user.is_authenticated or not await self.authorized(user): await self.close(code=4403); return
  await self.channel_layer.group_add(self.room,self.channel_name); await self.accept()
  await self.send_json({"type":"room_peers","peers":await self.peer_names(user)})
  await self.send_json({"type":"board_state","actions":await self.load_board()})
  await self.channel_layer.group_send(self.room,{"type":"broadcast","payload":{"type":"peer_joined","id":user.username}})
 async def disconnect(self,code):
  if hasattr(self,"room"):
   await self.channel_layer.group_send(self.room,{"type":"broadcast","payload":{"type":"peer_left","id":self.scope["user"].username}})
   await self.channel_layer.group_discard(self.room,self.channel_name)
   if self.scope["user"].is_authenticated: await self.mark_left(self.scope["user"])
 async def receive_json(self,data):
  if not await self.authorized(self.scope["user"]): await self.close(code=4403); return
  kind=data.get("type")
  if kind not in {"signal","chat","draw","clear","undo","share","ready"}: return
  if kind=="ready": return
  if kind=="chat":
   text=str(data.get("text","")).strip()
   if not text or len(text)>2000: return
   await self.save_chat(text); data={"type":"chat","name":self.scope["user"].username,"text":text}
  elif kind=="draw":
   action=data.get("action")
   if not self.valid_action(action): return
   await self.save_action(action)
   data={"type":"draw","action":action}
  elif kind=="clear":
   if not await self.is_host(): return
   await self.clear_board()
   data={"type":"clear"}
  elif kind=="undo":
   await self.undo_action()
   data={"type":"undo"}
  elif kind=="share": data={"type":"share","active":bool(data.get("active")),"name":self.scope["user"].username}
  else:
   target=data.get("target")
   if not isinstance(target,str) or len(json.dumps(data))>100000: return
   data={**data,"from":self.scope["user"].username}
   await self.channel_layer.group_send(self.room,{"type":"broadcast","payload":data,"exclude":self.channel_name}); return
  await self.channel_layer.group_send(self.room,{"type":"broadcast","payload":data})
 async def broadcast(self,event):
  if event.get("exclude")==self.channel_name: return
  await self.send_json(event["payload"])
 @database_sync_to_async
 def authorized(self,user):
  try:
   m=Meeting.objects.get(code=self.code)
   return m.status!="ended" and (m.host_id==user.id or MeetingParticipant.objects.filter(meeting=m,user=user,left_at__isnull=True).exists())
  except Meeting.DoesNotExist: return False
 @database_sync_to_async
 def peer_names(self,user):
  return list(MeetingParticipant.objects.filter(meeting__code=self.code,left_at__isnull=True).exclude(user=user).values_list("user__username",flat=True))
 @staticmethod
 def valid_action(action):
  if not isinstance(action,dict) or len(json.dumps(action))>10000: return False
  points=action.get("points")
  if not isinstance(points,list) or not points or len(points)>1000: return False
  if not isinstance(action.get("color"),str) or len(action["color"])!=7 or not action["color"].startswith("#"): return False
  if not isinstance(action.get("size"),(int,float)) or not 1<=action["size"]<=32: return False
  return all(isinstance(p,list) and len(p)==2 and all(isinstance(v,(int,float)) and 0<=v<=1 for v in p) for p in points)
 @database_sync_to_async
 def load_board(self):
  from .models import WhiteboardSession
  try: return WhiteboardSession.objects.get(meeting__code=self.code).state
  except WhiteboardSession.DoesNotExist: return []
 @database_sync_to_async
 def save_action(self,action):
  from .models import WhiteboardSession
  board,_=WhiteboardSession.objects.get_or_create(meeting=Meeting.objects.get(code=self.code))
  board.state=(board.state+[action])[-2000:]; board.save(update_fields=["state","updated_at"])
 @database_sync_to_async
 def clear_board(self):
  from .models import WhiteboardSession
  board,_=WhiteboardSession.objects.get_or_create(meeting=Meeting.objects.get(code=self.code)); board.state=[]; board.save(update_fields=["state","updated_at"])
 @database_sync_to_async
 def is_host(self): return Meeting.objects.filter(code=self.code,host=self.scope["user"]).exists()
 @database_sync_to_async
 def save_chat(self,text): Meeting.objects.get(code=self.code).messages.create(sender=self.scope["user"],text=text)
 @database_sync_to_async
 def undo_action(self):
  from .models import WhiteboardSession
  try:
   board=WhiteboardSession.objects.get(meeting__code=self.code)
   board.state=board.state[:-1]; board.save(update_fields=["state","updated_at"])
  except WhiteboardSession.DoesNotExist: pass
 @database_sync_to_async
 def mark_left(self,user):
  from django.utils import timezone
  MeetingParticipant.objects.filter(meeting__code=self.code,user=user,left_at__isnull=True).update(left_at=timezone.now())


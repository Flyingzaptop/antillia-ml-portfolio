from django.db import models
from django.contrib.auth.models import User
class Document(models.Model):
 title=models.CharField(max_length=200)
 language=models.CharField(max_length=2,default='pl')
 body=models.TextField()
 access=models.CharField(max_length=10,default='all')
 created=models.DateTimeField(auto_now_add=True)
class Chunk(models.Model):
 document=models.ForeignKey(Document,on_delete=models.CASCADE,related_name='chunks')
 position=models.PositiveIntegerField()
 text=models.TextField()
 vector=models.JSONField(default=list)
class Chat(models.Model):
 owner=models.ForeignKey(User,on_delete=models.CASCADE)
 title=models.CharField(max_length=100,default='Nowa rozmowa')
 created=models.DateTimeField(auto_now_add=True)
class Message(models.Model):
 chat=models.ForeignKey(Chat,on_delete=models.CASCADE,related_name='messages')
 role=models.CharField(max_length=10)
 text=models.TextField()
 sources=models.JSONField(default=list)
 created=models.DateTimeField(auto_now_add=True)

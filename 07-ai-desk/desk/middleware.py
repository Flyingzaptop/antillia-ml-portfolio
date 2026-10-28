import json,time,uuid,logging
from django.conf import settings
class RequestLog:
 def __init__(self,get_response):
  self.get_response=get_response
  folder=settings.BASE_DIR/'logs'; folder.mkdir(exist_ok=True)
  self.logger=logging.getLogger('desk.http'); self.logger.setLevel(logging.DEBUG)
  if not self.logger.handlers:self.logger.addHandler(logging.FileHandler(folder/'requests.jsonl',encoding='utf-8'))
 def __call__(self,request):
  request.request_id=uuid.uuid4().hex; start=time.perf_counter()
  response=self.get_response(request)
  response['X-Request-ID']=request.request_id
  response['Content-Security-Policy']="default-src 'self'; style-src 'self' 'unsafe-inline'; script-src 'self'; img-src 'self' data:; frame-ancestors 'none'"
  response['X-Frame-Options']='DENY'
  self.logger.info(json.dumps({'request_id':request.request_id,'user_id':getattr(getattr(request,'user',None),'pk',None),'method':request.method,'path':request.path,'status':response.status_code,'ms':round((time.perf_counter()-start)*1000)}))
  return response

import numpy as np
import re
from functools import lru_cache
from django.conf import settings
from .models import Chunk
@lru_cache(maxsize=1)
def encoder():
 import torch
 torch.set_num_threads(2)
 from sentence_transformers import SentenceTransformer
 return SentenceTransformer(str(settings.BASE_DIR/'artifacts'/'encoder'),device='cpu',local_files_only=True)
def encode(texts):return encoder().encode(texts,normalize_embeddings=True,show_progress_bar=False).tolist()
def role(user):return 'admin' if user.is_superuser else ('editor' if user.groups.filter(name='editor').exists() else 'user')
def allowed(user):return ['all','staff','admin'] if role(user)=='admin' else (['all','staff'] if role(user)=='editor' else ['all'])
def retrieve(user,query):
 # ACL is applied in SQL before vectors are materialized or ranked.
 chunks=list(Chunk.objects.select_related('document').filter(document__access__in=allowed(user)))
 if not chunks:return []
 q=np.asarray(encode([query])[0]); scores=np.asarray([c.vector for c in chunks])@q
 # Short policy headings are often underrepresented in sentence embeddings.
 # A bounded title-overlap bonus keeps exact topic navigation dependable.
 terms=set(re.findall(r'\w{4,}',query.casefold()))
 for i,c in enumerate(chunks):
  heading=set(re.findall(r'\w{4,}',c.document.title.casefold()))
  if heading:scores[i]+=0.22*len(terms & heading)/len(heading)
 chosen=np.argsort(scores)[::-1][:4]
 return [{'id':chunks[i].id,'document_id':chunks[i].document_id,'title':chunks[i].document.title,'text':chunks[i].text,'score':round(float(scores[i]),4)} for i in chosen if scores[i]>=0.38]
def index_document(doc):
 paragraphs=[doc.body[i:i+1000] for i in range(0,len(doc.body),850)]
 vectors=encode(paragraphs)
 Chunk.objects.bulk_create([Chunk(document=doc,position=i,text=t,vector=v) for i,(t,v) in enumerate(zip(paragraphs,vectors))])

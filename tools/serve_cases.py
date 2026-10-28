"""Serve only public case-study files, never application secrets or databases."""
from http.server import SimpleHTTPRequestHandler,ThreadingHTTPServer
from pathlib import Path
from urllib.parse import urlsplit,unquote
ROOT=Path(__file__).resolve().parents[1]
PAGES={'index.html','demandcast.html','intentroute.html','terravision.html','machinesentinel.html','basketwise.html','reviewpulse.html','ai-desk.html'}
class Handler(SimpleHTTPRequestHandler):
    def do_GET(self):
        name=unquote(urlsplit(self.path).path).lstrip('/') or 'index.html';p=(ROOT/name).resolve()
        if not p.is_relative_to(ROOT) or not(name in PAGES or name.startswith('case-study-assets/')) or not p.is_file():self.send_error(404);return
        super().do_GET()
    def translate_path(self,path):return str(ROOT/(unquote(urlsplit(path).path).lstrip('/') or 'index.html'))
    def list_directory(self,path):self.send_error(404)
if __name__=='__main__':
    print('Antillia case studies: http://127.0.0.1:8090',flush=True);ThreadingHTTPServer(('127.0.0.1',8090),Handler).serve_forever()

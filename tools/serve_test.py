"""Local-only development server with the same isolation headers as the APK."""
from http.server import ThreadingHTTPServer,SimpleHTTPRequestHandler
from pathlib import Path
import argparse
parser=argparse.ArgumentParser();parser.add_argument('--port',type=int,default=8877)
args=parser.parse_args()
root=Path(__file__).resolve().parents[1]/'app/src/main/assets/engine'
class Handler(SimpleHTTPRequestHandler):
    extensions_map={**SimpleHTTPRequestHandler.extensions_map,'.wasm':'application/wasm','.js':'text/javascript'}
    def __init__(self,*a,**k):super().__init__(*a,directory=str(root),**k)
    def end_headers(self):
        self.send_header('Cross-Origin-Opener-Policy','same-origin')
        self.send_header('Cross-Origin-Embedder-Policy','require-corp')
        self.send_header('Document-Isolation-Policy','isolate-and-require-corp')
        super().end_headers()
    def log_message(self,*a):pass
print(f'Local QA: http://127.0.0.1:{args.port}/freecad-gui.html',flush=True)
ThreadingHTTPServer(('127.0.0.1',args.port),Handler).serve_forever()

"""Local-only Python backend. Run with the bundled Python or any Python 3.10+."""
from http.server import ThreadingHTTPServer, SimpleHTTPRequestHandler
from pathlib import Path
import json, webbrowser, argparse, os, hashlib, re, urllib.parse
from import_data import build
from associations import analyse

ROOT=Path(__file__).resolve().parent
PORTRAIT_MANIFEST=['survivor.png']+[f'survivor-{i:02d}.png' for i in range(1,21)]
def association_data(events):
    path=ROOT/'confirmed-teams.json'
    groups=json.loads(path.read_text(encoding='utf-8'))['groups'] if path.exists() else []
    return analyse(events,[g['profiles'] for g in groups])
def attach_portraits(dataset):
    path=ROOT/'portrait-assignments.json'
    saved=json.loads(path.read_text()) if path.exists() else {'version':1,'profiles':{}}
    mapping=saved['profiles']
    ids={e[role]['id'] for e in dataset['events'] for role in ('killer','victim')}
    changed=not path.exists()
    for pid in sorted(ids):
        if pid not in mapping:
            mapping[pid]=PORTRAIT_MANIFEST[int(hashlib.sha256(pid.encode()).hexdigest(),16)%len(PORTRAIT_MANIFEST)]
            changed=True
    if changed: path.write_text(json.dumps(saved,indent=2),encoding='utf-8')
    dataset['portraits']={pid:'/assets/'+mapping[pid] for pid in ids}
    source=ROOT/'assets/weapon-sources.json'
    dataset['weaponImages']=json.loads(source.read_text(encoding='utf-8')) if source.exists() else {}
    return dataset
class MemoryFile:
    def __init__(self, name, text): self.name=name; self.text=text
    def read_text(self, **kwargs): return self.text

class Handler(SimpleHTTPRequestHandler):
    def end_headers(self):
        self.send_header('Cache-Control','no-store')
        super().end_headers()
    def json_response(self, data, status=200):
        body=json.dumps(data).encode()
        self.send_response(status); self.send_header('Content-Type','application/json'); self.send_header('Content-Length',str(len(body))); self.end_headers(); self.wfile.write(body)
    def do_GET(self):
        if self.path=='/api/data': self.json_response(self.server.dataset)
        elif self.path.split('?')[0] in ('/','/index.html','/style.css','/app.js','/statistics.js') or re.fullmatch(r'/assets/survivor(?:-\d{2})?\.png',self.path) or re.fullmatch(r'/assets/weapons/[a-z0-9_ -]+\.(?:png|webp)',urllib.parse.unquote(self.path)): super().do_GET()
        else: self.send_error(404)
    def do_POST(self):
        if self.path!='/api/import': self.send_error(404); return
        try:
            size=int(self.headers.get('Content-Length','0'))
            if not 0<size<=150_000_000: raise ValueError('Choose exports totaling less than 150 MB.')
            payload=json.loads(self.rfile.read(size))
            files=payload['files']
            if not files: raise ValueError('Choose at least one TXT export.')
            # Rebuild a fresh, combined dataset; client filenames are never used as disk paths.
            dataset=build([MemoryFile(str(f['name']),f['text']) for f in files])
            if not dataset['events'] and not dataset['unparsed']: raise ValueError('No Discord messages found. Select copied Discord HTML TXT exports.')
            dataset['associations']=association_data(dataset['events'])
            self.json_response(attach_portraits(dataset))
        except (ValueError,KeyError,TypeError) as exc: self.json_response({'error':str(exc)},400)

if __name__=='__main__':
    parser=argparse.ArgumentParser(); parser.add_argument('--port',type=int,default=8765); parser.add_argument('--no-browser',action='store_true'); args=parser.parse_args()
    os.chdir(ROOT)
    server=ThreadingHTTPServer(('127.0.0.1',args.port),Handler)
    server.dataset=attach_portraits(build(sorted(ROOT.glob('killfeedpart*.txt'))))
    server.dataset['associations']=association_data(server.dataset['events'])
    print(f'DayZ Dossier: http://127.0.0.1:{args.port} ({len(server.dataset["events"]):,} events)',flush=True)
    if not args.no_browser: webbrowser.open(f'http://127.0.0.1:{args.port}')
    try: server.serve_forever()
    except KeyboardInterrupt: server.server_close()

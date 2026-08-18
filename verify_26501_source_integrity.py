#!/usr/bin/env python3
from pathlib import Path
import argparse,hashlib,json,sys
ALLOWED_NEW={
 'src/main/cpp/deps/archive.h','src/main/cpp/deps/archive_entry.h',
 'src/main/cpp/deps/technicallyflac.h','src/main/cpp/deps/tiny_dng_writer.h'}
def sha(p):
 h=hashlib.sha256();
 with p.open('rb') as f:
  for b in iter(lambda:f.read(1024*1024),b''): h.update(b)
 return h.hexdigest()
def collect(root):
 out={}
 for p in root.rglob('*'):
  if not p.is_file(): continue
  r=p.relative_to(root).as_posix()
  if r.startswith('build/') or r.startswith('.cxx/') or r.startswith('.gradle/'): continue
  if r in ALLOWED_NEW: continue
  out[r]=sha(p)
 return out
ap=argparse.ArgumentParser(); ap.add_argument('mode',choices=['snapshot','verify']); ap.add_argument('app'); ap.add_argument('manifest'); a=ap.parse_args(); root=Path(a.app); mf=Path(a.manifest)
if a.mode=='snapshot':
 d=collect(root); mf.write_text(json.dumps(d,sort_keys=True,indent=2)); print('snapshot files='+str(len(d))); sys.exit(0)
old=json.loads(mf.read_text()); now=collect(root)
missing=sorted(set(old)-set(now)); changed=sorted(k for k in old.keys()&now.keys() if old[k]!=now[k]); new=sorted(set(now)-set(old))
if missing or changed or new:
 print('missing',missing[:20]); print('changed',changed[:20]); print('new',new[:20]); raise SystemExit(1)
print('PASS: Gradle preserved every pre-existing app source/module file; only build outputs/known generated deps excluded')

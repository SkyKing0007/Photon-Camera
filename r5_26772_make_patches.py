#!/usr/bin/env python3
from pathlib import Path
import hashlib, os, shutil, subprocess, sys

if len(sys.argv) != 4:
    raise SystemExit('usage: r5_26772_make_patches.py BASE CANDIDATE OUTDIR')
base, cand, out = map(Path, sys.argv[1:])
out.mkdir(parents=True, exist_ok=True)
repo = out / 'patchrepo'
if repo.exists():
    shutil.rmtree(repo)
repo.mkdir()

def run(*args, cwd=repo, env=None, capture=False):
    e = os.environ.copy()
    if env:
        e.update(env)
    cp = subprocess.run(
        args,
        cwd=cwd,
        env=e,
        check=True,
        text=True,
        stdout=subprocess.PIPE if capture else None,
    )
    return cp.stdout if capture else None

def app_universe(root):
    app = Path(root) / 'app'
    return {
        str(p.relative_to(root)): hashlib.sha256(p.read_bytes()).hexdigest()
        for p in app.rglob('*') if p.is_file()
    }

def copy_app(src):
    dst = repo / 'app'
    if dst.exists():
        shutil.rmtree(dst)
    shutil.copytree(Path(src) / 'app', dst)

base_u = app_universe(base)
cand_u = app_universe(cand)
changed = sorted(k for k in set(base_u) | set(cand_u) if base_u.get(k) != cand_u.get(k))
if not changed:
    raise SystemExit('refusing empty runtime transition: base and candidate app universes are byte-identical')

run('git','init','-q')
run('git','config','user.name','Photon R5 Patch Proof')
run('git','config','user.email','proof@example.invalid')
run('git','config','core.autocrlf','false')
run('git','config','core.filemode','false')
fixed0={'GIT_AUTHOR_DATE':'2000-01-01T00:00:00Z','GIT_COMMITTER_DATE':'2000-01-01T00:00:00Z'}
fixed1={'GIT_AUTHOR_DATE':'2000-01-01T00:00:01Z','GIT_COMMITTER_DATE':'2000-01-01T00:00:01Z'}
copy_app(base)
run('git','add','-A')
run('git','commit','-q','-m','base26771',env=fixed0)
base_commit=run('git','rev-parse','HEAD',capture=True).strip()
copy_app(cand)
run('git','add','-A')
run('git','commit','-q','-m','candidate26772r5',env=fixed1)
cand_commit=run('git','rev-parse','HEAD',capture=True).strip()

pairs=[]
for abbrev in (7,12,40):
    run('git','config','core.abbrev',str(abbrev))
    f=run('git','diff','--binary','--full-index','--no-ext-diff',base_commit,cand_commit,'--','app',capture=True)
    r=run('git','diff','--binary','--full-index','--no-ext-diff',cand_commit,base_commit,'--','app',capture=True)
    if not f.strip() or not r.strip():
        raise SystemExit(f'empty patch generated for non-empty transition at core.abbrev={abbrev}')
    fp=out/f'r5_26772_FORWARD_FULL_INDEX_abbrev{abbrev}.patch'
    rp=out/f'r5_26772_ROLLBACK_FULL_INDEX_abbrev{abbrev}.patch'
    fp.write_text(f, encoding='utf-8', newline='\n')
    rp.write_text(r, encoding='utf-8', newline='\n')
    pairs.append((abbrev,fp,rp))

fh={hashlib.sha256(fp.read_bytes()).hexdigest() for _,fp,_ in pairs}
rh={hashlib.sha256(rp.read_bytes()).hexdigest() for _,_,rp in pairs}
if len(fh)!=1: raise SystemExit('forward patch varies with core.abbrev')
if len(rh)!=1: raise SystemExit('rollback patch varies with core.abbrev')

for abbrev,fp,rp in pairs:
    test=out/f'replay_abbrev{abbrev}'
    if test.exists(): shutil.rmtree(test)
    test.mkdir()
    shutil.copytree(base/'app', test/'app')
    subprocess.run(['git','apply','--check',str(fp)],cwd=test,check=True)
    subprocess.run(['git','apply',str(fp)],cwd=test,check=True)
    if app_universe(test) != cand_u:
        raise SystemExit(f'forward replay mismatch core.abbrev={abbrev}')
    subprocess.run(['git','apply','--check',str(rp)],cwd=test,check=True)
    subprocess.run(['git','apply',str(rp)],cwd=test,check=True)
    if app_universe(test) != base_u:
        raise SystemExit(f'rollback replay mismatch core.abbrev={abbrev}')
    shutil.rmtree(test)

# strict changed-file equality derived from byte universes, not patch parser heuristics
(out/'r5_26772_PATCH_CHANGED_PATHS.txt').write_text('\n'.join(changed)+'\n',encoding='utf-8')
(out/'r5_26772_FORWARD_FULL_INDEX.patch').write_bytes(pairs[-1][1].read_bytes())
(out/'r5_26772_ROLLBACK_FULL_INDEX.patch').write_bytes(pairs[-1][2].read_bytes())
shutil.rmtree(repo)
print(f'PASS deterministic binary full-index forward/rollback patch proof: {len(changed)} changed paths; core.abbrev 7/12/40; exact forward replay; exact rollback; non-empty transition')

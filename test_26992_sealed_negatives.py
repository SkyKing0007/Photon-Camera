#!/usr/bin/env python3
import hashlib,pathlib,shutil,subprocess,sys,tempfile,os
R=pathlib.Path(__file__).resolve().parent
entries={p:h for h,p in (x.split('  ',1) for x in (R/'26992_HANDOFF_HASHES.sha256').read_text().splitlines())}
# isolated replay does not need the remote repository's inherited inputs; verify those independently at Actions entry.
env=dict(os.environ);env.pop('GITHUB_ACTIONS',None)
with tempfile.TemporaryDirectory(prefix='26992-neg-') as d:
 t=pathlib.Path(d)
 for p in [*entries,'26992_HANDOFF_HASHES.sha256']:
  f=t/p;f.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(R/p,f)
 run=lambda:subprocess.run([sys.executable,'-S',str(t/'build_26992_incremental.py'),'seal'],capture_output=True,text=True,env=env)
 assert run().returncode==0
 cases=0
 for p in ['TRIGGER_26992.txt','.github/workflows/build-26992-change-aware.yml','26992_FORWARD_FULLINDEX.patch','26992_PROTECTED_SOURCE.sha256','compile_26992_shaders.sh','26992_REUSED_EXECUTABLES.json','build_26992_incremental.py','handoff_payload_26992/'+(R/'26992_CHANGED_RUNTIME_ALLOWLIST.txt').read_text().splitlines()[0]]:
  f=t/p;original=f.read_bytes();f.write_bytes(original+b'\n# tampered\n');assert run().returncode!=0,p;f.write_bytes(original);cases+=1
  f.unlink();assert run().returncode!=0,p;f.write_bytes(original);cases+=1
 extra=t/'handoff_payload_26992/app/unexpected.txt';extra.write_text('negative extra');assert run().returncode!=0;extra.unlink();cases+=1
 # Truncated/altered workflow with deliberately re-signed seal must still fail exact workflow derivation.
 p='.github/workflows/build-26992-change-aware.yml';f=t/p;original=f.read_bytes();f.write_bytes(original.replace(b'./gradlew --no-daemon --build-cache :app:assembleDebug',b'echo bypass',1));seal=t/'26992_HANDOFF_HASHES.sha256';originalseal=seal.read_text();seal.write_text(originalseal.replace(entries[p],hashlib.sha256(f.read_bytes()).hexdigest()));assert run().returncode!=0;f.write_bytes(original);seal.write_text(originalseal);cases+=1
 assert run().returncode==0
 print(f'PASS {cases} real missing/tamper/resealed-workflow/extra cases and restored clean seal')

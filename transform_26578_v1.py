#!/usr/bin/env python3
from pathlib import Path
import hashlib, shutil, sys

CHANGED=[
'app/src/main/java/com/hinnka/mycamera/processor/GlesIris26529SpatialRgbChromaPostprocessor.kt',
'app/version.properties',
]
BASE_HASH={
CHANGED[0]:'d6055090d1dc6f826905fb9ec83d925b11c04644f4ebb1148f6dcebd81768d30',
CHANGED[1]:'78f700cd6c7afcf79df14176f3e566f99f249e6db904623da6e20a403716393d',
}
EXPECTED_HASH={
CHANGED[0]:'6ed6aabeb9465c5ad575cd9058a383e2a4de1002c502efcc842789adc9fc055f',
CHANGED[1]:'7770498e33fee6edb3e94e81d7a274e6bcfcc75d5379f2cb81aa1427477d2378',
}
def sha(p): return hashlib.sha256(p.read_bytes()).hexdigest()
def fail(m): raise SystemExit('FAIL: '+m)
if len(sys.argv)!=3: fail('usage: transform base candidate')
base=Path(sys.argv[1]); out=Path(sys.argv[2]); pkg=Path(__file__).resolve().parent
for rel,h in BASE_HASH.items():
 p=base/rel
 if not p.is_file() or sha(p)!=h: fail('exact successful-26577 prewrite hash '+rel)
if out.exists(): shutil.rmtree(out)
shutil.copytree(base,out)
for rel in CHANGED:
 src=pkg/'handoff_payload_26578_v1'/rel
 if not src.is_file(): fail('sealed payload missing '+rel)
 dst=out/rel; dst.parent.mkdir(parents=True,exist_ok=True); shutil.copy2(src,dst)
 if sha(dst)!=EXPECTED_HASH[rel]: fail('sealed transformed hash '+rel)
print('PASS deterministic 26578 candidate overlay from exact successful-26577 authority')
print('PASS changed runtime allowlist = 2')
